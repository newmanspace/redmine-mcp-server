#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix ODS sync order to sync base data first

Correct sync order:
1. Projects (base metadata)
2. Users (user information)  
3. Issues (with journals included)
4. Journals (issue change logs)
5. Journal Details (change details)
"""

import re

file_path = "src/redmine_mcp_server/dws/services/ods_sync_service.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix sync_ods_incremental function
old_incremental = '''def sync_ods_incremental(project_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Run incremental ODS sync for projects

    Args:
        project_ids: Projects to sync (all subscribed if None)

    Returns:
        Sync results
    """
    from .subscription_service import SubscriptionManager

    sync_service = ODSSyncService()
    results = {"projects": {}, "total_fetched": 0, "total_synced": 0}

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

        for project_id in project_ids:
            try:
                fetched, synced = sync_service.sync_ods_issues_incremental(project_id)
                results["projects"][project_id] = {"fetched": fetched, "synced": synced}
                results["total_fetched"] += fetched
                results["total_synced"] += synced
            except Exception as e:
                results["projects"][project_id] = {"error": str(e)}

        logger.info(f"Incremental ODS sync completed: {results}")
        return results

    finally:
        sync_service.close()'''

new_incremental = '''def sync_ods_incremental(project_ids: Optional[List[int]] = None) -> Dict[str, Any]:
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
        sync_service.close()'''

content = content.replace(old_incremental, new_incremental)

# Fix sync_ods_full function
old_full = '''def sync_ods_full(
    project_ids: Optional[List[int]] = None, from_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Run full ODS sync for projects (force refresh)

    Args:
        project_ids: Projects to sync (all subscribed if None)
        from_date: Optional start date

    Returns:
        Sync results
    """
    from .subscription_service import SubscriptionManager

    sync_service = ODSSyncService()
    results = {"projects": {}, "total_fetched": 0, "total_synced": 0}

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

        for project_id in project_ids:
            try:
                fetched, synced = sync_service.sync_ods_issues_full(
                    project_id, from_date
                )
                results["projects"][project_id] = {"fetched": fetched, "synced": synced}
                results["total_fetched"] += fetched
                results["total_synced"] += synced
            except Exception as e:
                results["projects"][project_id] = {"error": str(e)}

        logger.info(f"Full ODS sync completed: {results}")
        return results

    finally:
        sync_service.close()'''

new_full = '''def sync_ods_full(
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
        sync_service.close()'''

content = content.replace(old_full, new_full)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Fixed ODS sync order!")
print("Sync order is now:")
print("  1. Projects (base metadata)")
print("  2. Users (user information)")
print("  3. Issues (with journals included)")
