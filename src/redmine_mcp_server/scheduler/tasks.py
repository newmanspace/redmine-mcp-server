# /docker/redmine-mcp-server/src/redmine_mcp_server/redmine_scheduler.py
"""
Redmine incremental sync scheduler with progressive weekly sync
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests


from ..dws.repository import DataWarehouse
from ..redmine_handler import REDMINE_URL, REDMINE_API_KEY, logger


class RedmineSyncScheduler:
    """Redmine incremental sync scheduler with progressive weekly sync"""

    def __init__(
        self, project_ids: Optional[List[int]] = None, sync_interval_minutes: int = 10
    ):
        """
        Initialize scheduler


        Args:
            project_ids: Projects to sync (if None, auto-detect from subscriptions)
            sync_interval_minutes: Sync interval in minutes
        """
        self.project_ids = project_ids  # Will be loaded from subscriptions if None
        self.sync_interval_minutes = sync_interval_minutes
        self.warehouse: Optional[DataWarehouse] = None
        self.scheduler = BlockingScheduler()
        self._sync_count = 0

        # Batch size for API requests (prevent Redmine overload)
        self.batch_size = int(os.getenv("SYNC_BATCH_SIZE", "100"))

        # Progressive sync: track last synced end date for each project
        self.project_sync_progress: Dict[int, datetime] = {}

        logger.info("RedmineSyncScheduler initialized (subscription-based)")
        logger.info(f"Sync interval: {self.sync_interval_minutes} minutes")
        logger.info(f"API batch size: {self.batch_size} issues per request")
        logger.info("Progressive weekly sync: enabled")

    def _init_warehouse(self):
        """Delay initialization of warehouse connection"""
        if self.warehouse is None:
            self.warehouse = DataWarehouse()
            logger.info("Warehouse connection initialized")

    def _load_subscribed_projects(self) -> List[int]:
        """Load subscribed project IDs from subscription manager"""
        try:
            from ..dws.services.subscription_service import get_subscription_manager

            manager = get_subscription_manager()
            all_subs = manager.list_all_subscriptions()
            project_ids = list(
                set(
                    sub.get("project_id")
                    for sub in all_subs
                    if sub.get("enabled", True)
                )
            )
            logger.info(f"Loaded {
                    len(project_ids)} subscribed projects: {project_ids}")
            return project_ids
        except Exception as e:
            logger.error(f"Failed to load subscribed projects: {e}")
            return []

    def _get_project_created_date(self, project_id: int) -> Optional[datetime]:
        """Get project creation date from Redmine API (returns naive datetime)"""
        try:
            api_url = f"{REDMINE_URL}/projects/{project_id}.json"
            headers = {"X-Redmine-API-Key": REDMINE_API_KEY}
            resp = requests.get(api_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            created_on = data.get("project", {}).get("created_on", "")
            if created_on:
                # Parse ISO format and convert to naive datetime
                dt = datetime.fromisoformat(created_on.replace("Z", "+00:00"))
                return dt.replace(tzinfo=None)
            return None
        except Exception as e:
            logger.warning(f"Failed to get project {project_id} creation date: {e}")
            return None

    def _get_progressive_sync_start(self, project_id: int) -> datetime:
        """Get start date for progressive sync (project creation or last synced date)"""
        # Check if we have progress tracked
        if project_id in self.project_sync_progress:
            return self.project_sync_progress[project_id]

        # First time: get project creation date
        created_date = self._get_project_created_date(project_id)
        if created_date:
            return created_date

        # Fallback: 6 months ago
        return datetime.now() - timedelta(days=180)

    def _sync_project(
        self, project_id: int, incremental: bool = True, progressive: bool = False
    ) -> int:
        """
        Sync a single project


        Args:
            project_id: Project ID
            incremental: True for incremental sync (recent updates)
            progressive: True for progressive weekly sync from project creation


        Returns:
            Number of issues synced
        """
        if not self.warehouse:
            self._init_warehouse()

        api_url = f"{REDMINE_URL}/issues.json"
        headers = {"X-Redmine-API-Key": REDMINE_API_KEY}

        all_issues: List[Dict[str, Any]] = []
        filtered_issues: List[Dict[str, Any]] = []
        offset = 0
        limit = 100

        # Build query parameters
        # Use status_id=* to get ALL issues (including closed ones)
        params = {
            "project_id": project_id,
            "status_id": "*",
            "limit": limit,
            "offset": offset,
        }

        # Determine date range for sync
        sync_start = None
        sync_end = None

        if progressive:
            # Progressive weekly sync: sync one week at a time from project
            # creation
            sync_start = self._get_progressive_sync_start(project_id)
            sync_end = sync_start + timedelta(days=7)
            if sync_end > datetime.now():
                sync_end = datetime.now()

            # Query from sync_start onwards, then filter client-side
            params["created_on"] = f'>={sync_start.strftime("%Y-%m-%d")}'
            logger.info(f"Progressive sync for project {project_id}: from {
                    sync_start.strftime('%Y-%m-%d')}")

        elif incremental:
            # Incremental sync: get issues updated in last 13 minutes (with buffer to prevent missing data)
            # Use 13 minutes to ensure we don't miss any data due to timing
            # issues or sync delays
            since = datetime.now() - timedelta(minutes=13)
            params["updated_on"] = f'>={since.strftime("%Y-%m-%d %H:%M:%S")}'
            logger.info(
                f"Incremental sync for project {project_id} since {since} (13-min window)"
            )

        else:
            # Full sync: start from project creation date (not limited to 6 months)
            # Use progressive sync to gradually sync all historical data
            project_created = self._get_project_created_date(project_id)
            if project_created:
                params["created_on"] = f'>={
                    project_created.strftime("%Y-%m-%d")}'
                logger.info(
                    f"Full sync for project {project_id}, from project creation ({
                        project_created.strftime('%Y-%m-%d')})"
                )
            else:
                # Fallback: sync all issues (no date filter)
                logger.info(
                    f"Full sync for project {project_id}, syncing all issues (no creation date found)"
                )

        # Paginate - fetch all issues (no total limit)
        while True:
            try:
                resp = requests.get(api_url, headers=headers, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < self.batch_size:
                    break

                offset += self.batch_size
                logger.debug(f"Fetched {len(all_issues)} issues...")

            except Exception as e:
                logger.error(f"Failed to fetch issues for project {project_id}: {e}")
                break

        # Filter issues by date range for progressive sync
        if progressive and sync_start and sync_end:
            for issue in all_issues:
                created_on = issue.get("created_on", "")
                if created_on:
                    issue_date = datetime.fromisoformat(
                        created_on.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    if sync_start <= issue_date < sync_end:
                        filtered_issues.append(issue)
                    elif issue_date >= sync_end:
                        break  # Issues are sorted by date, can stop early

            logger.info(f"Filtered {
                    len(all_issues)} issues to {
                    len(filtered_issues)} in date range [{
                    sync_start.strftime('%Y-%m-%d')}, {
                    sync_end.strftime('%Y-%m-%d')})")
            issues_to_sync = filtered_issues
        else:
            issues_to_sync = all_issues

        if not issues_to_sync:
            logger.info(f"No issues to sync for project {project_id}")
            return 0

        # Get yesterday's snapshot for comparison
        yesterday = datetime.now().date() - timedelta(days=1)
        try:
            previous_issues = self.warehouse.get_issues_snapshot(project_id, yesterday)
            previous_map = {i["issue_id"]: i for i in previous_issues}
        except Exception as e:
            logger.warning(f"Failed to get previous snapshot: {e}")
            previous_map = {}

        # Batch sync to warehouse
        try:
            self.warehouse.upsert_issues_batch(
                project_id, issues_to_sync, datetime.now().date(), previous_map
            )
            logger.info(f"Synced {
                    len(issues_to_sync)} issues for project {project_id}")

            # Update progress for progressive sync
            if progressive and sync_end:
                self.project_sync_progress[project_id] = sync_end
                logger.debug(
                    f"Project {project_id} sync progress updated to {sync_end}"
                )

            return len(issues_to_sync)
        except Exception as e:
            logger.error(f"Failed to upsert issues for project {project_id}: {e}")
            return 0

    def _sync_all_projects(self, full: bool = True, progressive: bool = False):
        """
        Sync all projects


        Args:
            full: True for full sync, False for incremental
            progressive: True for progressive weekly sync (overrides full)
        """
        if progressive:
            sync_type = "progressive (weekly)"
        elif full:
            sync_type = "full"
        else:
            sync_type = "incremental"

        logger.info(
            f"Starting {sync_type} sync for {len(self.project_ids)} projects..."
        )

        sync_results = {}
        for project_id in self.project_ids:
            try:
                count = self._sync_project(
                    project_id, incremental=not full, progressive=progressive
                )
                sync_results[project_id] = {"status": "success", "count": count}
            except Exception as e:
                logger.error(f"Failed to sync project {project_id}: {e}")
                sync_results[project_id] = {"status": "error", "error": str(e)}

        self._sync_count += 1
        logger.info("Sync completed")
        logger.info("Sync results: %s", sync_results)

    def _sync_all_projects_progressive(self):
        """
        Progressive sync: sync one week of data for each project per run
        Call this every 10 minutes to gradually build up historical data
        """
        logger.info(
            f"Starting progressive weekly sync for {len(self.project_ids)} projects..."
        )

        sync_results = {}
        for project_id in self.project_ids:
            try:
                count = self._sync_project(
                    project_id, incremental=False, progressive=True
                )
                sync_results[project_id] = {"status": "success", "count": count}
            except Exception as e:
                logger.error(f"Failed to sync project {project_id}: {e}")
                sync_results[project_id] = {"status": "error", "error": str(e)}

        self._sync_count += 1
        logger.info("Progressive sync completed")
        logger.info("Sync results: %s", sync_results)

    def start(self):
        """Start scheduler with incremental sync only (progressive sync is manual)"""
        import threading

        try:
            self._init_warehouse()

            # Load project IDs from subscriptions if not provided
            if self.project_ids is None:
                self.project_ids = self._load_subscribed_projects()

            if not self.project_ids:
                logger.warning("No projects to sync (no active subscriptions)")
                return

            # Add scheduled job for incremental sync (every 10 minutes)
            self.scheduler.add_job(
                self._sync_all_projects,
                IntervalTrigger(minutes=self.sync_interval_minutes),
                id="incremental_sync",
                name=f"Incremental Redmine Sync (every {
                    self.sync_interval_minutes} min)",
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=60,
            )

            # Start scheduler in background thread
            def run_scheduler():
                # Only run incremental sync automatically
                logger.info("Incremental sync scheduler started (every 10 minutes)")
                logger.info(
                    "Note: Full/progressive sync must be triggered manually via MCP tools"
                )
                self.scheduler.start()

            thread = threading.Thread(target=run_scheduler, daemon=True)
            thread.start()

            logger.info(f"Scheduler started in background thread")
            logger.info(f"Syncing {len(self.project_ids)} projects: {self.project_ids}")
            logger.info(f"Incremental sync interval: {
                    self.sync_interval_minutes} minutes (last 13 minutes of data)")
            logger.info(f"Progressive/Full sync: Manual trigger only (use MCP tools)")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise


# ========== Global Scheduler Instance ==========


_scheduler: Optional[RedmineSyncScheduler] = None


def init_scheduler(
    project_ids: Optional[List[int]] = None, sync_interval_minutes: int = 10
) -> RedmineSyncScheduler:
    """Initialize global scheduler instance"""
    global _scheduler
    _scheduler = RedmineSyncScheduler(project_ids, sync_interval_minutes)
    _scheduler.start()
    return _scheduler


def get_scheduler() -> Optional[RedmineSyncScheduler]:
    """Get global scheduler instance"""
    return _scheduler


def shutdown_scheduler():
    """Shutdown scheduler gracefully"""
    global _scheduler
    if _scheduler and _scheduler.scheduler:
        _scheduler.scheduler.shutdown()
        logger.info("Scheduler shutdown complete")
    _scheduler = None


# ========== ODS Sync Integration ==========


def sync_ods_layer_incremental(
    project_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Sync ODS layer incrementally (last 15 minutes)


    Args:
        project_ids: Projects to sync (all subscribed if None)


    Returns:
        Sync results
    """
    try:
        from ..dws.services.ods_sync_service import sync_ods_incremental

        logger.info("Starting ODS incremental sync...")
        return sync_ods_incremental(project_ids)
    except Exception as e:
        logger.error(f"ODS incremental sync failed: {e}")
        return {"error": str(e)}


def sync_ods_layer_full(
    project_ids: Optional[List[int]] = None, from_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Sync ODS layer fully (force refresh)


    Args:
        project_ids: Projects to sync (all subscribed if None)
        from_date: Optional start date


    Returns:
        Sync results
    """
    try:
        from ..dws.services.ods_sync_service import sync_ods_full

        logger.info(f"Starting ODS full sync...")
        return sync_ods_full(project_ids, from_date)
    except Exception as e:
        logger.error(f"ODS full sync failed: {e}")
        return {"error": str(e)}
