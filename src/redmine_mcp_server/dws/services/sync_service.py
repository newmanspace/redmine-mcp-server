# /docker/redmine-mcp-server/src/redmine_mcp_server/backfill_sync.py
"""
Backfill historical daily snapshots
Reconstruct daily snapshots from Issue creation date and journals
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests

from ..repository import DataWarehouse
from ...redmine_handler import REDMINE_URL, REDMINE_API_KEY, logger


class BackfillSync:
    """Backfill historical daily snapshots"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.warehouse: Optional[DataWarehouse] = None
        self._init_warehouse()

    def _init_warehouse(self):
        """Initialize warehouse connection"""
        try:
            self.warehouse = DataWarehouse()
            logger.info("BackfillSync: Warehouse connection initialized")
        except Exception as e:
            logger.error(f"BackfillSync: Failed to initialize warehouse: {e}")
            raise

    def get_project_issues(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all issues for a project with full journals

        Args:
            project_id: Project ID

        Returns:
            List of issues with journals
        """
        api_url = f"{REDMINE_URL}/issues.json"
        headers = {"X-Redmine-API-Key": REDMINE_API_KEY}

        all_issues = []
        offset = 0

        logger.info(f"Fetching all issues for project {project_id}...")

        while True:
            try:
                params = {
                    "project_id": project_id,
                    "status_id": "*",
                    "limit": self.batch_size,
                    "offset": offset,
                    "include": "journals",  # Include journals for history
                }

                resp = requests.get(api_url, headers=headers, params=params, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                logger.info(f"Fetched {len(all_issues)} issues...")

                if len(issues) < self.batch_size:
                    break

                offset += self.batch_size

            except Exception as e:
                logger.error(f"Failed to fetch issues: {e}")
                break

        logger.info(f"Total issues fetched: {len(all_issues)}")
        return all_issues

    def build_issue_timeline(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build timeline of issue state changes

        Args:
            issue: Issue data with journals

        Returns:
            List of daily snapshots
        """
        timeline = []

        issue_id = issue.get("id")
        created_on = issue.get("created_on", "")

        if not created_on:
            return timeline

        # Parse creation date
        try:
            created_date = datetime.fromisoformat(
                created_on.replace("Z", "+00:00")
            ).date()
        except:
            return timeline

        # Initial state (creation date)
        current_state = {
            "issue_id": issue_id,
            "project_id": issue.get("project", {}).get("id"),
            "subject": issue.get("subject", ""),
            "status_id": issue.get("status", {}).get("id"),
            "status_name": issue.get("status", {}).get("name"),
            "priority_id": issue.get("priority", {}).get("id"),
            "priority_name": issue.get("priority", {}).get("name"),
            "assigned_to_id": (
                issue.get("assigned_to", {}).get("id")
                if issue.get("assigned_to")
                else None
            ),
            "assigned_to_name": (
                issue.get("assigned_to", {}).get("name")
                if issue.get("assigned_to")
                else None
            ),
            "created_at": created_on,
            "updated_at": issue.get("updated_on", ""),
            "is_new": True,
            "is_closed": False,
            "is_updated": False,
        }

        timeline.append({"date": created_date, "state": current_state.copy()})

        # Process journals (change history)
        journals = issue.get("journals", [])
        for journal in journals:
            try:
                journal_date = datetime.fromisoformat(
                    journal.get("created_on", "").replace("Z", "+00:00")
                ).date()
            except:
                continue

            # Check for status/priority/assignee changes
            details = journal.get("details", [])
            state_changed = False

            for detail in details:
                prop = detail.get("prop_key")
                new_value = detail.get("new_value")
                old_value = detail.get("old_value")

                if prop == "status_id":
                    # Get status name from journal
                    status_name = detail.get("new_value", "")
                    current_state["status_id"] = new_value
                    current_state["status_name"] = status_name

                    # Check if closed
                    if status_name in ["已shutdown", "Closed"]:
                        current_state["is_closed"] = True

                    state_changed = True

                elif prop == "priority_id":
                    current_state["priority_id"] = new_value
                    current_state["priority_name"] = detail.get("new_value", "")
                    state_changed = True

                elif prop == "assigned_to_id":
                    current_state["assigned_to_id"] = new_value
                    current_state["assigned_to_name"] = detail.get("new_value", "")
                    state_changed = True

            if state_changed:
                current_state["updated_at"] = journal.get("created_on", "")
                current_state["is_new"] = False
                current_state["is_updated"] = True

                timeline.append({"date": journal_date, "state": current_state.copy()})

        return timeline

    def backfill_project(self, project_id: int, start_date: Optional[datetime] = None):
        """
        Backfill daily snapshots for a project

        Args:
            project_id: Project ID
            start_date: Optional start date (default: project creation)
        """
        logger.info(f"Starting backfill for project {project_id}...")

        # Get all issues with journals
        issues = self.get_project_issues(project_id)

        if not issues:
            logger.warning(f"No issues found for project {project_id}")
            return

        # Build timelines for all issues
        all_snapshots = {}  # date -> list of snapshots

        for issue in issues:
            timeline = self.build_issue_timeline(issue)

            for entry in timeline:
                date = entry["date"]
                state = entry["state"]

                if start_date and date < start_date.date():
                    continue

                if date not in all_snapshots:
                    all_snapshots[date] = []

                all_snapshots[date].append(state)

        logger.info(f"Built snapshots for {len(all_snapshots)} days")

        # Save snapshots to warehouse
        total_saved = 0
        for date in sorted(all_snapshots.keys()):
            snapshots = all_snapshots[date]

            try:
                # Save issue snapshots
                with self.warehouse.get_connection() as conn:
                    with conn.cursor() as cur:
                        for state in snapshots:
                            cur.execute(
                                """
                                INSERT INTO warehouse.dwd_issue_daily_snapshot (
                                    issue_id, project_id, snapshot_date,
                                    subject, status_id, status_name,
                                    priority_id, priority_name,
                                    assigned_to_id, assigned_to_name,
                                    created_at, updated_at,
                                    is_new, is_closed, is_updated
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                                ON CONFLICT (issue_id, snapshot_date) DO UPDATE SET
                                    status_id = EXCLUDED.status_id,
                                    status_name = EXCLUDED.status_name,
                                    priority_id = EXCLUDED.priority_id,
                                    priority_name = EXCLUDED.priority_name,
                                    assigned_to_id = EXCLUDED.assigned_to_id,
                                    assigned_to_name = EXCLUDED.assigned_to_name,
                                    updated_at = EXCLUDED.updated_at,
                                    is_closed = EXCLUDED.is_closed
                            """,
                                (
                                    state["issue_id"],
                                    state["project_id"],
                                    date,
                                    state["subject"],
                                    state["status_id"],
                                    state["status_name"],
                                    state["priority_id"],
                                    state["priority_name"],
                                    state["assigned_to_id"],
                                    state["assigned_to_name"],
                                    state["created_at"],
                                    state["updated_at"],
                                    state["is_new"],
                                    state["is_closed"],
                                    state["is_updated"],
                                ),
                            )

                # Refresh daily summary
                self.warehouse.refresh_daily_summary(project_id, date)

                total_saved += len(snapshots)
                logger.info(f"Saved {len(snapshots)} snapshots for {date}")

            except Exception as e:
                logger.error(f"Failed to save snapshots for {date}: {e}")

        logger.info(
            f"Backfill completed for project {project_id}: {total_saved} snapshots saved"
        )

    def close(self):
        """Close warehouse connection"""
        if self.warehouse:
            self.warehouse.close()


def backfill_all_projects(project_ids: List[int], batch_size: int = 100):
    """
    Backfill all projects

    Args:
        project_ids: List of project IDs
        batch_size: API batch size
    """
    sync = BackfillSync(batch_size)

    try:
        for project_id in project_ids:
            sync.backfill_project(project_id)
    finally:
        sync.close()


if __name__ == "__main__":
    # Example usage
    project_ids = [311, 315, 316, 337, 341, 356, 357, 358, 359, 367, 372, 373, 374, 375]
    backfill_all_projects(project_ids)
