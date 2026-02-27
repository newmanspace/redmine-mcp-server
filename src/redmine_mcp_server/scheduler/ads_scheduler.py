#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADS 报表定时生成任务

集成到 Redmine 调度器，支持：
- 每日生成项目健康度报表
- 每月生成贡献者和用户工作量报表
- 手动触发所有报表生成
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class ADSReportScheduler:
    """ADS 报表调度器"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        
    def get_connection(self):
        """获取数据库连接"""
        return self.db_pool.getconn()
    
    def release_connection(self, conn):
        """释放数据库连接"""
        self.db_pool.putconn(conn)
    
    def generate_daily_health_reports(self, project_ids: Optional[List[int]] = None) -> int:
        """
        生成每日项目健康度报表
        
        Args:
            project_ids: 项目 ID 列表（可选，默认所有项目）
        
        Returns:
            生成的报表数量
        """
        logger.info("Generating daily health reports...")
        
        conn = self.get_connection()
        count = 0
        
        try:
            with conn.cursor() as cur:
                # 获取项目列表
                if not project_ids:
                    cur.execute("SELECT DISTINCT project_id FROM warehouse.dws_project_daily_summary")
                    project_ids = [row['project_id'] for row in cur.fetchall()]
                
                logger.info(f"Generating health reports for {len(project_ids)} projects")
                
                for project_id in project_ids:
                    try:
                        # 获取最新统计数据
                        cur.execute("""
                            SELECT * FROM warehouse.dws_project_daily_summary
                            WHERE project_id = %s
                            ORDER BY snapshot_date DESC
                            LIMIT 1
                        """, (project_id,))
                        
                        summary = cur.fetchone()
                        
                        if not summary:
                            continue
                        
                        # 计算健康度
                        total = summary['total_issues']
                        closed = summary['status_closed']
                        
                        if total > 0:
                            health_score = min(100, (closed / total) * 100)
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
                        
                        # 获取项目名称
                        cur.execute("SELECT name FROM warehouse.ods_projects WHERE project_id = %s", (project_id,))
                        proj_result = cur.fetchone()
                        project_name = proj_result['name'] if proj_result else f"Project {project_id}"
                        
                        # 插入报表
                        cur.execute("""
                            INSERT INTO warehouse.ads_project_health_report (
                                project_id, project_name, snapshot_date,
                                total_issues, new_issues, closed_issues,
                                status_new, status_in_progress, status_resolved, status_closed,
                                priority_immediate, priority_urgent, priority_high,
                                health_score, risk_level, report_date
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                            ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
                                health_score = EXCLUDED.health_score,
                                risk_level = EXCLUDED.risk_level,
                                report_date = EXCLUDED.report_date
                        """, (
                            project_id,
                            project_name,
                            summary['snapshot_date'],
                            total,
                            summary['new_issues'],
                            summary['closed_issues'],
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
                        
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to generate health report for project {project_id}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Generated {count} health reports")
                
        except Exception as e:
            logger.error(f"Failed to generate daily health reports: {e}")
            conn.rollback()
        finally:
            self.release_connection(conn)
        
        return count
    
    def generate_monthly_contributor_reports(self, year_month: Optional[str] = None, 
                                            project_ids: Optional[List[int]] = None) -> int:
        """
        生成每月贡献者报表
        
        Args:
            year_month: 年月（YYYY-MM），默认上月
            project_ids: 项目 ID 列表
        
        Returns:
            生成的报表数量
        """
        if not year_month:
            # 默认生成上月报表
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            year_month = last_month.strftime('%Y-%m')
        
        logger.info(f"Generating monthly contributor reports for {year_month}...")
        
        conn = self.get_connection()
        count = 0
        
        try:
            with conn.cursor() as cur:
                # 获取项目列表
                if not project_ids:
                    cur.execute("SELECT DISTINCT project_id FROM warehouse.dws_issue_contributors")
                    project_ids = [row['project_id'] for row in cur.fetchall()]
                
                for project_id in project_ids:
                    try:
                        cur.execute("""
                            INSERT INTO warehouse.ads_contributor_report (
                                project_id, year_month, user_id, user_name,
                                role_category, total_issues, total_journals,
                                resolved_issues, report_date
                            )
                            SELECT 
                                ic.project_id, %s, ic.user_id, ic.user_name,
                                ic.role_category, COUNT(DISTINCT ic.issue_id),
                                SUM(ic.journal_count), SUM(ic.status_change_count),
                                CURRENT_DATE
                            FROM warehouse.dws_issue_contributors ic
                            WHERE ic.project_id = %s
                            GROUP BY ic.user_id, ic.user_name, ic.role_category
                            ON CONFLICT (project_id, year_month, user_id) DO UPDATE SET
                                total_issues = EXCLUDED.total_issues,
                                total_journals = EXCLUDED.total_journals,
                                resolved_issues = EXCLUDED.resolved_issues
                        """, (year_month, project_id))
                        
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to generate contributor report for project {project_id}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Generated contributor reports for {count} projects")
                
        except Exception as e:
            logger.error(f"Failed to generate monthly contributor reports: {e}")
            conn.rollback()
        finally:
            self.release_connection(conn)
        
        return count
    
    def generate_monthly_workload_reports(self, year_month: Optional[str] = None) -> int:
        """
        生成每月用户工作量报表
        
        Returns:
            生成的报表数量
        """
        if not year_month:
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            year_month = last_month.strftime('%Y-%m')
        
        logger.info(f"Generating monthly workload reports for {year_month}...")
        
        conn = self.get_connection()
        count = 0
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO warehouse.ads_user_workload_report (
                        user_id, user_name, year_month,
                        total_projects, total_issues, total_journals,
                        as_manager, as_implementation, as_developer, as_tester,
                        resolved_issues, report_date
                    )
                    SELECT 
                        uwr.user_id, uwr.user_name, uwr.year_month,
                        COUNT(DISTINCT uwr.project_id),
                        SUM(uwr.total_issues), SUM(uwr.total_journals),
                        SUM(uwr.as_manager), SUM(uwr.as_implementation),
                        SUM(uwr.as_developer), SUM(uwr.as_tester),
                        SUM(uwr.resolved_issues), CURRENT_DATE
                    FROM warehouse.dws_user_monthly_workload uwr
                    WHERE uwr.year_month = %s
                    GROUP BY uwr.user_id, uwr.user_name, uwr.year_month
                    ON CONFLICT (user_id, year_month) DO UPDATE SET
                        total_projects = EXCLUDED.total_projects,
                        total_issues = EXCLUDED.total_issues,
                        total_journals = EXCLUDED.total_journals
                """, (year_month,))
                
                count = cur.rowcount
                conn.commit()
                
                logger.info(f"Generated {count} workload reports")
                
        except Exception as e:
            logger.error(f"Failed to generate monthly workload reports: {e}")
            conn.rollback()
        finally:
            self.release_connection(conn)
        
        return count
    
    def generate_all_monthly_reports(self, year_month: Optional[str] = None) -> Dict[str, int]:
        """
        生成所有月度报表
        
        Returns:
            各类报表生成数量
        """
        logger.info("Generating all monthly reports...")
        
        results = {
            "contributor_reports": 0,
            "workload_reports": 0
        }
        
        results["contributor_reports"] = self.generate_monthly_contributor_reports(year_month)
        results["workload_reports"] = self.generate_monthly_workload_reports(year_month)
        
        logger.info(f"All monthly reports generated: {results}")
        return results


def init_ads_scheduler(db_pool):
    """初始化 ADS 报表调度器"""
    scheduler = ADSReportScheduler(db_pool)
    
    # 添加到主调度器
    from apscheduler.schedulers.background import BackgroundScheduler
    
    global ads_scheduler
    ads_scheduler = BackgroundScheduler()
    
    # 每日 9:00 生成项目健康度报表
    ads_scheduler.add_job(
        func=scheduler.generate_daily_health_reports,
        trigger="cron",
        hour=9,
        minute=0,
        id="ads_daily_health",
        replace_existing=True
    )
    
    # 每月 1 号生成上月贡献者和工作量报表
    ads_scheduler.add_job(
        func=scheduler.generate_monthly_contributor_reports,
        trigger="cron",
        day=1,
        hour=2,
        minute=0,
        id="ads_monthly_contributor",
        replace_existing=True
    )
    
    ads_scheduler.add_job(
        func=scheduler.generate_monthly_workload_reports,
        trigger="cron",
        day=1,
        hour=2,
        minute=30,
        id="ads_monthly_workload",
        replace_existing=True
    )
    
    ads_scheduler.start()
    logger.info("ADS report scheduler initialized")
    
    return scheduler


def shutdown_ads_scheduler():
    """关闭 ADS 报表调度器"""
    global ads_scheduler
    if ads_scheduler:
        ads_scheduler.shutdown()
        logger.info("ADS report scheduler shutdown")
