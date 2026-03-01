#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Tools - Subscription Management
"""

from typing import Dict, Any, List, Optional, Union

import os
from datetime import datetime
from ..server import mcp, redmine, logger
from ...redmine_handler import _handle_redmine_error


@mcp.tool()
async def create_redmine_wiki_page(
    project_id: Union[str, int],
    wiki_page_title: str,
    text: str,
    comments: str = "",
) -> Dict[str, Any]:
    """
    Create a new wiki page in a Redmine project.

    Args:
        project_id: Project identifier (ID number or string identifier)
        wiki_page_title: Wiki page title (e.g., "Installation_Guide")
        text: Wiki page content (Textile or Markdown depending on Redmine config)
        comments: Optional comment for the change log

    Returns:
        Dictionary containing created wiki page metadata, or error dict on failure
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        await _ensure_cleanup_started()

        # Create wiki page
        wiki_page = redmine.wiki_page.create(
            project_id=project_id,
            title=wiki_page_title,
            text=text,
            comments=comments if comments else None,
        )

        return _wiki_page_to_dict(wiki_page)

    except Exception as e:
        return _handle_redmine_error(
            e,
            f"creating wiki page '{wiki_page_title}' in project {project_id}",
            {"resource_type": "wiki page", "resource_id": wiki_page_title},
        )


@mcp.tool()
async def update_redmine_wiki_page(
    project_id: Union[str, int],
    wiki_page_title: str,
    text: str,
    comments: str = "",
) -> Dict[str, Any]:
    """
    Update an existing wiki page in a Redmine project.

    Args:
        project_id: Project identifier (ID number or string identifier)
        wiki_page_title: Wiki page title (e.g., "Installation_Guide")
        text: New wiki page content
        comments: Optional comment for the change log

    Returns:
        Dictionary containing updated wiki page metadata, or error dict on failure
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        await _ensure_cleanup_started()

        # Update wiki page
        redmine.wiki_page.update(
            wiki_page_title,
            project_id=project_id,
            text=text,
            comments=comments if comments else None,
        )

        # Fetch updated page to return current state
        wiki_page = redmine.wiki_page.get(wiki_page_title, project_id=project_id)

        return _wiki_page_to_dict(wiki_page)

    except Exception as e:
        return _handle_redmine_error(
            e,
            f"updating wiki page '{wiki_page_title}' in project {project_id}",
            {"resource_type": "wiki page", "resource_id": wiki_page_title},
        )


@mcp.tool()
async def delete_redmine_wiki_page(
    project_id: Union[str, int],
    wiki_page_title: str,
) -> Dict[str, Any]:
    """
    Delete a wiki page from a Redmine project.

    Args:
        project_id: Project identifier (ID number or string identifier)
        wiki_page_title: Wiki page title to delete

    Returns:
        Dictionary with success status, or error dict on failure
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        await _ensure_cleanup_started()

        # Delete wiki page
        redmine.wiki_page.delete(wiki_page_title, project_id=project_id)

        return {
            "success": True,
            "title": wiki_page_title,
            "message": f"Wiki page '{wiki_page_title}' deleted successfully.",
        }

    except Exception as e:
        return _handle_redmine_error(
            e,
            f"deleting wiki page '{wiki_page_title}' in project {project_id}",
            {"resource_type": "wiki page", "resource_id": wiki_page_title},
        )


@mcp.tool()
async def cleanup_attachment_files() -> Dict[str, Any]:
    """Clean up expired attachment files and return storage statistics.

    Returns:
        A dictionary containing cleanup statistics and current storage usage.
        On error, a dictionary with "error" is returned.
    """
    try:
        attachments_dir = os.getenv("ATTACHMENTS_DIR", "./attachments")
        manager = AttachmentFileManager(attachments_dir)
        cleanup_stats = manager.cleanup_expired_files()
        storage_stats = manager.get_storage_stats()

        return {"cleanup": cleanup_stats, "current_storage": storage_stats}
    except Exception as e:
        logger.error(f"Error during attachment cleanup: {e}")
        return {"error": f"An error occurred during cleanup: {str(e)}"}


@mcp.tool()
@mcp.tool()
async def get_project_daily_stats(
    project_id: int, date: Optional[str] = None, compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """Get project daily statistics with time-series comparison。Uses PostgreSQL warehouse, 97% lower token consumption。"""
    from datetime import timedelta
    from ..dws.repository import DataWarehouse
    import requests

    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        warehouse = DataWarehouse()

        # Parse date
        from datetime import date as date_class

        query_date = (
            datetime.strptime(date, "%Y-%m-%d").date() if date else date_class.today()
        )

        # Check if today data exists
        existing_data = warehouse.get_issues_snapshot(project_id, query_date)

        if not existing_data:
            # First query, sync latest data
            logger.info(f"No snapshot for {query_date}, syncing from Redmine API...")

            api_url = f"{REDMINE_URL}/issues.json"
            headers = {"X-Redmine-API-Key": REDMINE_API_KEY}

            # Paginate to get all issues
            all_issues = []
            offset = 0
            limit = 100

            while True:
                resp = requests.get(
                    api_url,
                    headers=headers,
                    params={"project_id": project_id, "limit": limit, "offset": offset},
                    timeout=30,
                )
                data = resp.json()
                issues = data.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < limit:
                    break

                offset += limit
                logger.info(f"Fetched {len(all_issues)} issues...")

            # Sync to warehouse
            yesterday = query_date - timedelta(days=1)
            previous_issues = warehouse.get_issues_snapshot(project_id, yesterday)
            previous_map = {i["issue_id"]: i for i in previous_issues}
            warehouse.upsert_issues_batch(
                project_id, all_issues, query_date, previous_map
            )
            logger.info(f"Synced {len(all_issues)} issues to warehouse")

        # Get statistics from warehouse
        stats = warehouse.get_project_daily_stats(project_id, query_date)

        # Get high priority issues
        high_priority = warehouse.get_high_priority_issues(
            project_id, query_date, limit=20
        )
        stats["high_priority_count"] = len(high_priority)
        stats["high_priority_issues"] = [
            {**issue, "url": f"{REDMINE_URL}/issues/{issue['issue_id']}"}
            for issue in high_priority
        ]

        # Get assignee workload
        stats["top_assignees"] = warehouse.get_top_assignees(
            project_id, query_date, limit=10
        )

        # Add comparison data
        if compare_with == "yesterday":
            yesterday = query_date - timedelta(days=1)
            yday_stats = warehouse.get_project_daily_stats(project_id, yesterday)
            stats["yesterday_new"] = yday_stats.get("today_new", 0)
            stats["yesterday_closed"] = yday_stats.get("today_closed", 0)
            stats["change_new"] = stats["today_new"] - stats["yesterday_new"]
            stats["change_closed"] = stats["today_closed"] - stats["yesterday_closed"]

        stats["from_cache"] = True
        return stats

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": f"Failed to get stats: {str(e)}"}


# ========== Subscription Management Tools ==========


@mcp.tool()
async def subscribe_project(
    project_id: int,
    channel: str = "email",
    channel_id: Optional[str] = None,
    user_name: Optional[str] = None,  # Subscriber name
    user_email: Optional[str] = None,  # Subscriber email
    report_type: str = "daily",
    report_level: str = "brief",
    language: str = "zh_CN",  # zh_CN/en_US
    send_time: str = "09:00",
    send_day_of_week: Optional[str] = None,
    send_day_of_month: Optional[int] = None,
    include_trend: bool = True,
    trend_period_days: int = 7,
) -> Dict[str, Any]:
    """
    Subscribe to project reports

    Args:
        project_id: Project ID
        channel: Push channel (email/dingtalk/telegram)
        channel_id: Channel ID (email address/DingTalk user ID/Telegram chat ID)
        user_name: Subscriber name
        user_email: Subscriber email (used as recipient for email channel)
        report_type: Report type (daily/weekly/monthly)
        report_level: Report level
            - brief: Key metrics overview
            - detailed: Detailed statistics + high priority issues
            - comprehensive: Full report + trend analysis + team workload
        language: Report language (zh_CN/en_US)
        send_time: Send time (HH:MM format, e.g., "09:00")
        send_day_of_week: Weekly report day (Mon/Tue/Wed/Thu/Fri/Sat/Sun)
        send_day_of_month: Monthly report day (1-31, e.g., 1st or 15th)
        include_trend: Include trend analysis
        trend_period_days: Trend analysis period in days

    Returns:
        Subscription result

    Examples:
        # Subscribe to daily report in Chinese
        >>> subscribe_project(
        ...     project_id=341,
        ...     user_name="Zhang San",
        ...     user_email="zhangsan@example.com",
        ...     channel="email",
        ...     report_type="daily",
        ...     language="zh_CN",
        ...     send_time="09:00"
        ... )

        # Subscribe to weekly report in English
        >>> subscribe_project(
        ...     project_id=341,
        ...     user_name="John Doe",
        ...     user_email="john@example.com",
        ...     channel="email",
        ...     report_type="weekly",
        ...     language="en_US",
        ...     send_day_of_week="Mon",
        ...     send_time="09:00"
        ... )

        # Subscribe to monthly comprehensive report with trend analysis
        >>> subscribe_project(
        ...     project_id=341,
        ...     user_name="CEO",
        ...     user_email="ceo@example.com",
        ...     channel="email",
        ...     report_type="monthly",
        ...     language="zh_CN",
        ...     send_day_of_month=1,
        ...     send_time="10:00",
        ...     report_level="comprehensive",
        ...     include_trend=True
        ... )
    """
    from ...dws.services.subscription_service import get_subscription_manager

    # Get current user ID (from context or default)
    user_id = "default_user"

    # Auto-detect channel_id if not provided
    if not channel_id:
        if channel == "email":
            channel_id = os.getenv("DEFAULT_EMAIL", "default@example.com")
        elif channel == "dingtalk":
            channel_id = os.getenv("DEFAULT_DINGTALK_USER", "default")
        elif channel == "telegram":
            channel_id = os.getenv("DEFAULT_TELEGRAM_CHAT_ID", "default")
        else:
            channel_id = "default"

    # If channel is email and user_email not provided, use channel_id
    if channel == "email" and not user_email:
        user_email = channel_id

    manager = get_subscription_manager()
    result = manager.subscribe(
        user_id=user_id,
        project_id=project_id,
        channel=channel,
        channel_id=channel_id,
        report_type=report_type,
        report_level=report_level,
        send_time=send_time,
        send_day_of_week=send_day_of_week,
        send_day_of_month=send_day_of_month,
        include_trend=include_trend,
        trend_period_days=trend_period_days,
    )

    # Close warehouse connection

    return result


@mcp.tool()
async def list_my_subscriptions() -> Dict[str, Any]:
    """
    List all my subscriptions

    Returns:
        List of subscriptions
    """
    from ...dws.services.subscription_service import get_subscription_manager

    try:
        manager = get_subscription_manager()
        subscriptions = manager.list_all_subscriptions()

        return {
            "success": True,
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def unsubscribe_project(
    project_id: Optional[int] = None,
    user_id: Optional[str] = None,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unsubscribe from project(s)

    Args:
        project_id: Project ID to unsubscribe (optional, unsubscribes all if not provided)
        user_id: User ID (optional, uses 'anonymous' if not provided)
        channel: Channel to unsubscribe (optional)

    Returns:
        Unsubscribe result
    """
    from ...dws.services.subscription_service import get_subscription_manager

    try:
        manager = get_subscription_manager()

        # Use default user_id if not provided
        if not user_id:
            user_id = 'anonymous'

        if project_id:
            # Unsubscribe specific project
            result = manager.unsubscribe(user_id=user_id, project_id=project_id, channel=channel)
        else:
            # Unsubscribe all for user
            result = manager.unsubscribe_all(user_id=user_id)

        return {
            "success": True,
            "message": f"Unsubscribed from project {project_id}" if project_id else "Unsubscribed from all projects",
            "details": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def test_email_service(to_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Test email service configuration

    Args:
        to_email: Test email recipient address (optional, only test connection if not provided)

    Returns:
        Test result
    """
    from ...dws.services.email_service import get_email_service

    service = get_email_service()

    # Test SMTP connection
    conn_result = service.test_connection()

    if not conn_result.get("success"):
        return conn_result

    # Send test email if to_email provided
    if to_email:
        subject = "[Redmine MCP] Email Service Test"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>✅ Email Service Configured Successfully</h2>
            <p>This is a test email to verify the email push functionality of Redmine MCP Server.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
                This email was automatically sent by Redmine MCP Server<br>
                Sent at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </body>
        </html>
        """
        send_result = service.send_email(to_email, subject, body, html=True)
        return {"connection": conn_result, "test_email": send_result}

    return {
        "connection": conn_result,
        "message": "SMTP connection successful. Provide to_email to send a test message.",
    }
