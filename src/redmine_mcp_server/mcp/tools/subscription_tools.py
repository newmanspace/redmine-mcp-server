#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Tools
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union

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
    project_id: int,
    date: Optional[str] = None,
    compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """获取项目每日统计数据，支持时间维度对比。使用 PostgreSQL 数仓，Token 消耗低 97%。"""
    from datetime import timedelta
    from .redmine_warehouse import DataWarehouse
    import requests
    
    if not redmine:
        return {"error": "Redmine client not initialized."}
    
    try:
        warehouse = DataWarehouse()
        
        # Parse date
        from datetime import date as date_class
        query_date = datetime.strptime(date, '%Y-%m-%d').date() if date else date_class.today()
        
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
                    params={'project_id': project_id, 'limit': limit, 'offset': offset},
                    timeout=30
                )
                data = resp.json()
                issues = data.get('issues', [])
                all_issues.extend(issues)
                
                if len(issues) < limit:
                    break
                
                offset += limit
                logger.info(f"Fetched {len(all_issues)} issues...")
            
            # Sync to warehouse
            yesterday = query_date - timedelta(days=1)
            previous_issues = warehouse.get_issues_snapshot(project_id, yesterday)
            previous_map = {i['issue_id']: i for i in previous_issues}
            warehouse.upsert_issues_batch(project_id, all_issues, query_date, previous_map)
            logger.info(f"Synced {len(all_issues)} issues to warehouse")
        
        # Get statistics from warehouse
        stats = warehouse.get_project_daily_stats(project_id, query_date)
        
        # Get high priority issues
        high_priority = warehouse.get_high_priority_issues(project_id, query_date, limit=20)
        stats['high_priority_count'] = len(high_priority)
        stats['high_priority_issues'] = [
            {
                **issue,
                'url': f"{REDMINE_URL}/issues/{issue['issue_id']}"
            }
            for issue in high_priority
        ]
        
        # Get assignee workload
        stats['top_assignees'] = warehouse.get_top_assignees(project_id, query_date, limit=10)
        
        # Add comparison data
        if compare_with == 'yesterday':
            yesterday = query_date - timedelta(days=1)
            yday_stats = warehouse.get_project_daily_stats(project_id, yesterday)
            stats['yesterday_new'] = yday_stats.get('today_new', 0)
            stats['yesterday_closed'] = yday_stats.get('today_closed', 0)
            stats['change_new'] = stats['today_new'] - stats['yesterday_new']
            stats['change_closed'] = stats['today_closed'] - stats['yesterday_closed']
        
        stats['from_cache'] = True
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": f"Failed to get stats: {str(e)}"}


# ========== Subscription Management Tools ==========

@mcp.tool()
async def subscribe_project(
    project_id: int,
    frequency: str = "daily",
    level: str = "brief",
    push_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    订阅项目报告
    
    Args:
        project_id: 项目 ID
        frequency: 推送频率 (realtime/daily/weekly/monthly)
        level: 报告级别 (brief/detailed)
        push_time: 推送时间 (daily 用 "09:00", weekly 用 "Mon 09:00")
    
    Returns:
        订阅结果
    """
    from .subscriptions import get_subscription_manager
    
    # Get current user ID (from context or default)
    # TODO: Implement user context retrieval
    user_id = "default_user"
    
    # Determine push channel and ID
    # TODO: Auto-detect based on current session channel
    channel = "dingtalk"
    channel_id = "default"
    
    manager = get_subscription_manager()
    result = manager.subscribe(
        user_id=user_id,
        project_id=project_id,
        channel=channel,
        channel_id=channel_id,
        frequency=frequency,
        level=level,
        push_time=push_time
    )
    
    return result


