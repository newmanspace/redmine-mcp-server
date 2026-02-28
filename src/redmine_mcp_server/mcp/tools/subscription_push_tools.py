#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Tools - Subscription Push

Manually trigger subscription report push
"""

from ..server import mcp, logger
from typing import Dict, Any, Optional


@mcp.tool()
async def push_subscription_reports(
    report_type: str = "daily", project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Manually trigger subscription report push

    Args:
        report_type: Report type (daily/weekly/monthly)
        project_id: Project ID (optional, push all subscribed projects if not provided)

    Returns:
        Push statistics
    """
    try:
        from ...dws.services.subscription_push_service import SubscriptionPushService

        logger.info(f"Manual trigger: Pushing {report_type} subscription reports...")

        service = SubscriptionPushService()

        if project_id:
            from ...dws.services.subscription_service import get_subscription_manager

            manager = get_subscription_manager()

            all_subs = manager.list_all_subscriptions()
            project_subs = [
                s
                for s in all_subs
                if s.get("project_id") == project_id and s.get("enabled", True)
            ]

            results = {
                "project_id": project_id,
                "total": len(project_subs),
                "success": 0,
                "failed": 0,
                "details": [],
            }

            for sub in project_subs:
                success = service.push_subscription(sub)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                results["details"].append(
                    {
                        "subscription_id": sub.get("subscription_id"),
                        "channel": sub.get("channel"),
                        "success": success,
                    }
                )

        else:
            if report_type == "daily":
                results = service.push_due_subscriptions("daily")
            elif report_type == "weekly":
                results = service.push_due_subscriptions("weekly")
            elif report_type == "monthly":
                results = service.push_due_subscriptions("monthly")
            else:
                return {
                    "error": f"Invalid report type: {report_type}",
                    "success": False,
                }

        logger.info(f"Push completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Failed to push subscription reports: {e}")
        return {"error": str(e), "success": False}


@mcp.tool()
async def send_project_report_email(
    project_id: int,
    to_email: str,
    report_type: str = "daily",
    report_level: str = "brief",
    include_trend: bool = True,
) -> Dict[str, Any]:
    """
    Send project report email (one-time, without creating subscription)

    Args:
        project_id: Project ID
        to_email: Recipient email
        report_type: Report type (daily/weekly/monthly)
        report_level: Report level (brief/detailed/comprehensive)
        include_trend: Include trend analysis

    Returns:
        Send result
    """
    try:
        from ...dws.services.subscription_push_service import SubscriptionPushService

        logger.info(f"Sending {report_type} report email to {to_email}...")

        service = SubscriptionPushService()

        report = service.generate_report(
            project_id,
            report_type,
            report_level,
            include_trend,
            trend_period=7 if report_type == "daily" else 30,
        )

        if not report or "error" in report:
            return {
                "success": False,
                "error": f"Failed to generate report for project {project_id}",
            }

        try:
            project_data = service.redmine_get(f"projects/{project_id}.json")
            project_name = project_data["project"]["name"]
        except:
            project_name = f"Project {project_id}"

        from ...dws.services.email_service import send_subscription_email

        result = send_subscription_email(to_email, project_name, report, report_level)

        if result.get("success"):
            stats = report.get("stats", {})
            return {
                "success": True,
                "project_id": project_id,
                "project_name": project_name,
                "to_email": to_email,
                "report_type": report_type,
                "report_level": report_level,
                "stats": {
                    "total_issues": stats.get("total_issues", 0),
                    "open_issues": stats.get("open_issues", 0),
                    "closed_issues": stats.get("closed_issues", 0),
                },
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to send email"),
            }

    except Exception as e:
        logger.error(f"Failed to send project report email: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_subscription_scheduler_status() -> Dict[str, Any]:
    """
    Get subscription scheduler status

    Returns:
        Scheduler status information
    """
    try:
        from ..scheduler.subscription_scheduler import get_subscription_scheduler

        scheduler = get_subscription_scheduler()

        if not scheduler:
            return {
                "status": "not_initialized",
                "message": "Subscription scheduler not initialized",
            }

        job_status = scheduler.get_job_status()

        return {
            "status": "running" if job_status["running"] else "stopped",
            "job_count": job_status["job_count"],
            "jobs": job_status["jobs"],
        }

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        return {"error": str(e), "status": "error"}
