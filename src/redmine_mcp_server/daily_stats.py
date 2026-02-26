# /docker/redmine-mcp-server/src/redmine_mcp_server/daily_stats.py
# 新增工具：get_project_daily_stats - 获取项目每日统计数据

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from .redmine_handler import RedmineHandler


async def get_project_daily_stats(
    project_id: int,
    date: Optional[str] = None,
    compare_with: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取项目每日统计数据，支持时间维度对比。
    返回聚合数据而非原始 Issue 列表，适合生成日报。
    
    Args:
        project_id: Redmine 项目 ID
        date: 查询日期 (YYYY-MM-DD), 默认为今天
        compare_with: 对比时间段 ('yesterday', 'last_week', 'last_month')
    
    Returns:
        聚合统计数据字典
    """
    handler = RedmineHandler()
    
    # 计算日期范围
    if date:
        today = datetime.strptime(date, '%Y-%m-%d')
    else:
        today = datetime.now()
    
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # 获取今日数据 (仅总数，不获取详细内容)
    today_str = today.strftime('%Y-%m-%d')
    today_issues = handler.get_issues(
        project_id=project_id,
        created_on=f'>={today_str}',
        limit=1  # 仅获取总数
    )
    
    today_closed = handler.get_issues(
        project_id=project_id,
        status_id='closed',
        updated_on=f'>={today_str}',
        limit=1
    )
    
    # 构建基础统计
    result = {
        'project_id': project_id,
        'date': today_str,
        'total': today_issues.get('total_count', 0),
        'today_new': today_issues.get('total_count', 0),
        'today_closed': today_closed.get('total_count', 0),
    }
    
    # 获取对比数据
    if compare_with == 'yesterday':
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        yesterday_issues = handler.get_issues(
            project_id=project_id,
            created_on=f'>={yesterday_str}&<={yesterday_str}',
            limit=1
        )
        yesterday_closed = handler.get_issues(
            project_id=project_id,
            status_id='closed',
            updated_on=f'>={yesterday_str}&<={yesterday_str}',
            limit=1
        )
        
        result['yesterday_new'] = yesterday_issues.get('total_count', 0)
        result['yesterday_closed'] = yesterday_closed.get('total_count', 0)
        result['change_new'] = result['today_new'] - result['yesterday_new']
        result['change_closed'] = result['today_closed'] - result['yesterday_closed']
    
    # 获取状态分布 (仅获取必要字段)
    all_issues = handler.get_issues(project_id=project_id, limit=500)
    issues_list = all_issues.get('issues', [])
    
    by_status = {}
    by_priority = {}
    for issue in issues_list:
        status = issue.get('status', {}).get('name', 'Unknown')
        priority = issue.get('priority', {}).get('name', 'Unknown')
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
    
    result['by_status'] = by_status
    result['by_priority'] = by_priority
    
    # 获取高优先级 Issue (仅 ID 和标题，限制数量)
    high_priority = handler.get_issues(
        project_id=project_id,
        priority_id='1,2,3',  # 立刻/紧急/高
        status_id='*',
        limit=50
    )
    
    result['high_priority_count'] = high_priority.get('total_count', 0)
    result['high_priority_issues'] = [
        {
            'id': i['id'],
            'subject': i['subject'],
            'priority': i.get('priority', {}).get('name', ''),
            'status': i.get('status', {}).get('name', ''),
            'url': f"{handler.redmine_url}/issues/{i['id']}"
        }
        for i in high_priority.get('issues', [])[:20]  # 限制返回 20 个
    ]
    
    return result
