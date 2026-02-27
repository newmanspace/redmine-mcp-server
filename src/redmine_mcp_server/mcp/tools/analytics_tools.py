#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Tools
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union

@mcp.tool()
async def get_sync_progress() -> Dict[str, Any]:
    """
    Get sync progress for all subscribed projects
    
    Returns:
        Sync progress status
    """
    from .redmine_scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    if not scheduler:
        return {
            "success": False,
            "error": "Scheduler not initialized"
        }
    
    progress_info = {}
    for project_id in scheduler.project_ids:
        if project_id in scheduler.project_sync_progress:
            last_synced = scheduler.project_sync_progress[project_id]
            days_synced = (datetime.now() - last_synced).days
            progress_info[project_id] = {
                "last_synced_week": last_synced.isoformat(),
                "days_remaining": max(0, days_synced),
                "status": "in_progress" if days_synced > 7 else "completed"
            }
        else:
            progress_info[project_id] = {
                "status": "not_started"
            }
    
    return {
        "success": True,
        "projects": len(scheduler.project_ids),
        "progress": progress_info,
        "sync_count": scheduler._sync_count
    }


@mcp.tool()
async def analyze_dev_tester_workload(
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyze developer and tester workload based on issue resolution flow
    
    Developer: Person who changes status to "已解决"
    Tester: Person assigned when status changes to "已解决"
    
    Args:
        project_id: Specific project ID (optional, analyze all subscribed if None)
    
    Returns:
        Analysis report
    """
    from .dev_test_analyzer import DevTestAnalyzer, analyze_project, analyze_projects
    from .redmine_scheduler import get_scheduler
    
    try:
        if project_id:
            # Analyze single project
            analysis = analyze_project(project_id)
        else:
            # Analyze all subscribed projects
            scheduler = get_scheduler()
            if not scheduler:
                return {
                    "success": False,
                    "error": "Scheduler not initialized"
                }
            
            project_ids = scheduler.project_ids
            analysis = analyze_projects(project_ids)
        
        # Generate report
        analyzer = DevTestAnalyzer()
        report = analyzer.generate_report(analysis)
        
        return {
            "success": True,
            "analysis": analysis,
            "report": report
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to analyze dev/tester workload"
        }


@mcp.tool()
async def backfill_historical_data(
    project_id: Optional[int] = None,
    from_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Backfill historical daily snapshots from Redmine journals
    
    Args:
        project_id: Specific project ID (optional, backfill all if None)
        from_date: Start date in YYYY-MM-DD format (optional)
    
    Returns:
        Backfill result
    """
    from .backfill_sync import BackfillSync, backfill_all_projects
    from .redmine_scheduler import get_scheduler
    
    try:
        if project_id:
            # Backfill single project
            sync = BackfillSync()
            start_date = datetime.strptime(from_date, '%Y-%m-%d') if from_date else None
            sync.backfill_project(project_id, start_date)
            sync.close()
            
            return {
                "success": True,
                "message": f"Backfill completed for project {project_id}",
                "project_id": project_id
            }
        else:
            # Backfill all subscribed projects
            scheduler = get_scheduler()
            if not scheduler:
                return {
                    "success": False,
                    "error": "Scheduler not initialized"
                }
            
            project_ids = scheduler.project_ids
            start_date = datetime.strptime(from_date, '%Y-%m-%d') if from_date else None
            
            # Run in background to avoid timeout
            import threading
            def run_backfill():
                backfill_all_projects(project_ids)
            
            thread = threading.Thread(target=run_backfill, daemon=True)
            thread.start()
            
            return {
                "success": True,
                "message": f"Backfill started for {len(project_ids)} projects",
                "projects": project_ids,
                "note": "Backfill running in background, check logs for progress"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to backfill historical data"
        }


@mcp.tool()
async def analyze_issue_contributors(issue_id: int) -> Dict[str, Any]:
    """
    分析 Issue 的贡献者（按角色分类）
    
    从数仓中获取 Issue 的所有贡献者，按角色优先级排序：
    - 管理人员 > 实施人员 > 开发人员 > 测试人员
    
    Args:
        issue_id: Issue ID
    
    Returns:
        贡献者列表和汇总统计
    """
    from .redmine_warehouse import DataWarehouse
    from .dev_test_analyzer import DevTestAnalyzer
    
    try:
        warehouse = DataWarehouse()
        
        # 获取贡献者
        contributors = warehouse.get_issue_contributors(issue_id)
        
        # 获取汇总
        summary = warehouse.get_issue_contributor_summary(issue_id)
        
        if not contributors:
            # 如果数仓中没有，尝试从 Redmine 实时分析
            logger.info(f"No contributors in warehouse, analyzing issue {issue_id} from Redmine...")
            
            if redmine:
                analyzer = DevTestAnalyzer()
                try:
                    # Get issue details first to get project_id
                    issue = redmine.issue.get(issue_id)
                    project_id = issue.project.get('id') if hasattr(issue, 'project') else None
                    
                    if project_id:
                        # Use REST API directly to get journals (more reliable)
                        journals = analyzer._get_issue_journals(issue_id)
                        
                        # Extract contributors from journals
                        if journals:
                            contributors_data = analyzer.extract_contributors_from_journals(
                                journals, issue_id, project_id
                            )
                            
                            # Save to warehouse
                            if contributors_data:
                                warehouse.upsert_issue_contributors(issue_id, project_id, contributors_data)
                                contributors = warehouse.get_issue_contributors(issue_id)
                                summary = warehouse.get_issue_contributor_summary(issue_id)
                except Exception as e:
                    logger.error(f"Failed to analyze from Redmine: {e}")
            
            if not contributors:
                warehouse.close()
                return {
                    "issue_id": issue_id, 
                    "message": "Contributors not yet analyzed. Trigger a sync to populate data.",
                    "contributors": [],
                    "summary": None
                }
        
        warehouse.close()
        
        return {
            "issue_id": issue_id,
            "contributors": contributors,
            "summary": summary,
            "from_cache": True
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze contributors: {e}")
        return {"error": f"Failed to analyze contributors: {str(e)}"}


