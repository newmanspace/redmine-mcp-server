# /docker/redmine-mcp-server/src/redmine_mcp_server/daily_stats.py
# New tool: get_project_daily_stats - Get daily project statistics

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from .redmine_handler import RedmineHandler


async def get_project_daily_stats(
    project_id: int, date: Optional[str] = None, compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """
    getproject每日statisticsdata，supporttime维度对比。
    return聚合data而非原始 Issue list，适合generate日报。

    Args:
        project_id: Redmine project ID
        date: querydate (YYYY-MM-DD), default为今天
        compare_with: 对比time段 ('yesterday', 'last_week', 'last_month')

    Returns:
        聚合statisticsdatadictionary
    """
    handler = RedmineHandler()

    # Calculate date range
    if date:
        today = datetime.strptime(date, "%Y-%m-%d")
    else:
        today = datetime.now()

    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)

    # Get today data (only count, no details)
    today_str = today.strftime("%Y-%m-%d")
    today_issues = handler.get_issues(
        # Only get count
        project_id=project_id,
        created_on=f">={today_str}",
        limit=1,
    )

    today_closed = handler.get_issues(
        project_id=project_id, status_id="closed", updated_on=f">={today_str}", limit=1
    )

    # Build basic statistics
    result = {
        "project_id": project_id,
        "date": today_str,
        "total": today_issues.get("total_count", 0),
        "today_new": today_issues.get("total_count", 0),
        "today_closed": today_closed.get("total_count", 0),
    }

    # Get comparison data
    if compare_with == "yesterday":
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        yesterday_issues = handler.get_issues(
            project_id=project_id,
            created_on=f">={yesterday_str}&<={yesterday_str}",
            limit=1,
        )
        yesterday_closed = handler.get_issues(
            project_id=project_id,
            status_id="closed",
            updated_on=f">={yesterday_str}&<={yesterday_str}",
            limit=1,
        )

        result["yesterday_new"] = yesterday_issues.get("total_count", 0)
        result["yesterday_closed"] = yesterday_closed.get("total_count", 0)
        result["change_new"] = result["today_new"] - result["yesterday_new"]
        result["change_closed"] = result["today_closed"] - result["yesterday_closed"]

    # Get status distribution (only essential fields)
    all_issues = handler.get_issues(project_id=project_id, limit=500)
    issues_list = all_issues.get("issues", [])

    by_status = {}
    by_priority = {}
    for issue in issues_list:
        status = issue.get("status", {}).get("name", "Unknown")
        priority = issue.get("priority", {}).get("name", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    result["by_status"] = by_status
    result["by_priority"] = by_priority

    # Get high priority issues (only ID and title, limited)
    high_priority = handler.get_issues(
        project_id=project_id,
        priority_id="1,2,3",  # Immediate/Urgent/High
        status_id="*",
        limit=50,
    )

    result["high_priority_count"] = high_priority.get("total_count", 0)
    result["high_priority_issues"] = [
        {
            "id": i["id"],
            "subject": i["subject"],
            "priority": i.get("priority", {}).get("name", ""),
            "status": i.get("status", {}).get("name", ""),
            "url": f"{handler.redmine_url}/issues/{i['id']}",
        }
        for i in high_priority.get("issues", [])[:20]  # Limit to 20 issues
    ]

    return result
