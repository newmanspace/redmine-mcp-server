#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ODS Layer Sync Service

Sync data from Redmine API to ODS (Operational Data Store) tables.
Supports both incremental and full sync modes.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests

from .redmine_handler import REDMINE_URL, REDMINE_API_KEY, logger
from ..repository import DataWarehouse


class ODSSyncService:
    """ODS Layer Synchronization Service"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.warehouse: Optional[DataWarehouse] = None
        self._init_warehouse()

        # API configuration
        self.api_url = f"{REDMINE_URL}/issues.json"
        self.headers = {"X-Redmine-API-Key": REDMINE_API_KEY}

        logger.info(f"ODSSyncService initialized (batch_size={batch_size})")

    def _init_warehouse(self):
        """Initialize warehouse connection"""
        try:
            self.warehouse = DataWarehouse()
            logger.info("ODSSyncService: Warehouse connection initialized")
        except Exception as e:
            logger.error(f"ODSSyncService: Failed to initialize warehouse: {e}")
            raise

    def sync_ods_projects(self, project_ids: Optional[List[int]] = None) -> int:
        """
        Sync projects to ODS layer

        Args:
            project_ids: Specific project IDs to sync (all if None)

        Returns:
            Number of projects synced
        """
        if not project_ids:
            # Get all accessible projects
            try:
                projects_url = f"{REDMINE_URL}/projects.json"
                all_projects = []
                offset = 0

                while True:
                    resp = requests.get(
                        projects_url,
                        headers=self.headers,
                        params={"limit": self.batch_size, "offset": offset},
                        timeout=30,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    projects = data.get("projects", [])
                    all_projects.extend(projects)

                    if len(projects) < self.batch_size:
                        break
                    offset += self.batch_size

                project_ids = [p["id"] for p in all_projects]
                logger.info(f"Found {len(project_ids)} projects to sync")
            except Exception as e:
                logger.error(f"Failed to fetch project list: {e}")
                return 0

        count = 0
        for project_id in project_ids:
            try:
                self._sync_single_project_to_ods(project_id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync project {project_id}: {e}")

        logger.info(f"Synced {count} projects to ODS")
        return count

    def _sync_single_project_to_ods(self, project_id: int):
        """Sync single project metadata to ODS"""
        try:
            projects_url = f"{REDMINE_URL}/projects/{project_id}.json"
            resp = requests.get(projects_url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            project = data.get("project", {})

            with self.warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO warehouse.ods_projects (
                            project_id, name, identifier, description,
                            status, created_on, updated_on
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (project_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            identifier = EXCLUDED.identifier,
                            description = EXCLUDED.description,
                            status = EXCLUDED.status,
                            updated_on = EXCLUDED.updated_on
                    """,
                        (
                            project.get("id"),
                            project.get("name"),
                            project.get("identifier"),
                            project.get("description"),
                            project.get("status"),
                            project.get("created_on"),
                            project.get("updated_on"),
                        ),
                    )
        except Exception as e:
            logger.error(f"Failed to sync project {project_id} metadata: {e}")
            raise

    def sync_ods_issues_incremental(
        self, project_id: int, since_minutes: int = 15
    ) -> Tuple[int, int]:
        """
        Incremental sync of issues to ODS layer

        Args:
            project_id: Project ID to sync
            since_minutes: Fetch issues updated in last N minutes

        Returns:
            Tuple of (fetched_count, synced_count)
        """
        since = datetime.now() - timedelta(minutes=since_minutes)
        date_filter = f">={since.strftime('%Y-%m-%d %H:%M:%S')}"

        logger.info(f"Incremental sync for project {project_id} since {since}")

        return self._fetch_and_sync_issues(project_id, {"updated_on": date_filter})

    def sync_ods_issues_full(
        self, project_id: int, from_date: Optional[datetime] = None
    ) -> Tuple[int, int]:
        """
        Full sync of issues to ODS layer

        Args:
            project_id: Project ID to sync
            from_date: Optional start date (sync from project creation if None)

        Returns:
            Tuple of (fetched_count, synced_count)
        """
        if from_date:
            date_filter = f">={from_date.strftime('%Y-%m-%d')}"
            logger.info(f"Full sync for project {project_id} from {from_date}")
        else:
            # Get project creation date
            try:
                projects_url = f"{REDMINE_URL}/projects/{project_id}.json"
                resp = requests.get(projects_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                created_on = data.get("project", {}).get("created_on", "")
                if created_on:
                    from_date = datetime.fromisoformat(
                        created_on.replace("Z", "+00:00")
                    )
                    date_filter = f">={from_date.strftime('%Y-%m-%d')}"
                    logger.info(f"Full sync from project creation: {from_date}")
                else:
                    date_filter = None
                    logger.info(f"Full sync for project {project_id} (no date filter)")
            except Exception as e:
                logger.warning(f"Failed to get project creation date: {e}")
                date_filter = None

        params = {}
        if date_filter:
            params["created_on"] = date_filter

        return self._fetch_and_sync_issues(project_id, params)

    def _fetch_and_sync_issues(
        self, project_id: int, params: Dict[str, Any]
    ) -> Tuple[int, int]:
        """
        Fetch issues from API and sync to ODS

        Args:
            project_id: Project ID
            params: Additional query parameters

        Returns:
            Tuple of (fetched_count, synced_count)
        """
        all_issues = []
        offset = 0

        # Add base parameters
        base_params = {
            "project_id": project_id,
            "status_id": "*",
            "limit": self.batch_size,
            "offset": offset,
            **params,
        }

        # Paginate through all issues
        while True:
            try:
                base_params["offset"] = offset
                resp = requests.get(
                    self.api_url, headers=self.headers, params=base_params, timeout=60
                )
                resp.raise_for_status()
                data = resp.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                logger.debug(
                    f"Fetched {len(all_issues)} issues for project {project_id}"
                )

                if len(issues) < self.batch_size:
                    break

                offset += self.batch_size

            except Exception as e:
                logger.error(f"Failed to fetch issues: {e}")
                break

        if not all_issues:
            logger.info(f"No issues to sync for project {project_id}")
            return (0, 0)

        # Sync to ODS
        synced_count = self._sync_issues_to_ods(project_id, all_issues)

        logger.info(
            f"Synced {synced_count}/{len(all_issues)} issues to ODS for project {project_id}"
        )
        return (len(all_issues), synced_count)

    def _sync_issues_to_ods(self, project_id: int, issues: List[Dict]) -> int:
        """
        Sync issues to ODS layer

        Args:
            project_id: Project ID
            issues: List of issue data from API

        Returns:
            Number of issues synced
        """
        count = 0
        with self.warehouse.get_connection() as conn:
            with conn.cursor() as cur:
                for issue in issues:
                    try:
                        # Sync issue
                        cur.execute(
                            """
                            INSERT INTO warehouse.ods_issues (
                                issue_id, project_id, subject, description,
                                status_id, priority_id, tracker_id,
                                author_id, assigned_to_id,
                                created_on, updated_on, done_ratio,
                                due_date, estimated_hours, spent_hours
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (issue_id) DO UPDATE SET
                                subject = EXCLUDED.subject,
                                description = EXCLUDED.description,
                                status_id = EXCLUDED.status_id,
                                priority_id = EXCLUDED.priority_id,
                                assigned_to_id = EXCLUDED.assigned_to_id,
                                updated_on = EXCLUDED.updated_on,
                                done_ratio = EXCLUDED.done_ratio
                        """,
                            (
                                issue.get("id"),
                                issue.get("project", {}).get("id"),
                                issue.get("subject"),
                                issue.get("description"),
                                issue.get("status", {}).get("id"),
                                issue.get("priority", {}).get("id"),
                                issue.get("tracker", {}).get("id"),
                                issue.get("author", {}).get("id"),
                                (
                                    issue.get("assigned_to", {}).get("id")
                                    if issue.get("assigned_to")
                                    else None
                                ),
                                issue.get("created_on"),
                                issue.get("updated_on"),
                                issue.get("done_ratio"),
                                issue.get("due_date"),
                                issue.get("estimated_hours"),
                                issue.get("spent_hours"),
                            ),
                        )

                        # Sync journals if included
                        if "journals" in issue:
                            self._sync_journals_to_ods(
                                cur, issue.get("id"), issue.get("journals", [])
                            )

                        count += 1
                    except Exception as e:
                        logger.error(f"Failed to sync issue {issue.get('id')}: {e}")
                        continue

        return count

    def _sync_journals_to_ods(self, cur, issue_id: int, journals: List[Dict]):
        """Sync journals to ODS layer"""
        for journal in journals:
            try:
                cur.execute(
                    """
                    INSERT INTO warehouse.ods_journals (
                        journal_id, issue_id, user_id, notes,
                        created_on, private_notes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (journal_id) DO UPDATE SET
                        notes = EXCLUDED.notes,
                        private_notes = EXCLUDED.private_notes
                """,
                    (
                        journal.get("id"),
                        issue_id,
                        journal.get("user_id"),
                        journal.get("notes"),
                        journal.get("created_on"),
                        journal.get("private_notes"),
                    ),
                )

                # Sync journal details
                for detail in journal.get("details", []):
                    cur.execute(
                        """
                        INSERT INTO warehouse.ods_journal_details (
                            journal_id, name, old_value, new_value, prop_key
                        ) VALUES (%s, %s, %s, %s, %s)
                    """,
                        (
                            journal.get("id"),
                            detail.get("name"),
                            detail.get("old_value"),
                            detail.get("new_value"),
                            detail.get("prop_key"),
                        ),
                    )
            except Exception as e:
                logger.error(f"Failed to sync journal: {e}")
                continue

    def sync_ods_users(self, user_ids: Optional[List[int]] = None) -> int:
        """
        Sync users to ODS layer

        Args:
            user_ids: Specific user IDs to sync (all active if None)

        Returns:
            Number of users synced
        """
        try:
            users_url = f"{REDMINE_URL}/users.json"
            params = {"limit": self.batch_size}
            if user_ids:
                params["ids"] = ",".join(map(str, user_ids))

            all_users = []
            offset = 0

            while True:
                params["offset"] = offset
                resp = requests.get(
                    users_url, headers=self.headers, params=params, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                users = data.get("users", [])
                all_users.extend(users)

                if len(users) < self.batch_size:
                    break
                offset += self.batch_size

            # Sync to ODS
            count = 0
            with self.warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    for user in all_users:
                        try:
                            cur.execute(
                                """
                                INSERT INTO warehouse.ods_users (
                                    user_id, login, firstname, lastname,
                                    mail, status, created_on, last_login_on
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (user_id) DO UPDATE SET
                                    login = EXCLUDED.login,
                                    firstname = EXCLUDED.firstname,
                                    lastname = EXCLUDED.lastname,
                                    mail = EXCLUDED.mail,
                                    status = EXCLUDED.status,
                                    last_login_on = EXCLUDED.last_login_on
                            """,
                                (
                                    user.get("id"),
                                    user.get("login"),
                                    user.get("firstname"),
                                    user.get("lastname"),
                                    user.get("mail"),
                                    user.get("status"),
                                    user.get("created_on"),
                                    user.get("last_login_on"),
                                ),
                            )
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to sync user {user.get('id')}: {e}")

            logger.info(f"Synced {count} users to ODS")
            return count

        except Exception as e:
            logger.error(f"Failed to sync users: {e}")
            return 0

    def close(self):
        """Close warehouse connection"""
        if self.warehouse:
            self.warehouse.close()
            logger.info("ODSSyncService: Warehouse connection closed")


# Convenience functions for external use


def sync_ods_incremental(project_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Run incremental ODS sync for projects

    Sync order:
    1. Projects (base metadata)
    2. Users (user information)
    3. Issues (with journals included)

    Args:
        project_ids: Projects to sync (all subscribed if None)

    Returns:
        Sync results
    """
    from .subscription_service import SubscriptionManager

    sync_service = ODSSyncService()
    results = {
        "projects": {},
        "total_projects_synced": 0,
        "total_users_synced": 0,
        "total_issues_fetched": 0,
        "total_issues_synced": 0,
    }

    try:
        # Load subscribed projects if not specified
        if not project_ids:
            manager = SubscriptionManager()
            project_ids = list(
                set(
                    sub.get("project_id")
                    for sub in manager.list_all_subscriptions()
                    if sub.get("enabled", True)
                )
            )
            logger.info(f"Syncing {len(project_ids)} subscribed projects")

        # Step 1: Sync projects metadata first
        logger.info("Step 1: Syncing project metadata...")
        results["total_projects_synced"] = sync_service.sync_ods_projects(project_ids)

        # Step 2: Sync users
        logger.info("Step 2: Syncing user information...")
        results["total_users_synced"] = sync_service.sync_ods_users()

        # Step 3: Sync issues (with journals)
        logger.info("Step 3: Syncing issues and journals...")
        for project_id in project_ids:
            try:
                fetched, synced = sync_service.sync_ods_issues_incremental(project_id)
                results["projects"][project_id] = {
                    "fetched": fetched,
                    "synced": synced,
                }
                results["total_issues_fetched"] += fetched
                results["total_issues_synced"] += synced
            except Exception as e:
                results["projects"][project_id] = {"error": str(e)}

        logger.info(f"Incremental ODS sync completed: {results}")
        return results

    finally:
        sync_service.close()


def sync_ods_full(
    project_ids: Optional[List[int]] = None, from_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Run full ODS sync for projects (force refresh)

    Sync order:
    1. Projects (base metadata)
    2. Users (user information)
    3. Issues (with journals included)

    Args:
        project_ids: Projects to sync (all subscribed if None)
        from_date: Optional start date

    Returns:
        Sync results
    """
    from .subscription_service import SubscriptionManager

    sync_service = ODSSyncService()
    results = {
        "projects": {},
        "total_projects_synced": 0,
        "total_users_synced": 0,
        "total_issues_fetched": 0,
        "total_issues_synced": 0,
    }

    try:
        # Load subscribed projects if not specified
        if not project_ids:
            manager = SubscriptionManager()
            project_ids = list(
                set(
                    sub.get("project_id")
                    for sub in manager.list_all_subscriptions()
                    if sub.get("enabled", True)
                )
            )
            logger.info(f"Full sync for {len(project_ids)} subscribed projects")

        # Step 1: Sync projects metadata first
        logger.info("Step 1: Syncing project metadata...")
        results["total_projects_synced"] = sync_service.sync_ods_projects(project_ids)

        # Step 2: Sync users
        logger.info("Step 2: Syncing user information...")
        results["total_users_synced"] = sync_service.sync_ods_users()

        # Step 3: Sync issues (with journals)
        logger.info("Step 3: Syncing issues and journals...")
        for project_id in project_ids:
            try:
                fetched, synced = sync_service.sync_ods_issues_full(
                    project_id, from_date
                )
                results["projects"][project_id] = {
                    "fetched": fetched,
                    "synced": synced,
                }
                results["total_issues_fetched"] += fetched
                results["total_issues_synced"] += synced
            except Exception as e:
                results["projects"][project_id] = {"error": str(e)}

        logger.info(f"Full ODS sync completed: {results}")
        return results

    finally:
        sync_service.close()
