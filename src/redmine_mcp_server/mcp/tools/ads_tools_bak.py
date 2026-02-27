#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADS 层报表生成 MCP 工具
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def register_ads_tools(mcp):
    """注册 ADS 报表工具到 MCP"""
    
    @mcp.tool()
    async def generate_contributor_report(
        project_id: int,
        year_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成贡献者分析报表"""
        from .redmine_warehouse import DataWarehouse
        
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')
        
        try:
            warehouse = DataWarehouse()
            
            with warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO warehouse.ads_contributor_report (
                            project_id, year_month, user_id, user_name,
                            role_category, total_issues, total_journals,
                            report_date
                        )
                        SELECT 
                            ic.project_id, %s, ic.user_id, ic.user_name,
                            ic.role_category, COUNT(DISTINCT ic.issue_id),
                            SUM(ic.journal_count), CURRENT_DATE
                        FROM warehouse.dws_issue_contributors ic
                        WHERE ic.project_id = %s
                        GROUP BY ic.user_id, ic.user_name, ic.role_category
                        ON CONFLICT (project_id, year_month, user_id) DO UPDATE SET
                            total_issues = EXCLUDED.total_issues,
                            total_journals = EXCLUDED.total_journals
                    """, (year_month, project_id))
            
            warehouse.close()
            
            return {
                "success": True,
                "message": f"Contributor report generated for project {project_id}, {year_month}"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate contributor report: {e}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def generate_project_health_report(
        project_id: int,
        snapshot_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成项目健康度报表"""
        from .redmine_warehouse import DataWarehouse
        from datetime import date as date_class
        
        try:
            warehouse = DataWarehouse()
            
            with warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    if not snapshot_date:
                        cur.execute("""
                            SELECT MAX(snapshot_date) as max_date 
                            FROM warehouse.dws_project_daily_summary 
                            WHERE project_id = %s
                        """, (project_id,))
                        result = cur.fetchone()
                        snapshot_date = result['max_date'].isoformat() if result and result['max_date'] else date_class.today().isoformat()
                    
                    cur.execute("""
                        SELECT * FROM warehouse.dws_project_daily_summary
                        WHERE project_id = %s AND snapshot_date = %s
                    """, (project_id, snapshot_date))
                    
                    summary = cur.fetchone()
                    
                    if not summary:
                        warehouse.close()
                        return {"success": False, "message": "No data"}
                    
                    total = summary['total_issues']
                    closed = summary['status_closed']
                    health_score = min(100, (closed / total * 100) if total > 0 else 100)
                    risk_level = 'low' if health_score >= 80 else 'medium' if health_score >= 60 else 'high' if health_score >= 40 else 'critical'
                    
                    cur.execute("""
                        INSERT INTO warehouse.ads_project_health_report (
                            project_id, snapshot_date, total_issues,
                            closed_issues, health_score, risk_level, report_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
                        ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
                            health_score = EXCLUDED.health_score,
                            risk_level = EXCLUDED.risk_level
                    """, (project_id, snapshot_date, total, closed, health_score, risk_level))
            
            warehouse.close()
            
            return {
                "success": True,
                "project_id": project_id,
                "health_score": round(health_score, 2),
                "risk_level": risk_level
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @mcp.tool()
    async def generate_all_ads_reports(
        project_ids: Optional[List[int]] = None,
        year_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成所有 ADS 报表"""
        from .redmine_warehouse import DataWarehouse
        
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')
        
        try:
            warehouse = DataWarehouse()
            count = 0
            
            with warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    if not project_ids:
                        cur.execute("SELECT DISTINCT project_id FROM warehouse.dws_project_daily_summary")
                        project_ids = [row['project_id'] for row in cur.fetchall()]
                    
                    for pid in project_ids:
                        try:
                            cur.execute("""
                                INSERT INTO warehouse.ads_contributor_report (
                                    project_id, year_month, user_id, user_name,
                                    role_category, total_issues, total_journals, report_date
                                )
                                SELECT project_id, %s, user_id, user_name, role_category,
                                    COUNT(DISTINCT issue_id), SUM(journal_count), CURRENT_DATE
                                FROM warehouse.dws_issue_contributors
                                WHERE project_id = %s
                                GROUP BY user_id, user_name, role_category
                                ON CONFLICT (project_id, year_month, user_id) DO UPDATE SET
                                    total_issues = EXCLUDED.total_issues
                            """, (year_month, pid))
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed for project {pid}: {e}")
            
            warehouse.close()
            
            return {
                "success": True,
                "message": f"Generated reports for {count} projects",
                "projects": count
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_contributor_ranking(
        project_id: int,
        year_month: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取贡献者排行榜"""
        from .redmine_warehouse import DataWarehouse
        
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')
        
        try:
            warehouse = DataWarehouse()
            
            with warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT user_id, user_name, role_category,
                            total_issues, total_journals, resolved_issues
                        FROM warehouse.ads_contributor_report
                        WHERE project_id = %s AND year_month = %s
                        ORDER BY total_issues DESC
                        LIMIT %s
                    """, (project_id, year_month, limit))
                    
                    rankings = [dict(row) for row in cur.fetchall()]
            
            warehouse.close()
            
            return {"project_id": project_id, "rankings": rankings}
            
        except Exception as e:
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_project_health_latest(
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取最新项目健康度"""
        from .redmine_warehouse import DataWarehouse
        
        try:
            warehouse = DataWarehouse()
            
            with warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    if project_id:
                        cur.execute("""
                            SELECT * FROM warehouse.ads_project_health_report
                            WHERE project_id = %s
                            ORDER BY snapshot_date DESC LIMIT 1
                        """, (project_id,))
                    else:
                        cur.execute("""
                            SELECT DISTINCT ON (project_id) *
                            FROM warehouse.ads_project_health_report
                            ORDER BY project_id, snapshot_date DESC
                        """)
                    
                    health_data = [dict(row) for row in cur.fetchall()]
            
            warehouse.close()
            
            return {"health_reports": health_data}
            
        except Exception as e:
            return {"error": str(e)}
