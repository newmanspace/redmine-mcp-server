#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADS 层报表生成脚本

生成以下报表：
- 贡献者分析报表
- 项目健康度报表
- 用户工作量报表
- 团队绩效报表
"""

import os
import sys
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from decimal import Decimal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
WAREHOUSE_DB_HOST = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
WAREHOUSE_DB_PORT = os.getenv("WAREHOUSE_DB_PORT", "5432")
WAREHOUSE_DB_NAME = os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse")
WAREHOUSE_DB_USER = os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse")
WAREHOUSE_DB_PASSWORD = os.getenv("WAREHOUSE_DB_PASSWORD")

import psycopg2
from psycopg2.extras import RealDictCursor


class ADSReportGenerator:
    """ADS 层报表生成器"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host=WAREHOUSE_DB_HOST,
                port=WAREHOUSE_DB_PORT,
                dbname=WAREHOUSE_DB_NAME,
                user=WAREHOUSE_DB_USER,
                password=WAREHOUSE_DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connected")
        except Exception as e:
            logger.error(f"Failed to connect database: {e}")
            raise
    
    def close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def generate_contributor_report(self, project_id: int, year_month: str) -> int:
        """
        生成贡献者分析报表
        
        Args:
            project_id: 项目 ID
            year_month: 年月 (YYYY-MM)
        """
        logger.info(f"Generating contributor report for project {project_id}, {year_month}")
        
        try:
            # 从数仓聚合贡献者数据
            self.cursor.execute("""
                INSERT INTO warehouse.ads_contributor_report (
                    project_id, project_name, year_month, user_id, user_name,
                    role_category, total_issues, total_journals, resolved_issues,
                    verified_issues, as_manager, as_implementation, as_developer, as_tester,
                    report_date
                )
                SELECT 
                    ic.project_id,
                    (SELECT name FROM warehouse.ods_projects WHERE project_id = ic.project_id) as project_name,
                    %s as year_month,
                    ic.user_id,
                    ic.user_name,
                    ic.role_category,
                    COUNT(DISTINCT ic.issue_id) as total_issues,
                    SUM(ic.journal_count) as total_journals,
                    SUM(ic.status_change_count) as resolved_issues,
                    0 as verified_issues,
                    SUM(CASE WHEN ic.role_category='manager' THEN 1 ELSE 0 END) as as_manager,
                    SUM(CASE WHEN ic.role_category='implementation' THEN 1 ELSE 0 END) as as_implementation,
                    SUM(CASE WHEN ic.role_category='developer' THEN 1 ELSE 0 END) as as_developer,
                    SUM(CASE WHEN ic.role_category='tester' THEN 1 ELSE 0 END) as as_tester,
                    CURRENT_DATE as report_date
                FROM warehouse.dws_issue_contributors ic
                JOIN warehouse.dwd_issue_daily_snapshot ids ON ic.issue_id = ids.issue_id
                WHERE ic.project_id = %s
                  AND ids.snapshot_date >= (%s || '-01')::DATE
                  AND ids.snapshot_date < ((%s || '-01')::DATE + INTERVAL '1 month')
                GROUP BY ic.project_id, ic.user_id, ic.user_name, ic.role_category
                ON CONFLICT (project_id, year_month, user_id) DO UPDATE SET
                    total_issues = EXCLUDED.total_issues,
                    total_journals = EXCLUDED.total_journals,
                    resolved_issues = EXCLUDED.resolved_issues,
                    as_manager = EXCLUDED.as_manager,
                    as_implementation = EXCLUDED.as_implementation,
                    as_developer = EXCLUDED.as_developer,
                    as_tester = EXCLUDED.as_tester,
                    report_date = EXCLUDED.report_date
            """, (year_month, project_id, year_month, year_month))
            
            self.conn.commit()
            
            # 获取生成的记录数
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM warehouse.ads_contributor_report
                WHERE project_id = %s AND year_month = %s
            """, (project_id, year_month))
            
            result = self.cursor.fetchone()
            count = result['count'] if result else 0
            
            logger.info(f"Generated {count} contributor records")
            return count
            
        except Exception as e:
            logger.error(f"Failed to generate contributor report: {e}")
            self.conn.rollback()
            raise
    
    def generate_project_health_report(self, project_id: int, snapshot_date: date) -> int:
        """
        生成项目健康度报表
        
        Args:
            project_id: 项目 ID
            snapshot_date: 快照日期
        """
        logger.info(f"Generating project health report for project {project_id}, {snapshot_date}")
        
        try:
            # 获取项目统计数据
            self.cursor.execute("""
                SELECT * FROM warehouse.dws_project_daily_summary
                WHERE project_id = %s AND snapshot_date = %s
            """, (project_id, snapshot_date.isoformat()))
            
            summary = self.cursor.fetchone()
            
            if not summary:
                logger.warning(f"No summary data for project {project_id} on {snapshot_date}")
                return 0
            
            # 计算健康度指标
            total = summary['total_issues']
            open_issues = summary['status_new'] + summary['status_in_progress']
            closed = summary['status_closed']
            
            # 健康度评分 (简化版)
            if total > 0:
                close_rate = closed / total
                health_score = min(100, close_rate * 100)
            else:
                health_score = 100
            
            # 风险等级
            if health_score >= 80:
                risk_level = 'low'
            elif health_score >= 60:
                risk_level = 'medium'
            elif health_score >= 40:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            # 插入报表
            self.cursor.execute("""
                INSERT INTO warehouse.ads_project_health_report (
                    project_id, project_name, snapshot_date,
                    total_issues, new_issues, closed_issues, open_issues,
                    status_new, status_in_progress, status_resolved, status_closed,
                    priority_immediate, priority_urgent, priority_high,
                    health_score, risk_level, report_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
                    total_issues = EXCLUDED.total_issues,
                    health_score = EXCLUDED.health_score,
                    risk_level = EXCLUDED.risk_level,
                    report_date = EXCLUDED.report_date
            """, (
                project_id,
                (SELECT name FROM warehouse.ods_projects WHERE project_id = %s),
                snapshot_date.isoformat(),
                total,
                summary['new_issues'],
                summary['closed_issues'],
                open_issues,
                summary['status_new'],
                summary['status_in_progress'],
                summary['status_resolved'],
                summary['status_closed'],
                summary['priority_immediate'],
                summary['priority_urgent'],
                summary['priority_high'],
                health_score,
                risk_level
            ))
            
            self.conn.commit()
            logger.info("Project health report generated")
            return 1
            
        except Exception as e:
            logger.error(f"Failed to generate project health report: {e}")
            self.conn.rollback()
            raise
    
    def generate_user_workload_report(self, user_id: int, year_month: str) -> int:
        """
        生成用户工作量报表
        
        Args:
            user_id: 用户 ID
            year_month: 年月 (YYYY-MM)
        """
        logger.info(f"Generating user workload report for user {user_id}, {year_month}")
        
        try:
            # 聚合用户工作量
            self.cursor.execute("""
                INSERT INTO warehouse.ads_user_workload_report (
                    user_id, user_name, year_month,
                    total_projects, total_issues, total_journals,
                    as_manager, as_implementation, as_developer, as_tester,
                    resolved_issues, report_date
                )
                SELECT 
                    uwr.user_id,
                    uwr.user_name,
                    uwr.year_month,
                    COUNT(DISTINCT uwr.project_id) as total_projects,
                    SUM(uwr.total_issues) as total_issues,
                    SUM(uwr.total_journals) as total_journals,
                    SUM(uwr.as_manager) as as_manager,
                    SUM(uwr.as_implementation) as as_implementation,
                    SUM(uwr.as_developer) as as_developer,
                    SUM(uwr.as_tester) as as_tester,
                    SUM(uwr.resolved_issues) as resolved_issues,
                    CURRENT_DATE as report_date
                FROM warehouse.dws_user_monthly_workload uwr
                WHERE uwr.user_id = %s AND uwr.year_month = %s
                GROUP BY uwr.user_id, uwr.user_name, uwr.year_month
                ON CONFLICT (user_id, year_month) DO UPDATE SET
                    total_projects = EXCLUDED.total_projects,
                    total_issues = EXCLUDED.total_issues,
                    total_journals = EXCLUDED.total_journals,
                    report_date = EXCLUDED.report_date
            """, (user_id, year_month))
            
            self.conn.commit()
            logger.info("User workload report generated")
            return 1
            
        except Exception as e:
            logger.error(f"Failed to generate user workload report: {e}")
            self.conn.rollback()
            raise
    
    def generate_all_reports(self, project_ids: list = None, year_month: str = None):
        """
        生成所有报表
        
        Args:
            project_ids: 项目 ID 列表（可选，默认所有订阅项目）
            year_month: 年月（可选，默认当前月）
        """
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')
        
        self.connect_db()
        
        try:
            # 获取项目列表
            if not project_ids:
                self.cursor.execute("SELECT DISTINCT project_id FROM warehouse.dws_project_daily_summary")
                project_ids = [row['project_id'] for row in self.cursor.fetchall()]
            
            logger.info(f"Generating reports for {len(project_ids)} projects")
            
            # 生成贡献者报表
            for project_id in project_ids:
                try:
                    self.generate_contributor_report(project_id, year_month)
                except Exception as e:
                    logger.error(f"Failed to generate contributor report for project {project_id}: {e}")
            
            # 生成项目健康度报表（最新日期）
            for project_id in project_ids:
                try:
                    self.cursor.execute("""
                        SELECT MAX(snapshot_date) as max_date 
                        FROM warehouse.dws_project_daily_summary 
                        WHERE project_id = %s
                    """, (project_id,))
                    result = self.cursor.fetchone()
                    if result and result['max_date']:
                        self.generate_project_health_report(project_id, result['max_date'])
                except Exception as e:
                    logger.error(f"Failed to generate health report for project {project_id}: {e}")
            
            logger.info("All reports generated successfully")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise
        finally:
            self.close_db()


def main():
    """主函数"""
    generator = ADSReportGenerator()
    generator.generate_all_reports()


if __name__ == "__main__":
    main()
