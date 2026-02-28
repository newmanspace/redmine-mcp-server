#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Tools - Subscription Management
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union


@mcp.tool()
async def unsubscribe_project(project_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Unsubscribe from project

    Args:
        project_id: project_id (optional, unsubscribe all if not provided)

    Returns:
        取消结果
    """
    from ...dws.services.subscription_service import get_subscription_manager

    user_id = "default_user"
    manager = get_subscription_manager()

    result = manager.unsubscribe(user_id=user_id, project_id=project_id)

    # Close warehouse connection

    return result


@mcp.tool()
async def list_my_subscriptions() -> List[Dict[str, Any]]:
    """
    查看我report forsubscription list

    Returns:
        subscription list
    """
    from ...dws.services.subscription_service import get_subscription_manager

    user_id = "default_user"
    manager = get_subscription_manager()

    result = manager.get_user_subscriptions(user_id)

    # Close warehouse connection

    return result


@mcp.tool()
async def get_subscription_stats() -> Dict[str, Any]:
    """
    Get subscription statistics信息

    Returns:
        统计数据
    """
    from ...dws.services.subscription_service import get_subscription_manager

    manager = get_subscription_manager()
    result = manager.get_stats()

    # Close warehouse connection

    return result


@mcp.tool()
async def generate_subscription_report(
    project_id: int, level: str = "brief"
) -> Dict[str, Any]:
    """
    Generate project subscription report (manual trigger)

    Args:
        project_id: Project ID
        level: Report level (brief/detailed)

    Returns:
        Report data
    """
    from .subscription_reporter import get_reporter

    reporter = get_reporter()

    if level == "detailed":
        return reporter.generate_detailed_report(project_id)
    else:
        return reporter.generate_brief_report(project_id)


@mcp.tool()
async def trigger_full_sync(project_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Trigger full data sync for warehouse (manual)

    Args:
        project_id: Specific project ID (optional, sync all if None)

    Returns:
        Sync result
    """
    from .redmine_scheduler import get_scheduler
    from .redmine_warehouse import DataWarehouse

    scheduler = get_scheduler()

    if project_id:
        # Sync single project
        try:
            warehouse = DataWarehouse()
            count = scheduler._sync_project(project_id, incremental=False)
            return {
                "success": True,
                "project_id": project_id,
                "synced_issues": count,
                "message": f"Full sync completed for project {project_id}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to sync project {project_id}",
            }
    else:
        # Sync all subscribed projects
        try:
            # Run in background to avoid timeout
            import threading

            def run_sync():
                scheduler._sync_all_projects(full=True)

            thread = threading.Thread(target=run_sync, daemon=True)
            thread.start()

            return {
                "success": True,
                "message": f"Full sync started for {len(scheduler.project_ids)} projects",
                "projects": scheduler.project_ids,
                "note": "Sync running in background, check logs for progress",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to start full sync",
            }


@mcp.tool()
async def trigger_progressive_sync() -> Dict[str, Any]:
    """
    Trigger progressive weekly sync (manual)
    Syncs one week of data for each project per run

    Returns:
        Sync result
    """
    from .redmine_scheduler import get_scheduler

    scheduler = get_scheduler()

    if not scheduler:
        return {"success": False, "error": "Scheduler not initialized"}

    try:
        # Run in background
        import threading

        def run_sync():
            scheduler._sync_all_projects_progressive()

        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()

        return {
            "success": True,
            "message": f"Progressive weekly sync started for {len(scheduler.project_ids)} projects",
            "projects": scheduler.project_ids,
            "note": "Each run syncs one week of data. Multiple runs needed to complete full history.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start progressive sync",
        }
