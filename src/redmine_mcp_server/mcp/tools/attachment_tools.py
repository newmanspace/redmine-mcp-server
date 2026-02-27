#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP - Attachment Management Tools
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union

@mcp.tool()
async def summarize_project_status(project_id: int, days: int = 30) -> Dict[str, Any]:
    """Provide a summary of project status based on issue activity over the
    specified time period.

    Args:
        project_id: The ID of the project to summarize
        days: Number of days to look back for analysis. Defaults to 30.

    Returns:
        A dictionary containing project status summary with issue counts,
        activity metrics, and trends. On error, returns a dictionary with
        an "error" key.
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        # Validate project exists
        try:
            project = redmine.project.get(project_id)
        except ResourceNotFoundError:
            return {"error": f"Project {project_id} not found."}

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_filter = f">={start_date.strftime('%Y-%m-%d')}"

        # Get issues created in the date range
        created_issues = list(
            redmine.issue.filter(project_id=project_id, created_on=date_filter)
        )

        # Get issues updated in the date range
        updated_issues = list(
            redmine.issue.filter(project_id=project_id, updated_on=date_filter)
        )

        # Analyze created issues
        created_stats = _analyze_issues(created_issues)

        # Analyze updated issues
        updated_stats = _analyze_issues(updated_issues)

        # Calculate trends
        total_created = len(created_issues)
        total_updated = len(updated_issues)

        # Get all project issues for context
        all_issues = list(redmine.issue.filter(project_id=project_id))
        all_stats = _analyze_issues(all_issues)

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "identifier": getattr(project, "identifier", ""),
            },
            "analysis_period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
            "recent_activity": {
                "issues_created": total_created,
                "issues_updated": total_updated,
                "created_breakdown": created_stats,
                "updated_breakdown": updated_stats,
            },
            "project_totals": {
                "total_issues": len(all_issues),
                "overall_breakdown": all_stats,
            },
            "insights": {
                "daily_creation_rate": round(total_created / days, 2),
                "daily_update_rate": round(total_updated / days, 2),
                "recent_activity_percentage": round(
                    (total_updated / len(all_issues) * 100) if all_issues else 0, 2
                ),
            },
        }

    except Exception as e:
        return _handle_redmine_error(
            e,
            f"summarizing project {project_id}",
            {"resource_type": "project", "resource_id": project_id},
        )


def _analyze_issues(issues: List[Any]) -> Dict[str, Any]:
    """Helper function to analyze a list of issues and return statistics."""
    if not issues:
        return {
            "by_status": {},
            "by_priority": {},
            "by_assignee": {},
            "total": 0,
        }

    status_counts = {}
    priority_counts = {}
    assignee_counts = {}

    for issue in issues:
        # Count by status
        status_name = getattr(issue.status, "name", "Unknown")
        status_counts[status_name] = status_counts.get(status_name, 0) + 1

        # Count by priority
        priority_name = getattr(issue.priority, "name", "Unknown")
        priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

        # Count by assignee
        assigned_to = getattr(issue, "assigned_to", None)
        if assigned_to:
            assignee_name = getattr(assigned_to, "name", "Unknown")
            assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1
        else:
            assignee_counts["Unassigned"] = assignee_counts.get("Unassigned", 0) + 1

    return {
        "by_status": status_counts,
        "by_priority": priority_counts,
        "by_assignee": assignee_counts,
        "total": len(issues),
    }


