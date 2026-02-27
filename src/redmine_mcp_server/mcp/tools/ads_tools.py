#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Tools
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union

@mcp.tool()
async def trigger_contributor_sync(
    project_id: Optional[int] = None,
    issue_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    触发贡献者分析同步
    
    Args:
        project_id: 项目 ID（可选，分析整个项目）
        issue_ids: Issue ID 列表（可选，分析特定 Issue）
    
    Returns:
        同步结果
    """
    from .dev_test_analyzer import DevTestAnalyzer
    from .redmine_warehouse import DataWarehouse
    
    try:
        if not redmine:
            return {"error": "Redmine client not initialized"}
        
        analyzer = DevTestAnalyzer()
        warehouse = DataWarehouse()
        results = {"analyzed_issues": [], "errors": []}
        
        if issue_ids:
            # Analyze specific issues
            for iid in issue_ids:
                try:
                    issue = redmine.issue.get(iid, include='journals')
                    proj_id = issue.project.get('id') if hasattr(issue, 'project') else None
                    
                    if proj_id and hasattr(issue, 'journals'):
                        contributors = analyzer.extract_contributors_from_journals(
                            issue.journals, iid, proj_id
                        )
                        if contributors:
                            warehouse.upsert_issue_contributors(iid, proj_id, contributors)
                            results["analyzed_issues"].append(iid)
                except Exception as e:
                    results["errors"].append({"issue_id": iid, "error": str(e)})
        
        elif project_id:
            # Analyze all issues in project
            logger.info(f"Starting contributor analysis for project {project_id}...")
            
            # Get all issues for the project
            offset = 0
            limit = 100
            total_analyzed = 0
            
            while True:
                issues = redmine.issue.filter(project_id=project_id, limit=limit, offset=offset)
                if not issues:
                    break
                
                for issue in issues:
                    try:
                        # Use REST API directly to get journals (more reliable)
                        journals = analyzer._get_issue_journals(issue.id)
                        if journals:
                            contributors = analyzer.extract_contributors_from_journals(
                                journals, issue.id, project_id
                            )
                            if contributors:
                                warehouse.upsert_issue_contributors(issue.id, project_id, contributors)
                                total_analyzed += 1
                    except Exception as e:
                        logger.error(f"Failed to analyze issue {issue.id}: {e}")
                
                offset += limit
                if len(issues) < limit:
                    break
            
            # Refresh project role distribution
            from datetime import date as date_class
            warehouse.refresh_project_role_distribution(project_id, date_class.today())
            
            results["project_id"] = project_id
            results["total_analyzed"] = total_analyzed
        
        warehouse.close()
        
        return {
            "success": True,
            "message": f"Contributor analysis completed",
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Failed to trigger contributor sync: {e}")
        return {"error": f"Failed to trigger contributor sync: {str(e)}"}


if __name__ == "__main__":
    if not redmine:
        logger.warning(
            "Redmine client could not be initialized. Some tools may not work. "
            "Please check your .env file and Redmine server connectivity."
        )
    mcp.run(transport="stdio")
