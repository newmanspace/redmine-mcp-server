#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP - Project Status Summary Tools (DWS-powered)
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, date

try:
    from ...dws.repository import DataWarehouse

    DWS_AVAILABLE = True
except ImportError:
    DWS_AVAILABLE = False
    logger.warning("DWS repository not available, will fallback to Redmine API")


@mcp.tool()
async def summarize_project_status(project_id: int, days: int = 30) -> Dict[str, Any]:
    try:
        if DWS_AVAILABLE:
            result = await _summarize_from_dws(project_id, days)
            if result and not result.get("error"):
                return result
            logger.info(
                f"DWS has no data for project {project_id}, falling back to API"
            )
        return await _summarize_from_api(project_id, days)
    except Exception as e:
        logger.error(f"Failed to summarize project {project_id}: {e}")
        return {"error": f"Failed to summarize project {project_id}: {str(e)}"}


async def _summarize_from_dws(project_id: int, days: int = 30) -> Dict[str, Any]:
    warehouse = None
    try:
        warehouse = DataWarehouse()
        today = date.today()
        start_date = today - timedelta(days=days)

        current_stats = warehouse.get_project_daily_stats(project_id, today)
        if not current_stats.get("from_cache", False):
            return {"error": "No DWS data available for this project"}

        historical_stats = []
        for d in range(0, days, 7):
            sample_date = today - timedelta(days=d)
            stats = warehouse.get_project_daily_stats(project_id, sample_date)
            if stats.get("from_cache", False):
                historical_stats.append(
                    {
                        "date": sample_date.isoformat(),
                        "total": stats.get("total", 0),
                        "new": stats.get("today_new", 0),
                        "closed": stats.get("today_closed", 0),
                    }
                )

        top_assignees = warehouse.get_top_assignees(project_id, today, limit=10)
        high_priority_issues = warehouse.get_high_priority_issues(
            project_id, today, limit=20
        )
        role_distribution = warehouse.get_project_role_distribution(project_id, today)

        total_issues = current_stats.get("total", 0)
        new_today = current_stats.get("today_new", 0)
        closed_today = current_stats.get("today_closed", 0)
        updated_today = current_stats.get("today_updated", 0)

        avg_new_per_day = 0
        avg_closed_per_day = 0
        if historical_stats:
            avg_new_per_day = sum(s.get("new", 0) for s in historical_stats) / len(
                historical_stats
            )
            avg_closed_per_day = sum(
                s.get("closed", 0) for s in historical_stats
            ) / len(historical_stats)

        by_status = current_stats.get("by_status", {})
        by_priority = current_stats.get("by_priority", {})

        insights = _generate_dws_insights(
            total_issues,
            new_today,
            closed_today,
            by_status,
            by_priority,
            high_priority_issues,
            top_assignees,
        )

        return {
            "project": {"id": project_id, "from_dws": True},
            "analysis_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat(),
            },
            "recent_activity": {
                "issues_created": new_today,
                "issues_updated": updated_today,
                "issues_closed": closed_today,
                "avg_new_per_day": round(avg_new_per_day, 2),
                "avg_closed_per_day": round(avg_closed_per_day, 2),
            },
            "status_breakdown": by_status,
            "priority_breakdown": by_priority,
            "project_totals": {"total_issues": total_issues},
            "top_assignees": top_assignees[:10],
            "high_priority_issues": high_priority_issues[:10],
            "role_distribution": role_distribution,
            "historical_trend": historical_stats[:5],
            "insights": insights,
        }
    except Exception as e:
        logger.error(f"DWS summarize failed: {e}")
        return {"error": f"DWS error: {str(e)}"}
    finally:
        if warehouse:
            warehouse.close()


async def _summarize_from_api(project_id: int, days: int = 30) -> Dict[str, Any]:
    if not redmine:
        return {"error": "Redmine client not initialized."}
    try:
        project = redmine.project.get(project_id)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_filter = ">=" + start_date.strftime("%Y-%m-%d")

        created_issues = list(
            redmine.issue.filter(project_id=project_id, created_on=date_filter)
        )
        updated_issues = list(
            redmine.issue.filter(project_id=project_id, updated_on=date_filter)
        )
        created_stats = _analyze_issues(created_issues)
        updated_stats = _analyze_issues(updated_issues)

        total_created = len(created_issues)
        total_updated = len(updated_issues)
        all_issues = list(redmine.issue.filter(project_id=project_id))
        all_stats = _analyze_issues(all_issues)

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "identifier": getattr(project, "identifier", ""),
                "from_dws": False,
                "source": "Redmine API (fallback)",
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
        logger.error(f"API summarize failed: {e}")
        return {"error": f"API error: {str(e)}"}


def _analyze_issues(issues: List[Any]) -> Dict[str, Any]:
    if not issues:
        return {"by_status": {}, "by_priority": {}, "by_assignee": {}, "total": 0}
    status_counts, priority_counts, assignee_counts = {}, {}, {}
    for issue in issues:
        status_name = getattr(issue.status, "name", "Unknown")
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
        priority_name = getattr(issue.priority, "name", "Unknown")
        priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1
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


def _generate_dws_insights(
    total_issues,
    new_today,
    closed_today,
    by_status,
    by_priority,
    high_priority_issues,
    top_assignees,
):
    insights = {"alerts": [], "suggestions": []}
    overdue_count = len(
        [
            i
            for i in high_priority_issues
            if i.get("status_name") not in ["已关闭", "已解决"]
        ]
    )
    if overdue_count > 5:
        insights["alerts"].append(
            {
                "type": "high_priority_overdue",
                "severity": "high",
                "message": f"发现 {overdue_count} 个未关闭的高优先级 Issue",
                "count": overdue_count,
            }
        )
    for assignee in top_assignees[:3]:
        task_count = assignee.get("total", 0)
        if task_count > 30:
            insights["alerts"].append(
                {
                    "type": "workload_high",
                    "severity": "medium",
                    "message": f"{assignee.get('assigned_to_name')} 负载过高 ({task_count} 任务)",
                    "assignee": assignee.get("assigned_to_name"),
                    "task_count": task_count,
                }
            )
    if new_today > 20:
        insights["suggestions"].append("今日新增 Issue 较多，建议安排优先级评审")
    if closed_today == 0 and total_issues > 100:
        insights["suggestions"].append("今日无关闭 Issue，建议关注整体进度")
    in_progress = by_status.get("进行中", 0)
    if in_progress > 50:
        insights["suggestions"].append(
            f"进行中的 Issue 较多 ({in_progress})，建议加快处理速度"
        )
    return insights
