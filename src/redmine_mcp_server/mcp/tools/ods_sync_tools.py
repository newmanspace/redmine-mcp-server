#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Tools - ODS Layer Sync

Tools for triggering ODS layer synchronization.
"""

from ..server import mcp, logger
from typing import Dict, Any, List, Optional
from datetime import datetime


@mcp.tool()
async def sync_ods_incremental(
    project_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Trigger incremental ODS layer sync.

    Syncs issues updated in the last 15 minutes from Redmine API to ODS tables.
    This is a lightweight sync that runs automatically every 10 minutes.

    Args:
        project_ids: List of project IDs to sync. If None, syncs all subscribed projects.

    Returns:
        Sync results with fetched and synced counts per project.

    Example:
        >>> sync_ods_incremental()
        {
            "projects": {
                311: {"fetched": 5, "synced": 5},
                341: {"fetched": 3, "synced": 3}
            },
            "total_fetched": 8,
            "total_synced": 8
        }
    """
    try:
        logger.info(
            f"MCP: Triggering incremental ODS sync for projects: {project_ids or 'all subscribed'}"
        )

        from ...scheduler.tasks import sync_ods_layer_incremental

        result = sync_ods_layer_incremental(project_ids)

        logger.info(f"MCP: Incremental ODS sync completed: {result}")
        return result

    except Exception as e:
        logger.error(f"MCP: Incremental ODS sync failed: {e}")
        return {"error": f"Failed to sync ODS layer: {str(e)}"}


@mcp.tool()
async def sync_ods_full(
    project_ids: Optional[List[int]] = None, from_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger full ODS layer sync (force refresh).

    Syncs all issues from Redmine API to ODS tables.
    Use this to force refresh data or backfill historical data.

    Args:
        project_ids: List of project IDs to sync. If None, syncs all subscribed projects.
        from_date: Optional start date in YYYY-MM-DD format. If None, syncs from project creation.

    Returns:
        Sync results with fetched and synced counts per project.

    Example:
        >>> sync_ods_full(project_ids=[311, 341])
        {
            "projects": {
                311: {"fetched": 150, "synced": 150},
                341: {"fetched": 200, "synced": 200}
            },
            "total_fetched": 350,
            "total_synced": 350
        }

        >>> sync_ods_full(from_date="2026-01-01")
        {
            "projects": {...},
            "total_fetched": 500,
            "total_synced": 500,
            "from_date": "2026-01-01"
        }
    """
    try:
        logger.info(
            f"MCP: Triggering full ODS sync for projects: {project_ids or 'all subscribed'}, from_date: {from_date}"
        )

        # Parse from_date if provided
        parsed_date = None
        if from_date:
            try:
                parsed_date = datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                return {"error": f"Invalid date format: {from_date}. Use YYYY-MM-DD."}

        from ...scheduler.tasks import sync_ods_layer_full

        result = sync_ods_layer_full(project_ids, parsed_date)

        if from_date:
            result["from_date"] = from_date

        logger.info(f"MCP: Full ODS sync completed: {result}")
        return result

    except Exception as e:
        logger.error(f"MCP: Full ODS sync failed: {e}")
        return {"error": f"Failed to sync ODS layer: {str(e)}"}


@mcp.tool()
async def get_ods_sync_status() -> Dict[str, Any]:
    """
    Get ODS layer sync status and statistics.

    Returns:
        ODS sync status including table row counts and data freshness.

    Example:
        >>> get_ods_sync_status()
        {
            "table_counts": {
                "ods_issues": 1500,
                "ods_projects": 15,
                "ods_journals": 5000,
                "ods_users": 100
            },
            "latest_data": {
                "ods_issues": "2026-02-27T14:30:00",
                "ods_journals": "2026-02-27T14:25:00"
            },
            "status": "OK"
        }
    """
    try:
        from ...dws.repository import DataWarehouse

        warehouse = None
        try:
            warehouse = DataWarehouse()

            with warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get table counts
                    tables = ["ods_issues", "ods_projects", "ods_journals", "ods_users"]
                    counts = {}
                    latest_dates = {}

                    for table in tables:
                        cur.execute(f"SELECT COUNT(*) as count FROM warehouse.{table}")
                        result = cur.fetchone()
                        counts[table] = result["count"] if result else 0

                        # Get latest update time if applicable
                        if table in ["ods_issues", "ods_journals"]:
                            date_col = (
                                "updated_on" if table == "ods_issues" else "created_on"
                            )
                            cur.execute(
                                f"SELECT MAX({date_col}) as max_date FROM warehouse.{table}"
                            )
                            result = cur.fetchone()
                            if result and result["max_date"]:
                                latest_dates[table] = (
                                    result["max_date"].isoformat()
                                    if hasattr(result["max_date"], "isoformat")
                                    else str(result["max_date"])
                                )

                    # Check data freshness
                    status = "OK"
                    issues = []

                    for table, max_date_str in latest_dates.items():
                        if max_date_str:
                            max_date = datetime.fromisoformat(max_date_str)
                            age_hours = (
                                datetime.now() - max_date
                            ).total_seconds() / 3600
                            if age_hours > 24:
                                status = "STALE"
                                issues.append(
                                    f"{table} data is {age_hours:.1f} hours old"
                                )

                    return {
                        "table_counts": counts,
                        "latest_data": latest_dates,
                        "status": status,
                        "issues": issues if issues else None,
                    }

        finally:
            if warehouse:
                warehouse.close()

    except Exception as e:
        logger.error(f"MCP: Failed to get ODS sync status: {e}")
        return {"error": f"Failed to get ODS status: {str(e)}"}
