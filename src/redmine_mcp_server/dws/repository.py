# /docker/redmine-mcp-server/src/redmine_mcp_server/warehouse.py
"""
PostgreSQL 数据仓库 - 纯数据访问层
只提供读写接口，不包含业务逻辑
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DataWarehouse:
    """Redmine PostgreSQL 数据仓库 - 数据访问层"""
    
    def __init__(self):
        self.db_host = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
        self.db_port = os.getenv("WAREHOUSE_DB_PORT", "5432")
        self.db_name = os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse")
        self.db_user = os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse")
        self.db_password = os.getenv("WAREHOUSE_DB_PASSWORD")
        
        self.connection_pool = None
        self._init_pool()
    
    def _init_pool(self):
        """初始化数据库连接池"""
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 10,
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Connected to PostgreSQL warehouse at {self.db_host}:{self.db_port}")
        except Exception as e:
            logger.error(f"Failed to connect to warehouse database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """从连接池获取连接"""
        if not self.connection_pool:
            self._init_pool()
        
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)
    
    # ========== Write Operations (Scheduler only) ==========
    
    def upsert_issue(self, issue: Dict[str, Any], snapshot_date: date, 
                     is_new: bool = False, is_closed: bool = False, 
                     is_updated: bool = False):
        """插入或更新单个 Issue 快照"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO warehouse.dwd_issue_daily_snapshot (
                        issue_id, project_id, snapshot_date,
                        subject, status_id, status_name,
                        priority_id, priority_name,
                        assigned_to_id, assigned_to_name,
                        created_at, updated_at,
                        is_new, is_closed, is_updated
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (issue_id, snapshot_date) DO UPDATE SET
                        status_id = EXCLUDED.status_id,
                        status_name = EXCLUDED.status_name,
                        priority_id = EXCLUDED.priority_id,
                        priority_name = EXCLUDED.priority_name,
                        assigned_to_id = EXCLUDED.assigned_to_id,
                        assigned_to_name = EXCLUDED.assigned_to_name,
                        updated_at = EXCLUDED.updated_at,
                        is_updated = EXCLUDED.is_updated
                """, (
                    issue['id'], issue.get('project', {}).get('id'), snapshot_date,
                    issue.get('subject', ''),
                    issue.get('status', {}).get('id'),
                    issue.get('status', {}).get('name'),
                    issue.get('priority', {}).get('id'),
                    issue.get('priority', {}).get('name'),
                    issue.get('assigned_to', {}).get('id') if issue.get('assigned_to') else None,
                    issue.get('assigned_to', {}).get('name') if issue.get('assigned_to') else None,
                    issue.get('created_on', ''),
                    issue.get('updated_on', ''),
                    is_new,
                    is_closed,
                    is_updated
                ))
    
    def refresh_dws_project_daily_summary(self, project_id: int, snapshot_date: date):
        """刷新项目每日汇总表"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT warehouse.refresh_dws_project_daily_summary(%s, %s)",
                    (project_id, snapshot_date)
                )
    
    def upsert_issues_batch(self, project_id: int, issues: List[Dict[str, Any]], 
                            snapshot_date: date, previous_map: Dict[int, Dict]):
        """批量插入或更新 Issue 快照"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for issue in issues:
                    issue_id = issue['id']
                    prev = previous_map.get(issue_id, {})
                    
                    is_new = issue_id not in previous_map
                    is_closed = (
                        issue.get('status', {}).get('name') == '已关闭' and
                        prev.get('status_name') != '已关闭'
                    )
                    is_updated = (
                        issue.get('updated_on', '')[:10] == snapshot_date.isoformat()
                    )
                    
                    self.upsert_issue(issue, snapshot_date, is_new, is_closed, is_updated)
                
                # Refresh summary table
                self.refresh_dws_project_daily_summary(project_id, snapshot_date)
    
    # ========== Read Operations (MCP Tools only) ==========
    
    def get_issues_snapshot(self, project_id: int, snapshot_date: date) -> List[Dict]:
        """获取指定日期的 Issue 快照"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.dwd_issue_daily_snapshot
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, snapshot_date.isoformat()))
                
                return [dict(row) for row in cur.fetchall()]
    
    def get_project_daily_stats(self, project_id: int, snapshot_date: date) -> Dict[str, Any]:
        """获取项目每日统计（从汇总表）"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.dws_project_daily_summary
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, snapshot_date.isoformat()))
                
                summary = cur.fetchone()
                
                if summary:
                    return {
                        'project_id': project_id,
                        'date': snapshot_date.isoformat(),
                        'total': summary['total_issues'],
                        'today_new': summary['new_issues'],
                        'today_closed': summary['closed_issues'],
                        'today_updated': summary.get('updated_issues', 0),
                        'by_status': {
                            '新建': summary.get('status_new', 0),
                            '进行中': summary.get('status_in_progress', 0),
                            '已解决': summary.get('status_resolved', 0),
                            '已关闭': summary.get('status_closed', 0),
                            '反馈': summary.get('status_feedback', 0)
                        },
                        'by_priority': {
                            '立刻': summary.get('priority_immediate', 0),
                            '紧急': summary.get('priority_urgent', 0),
                            '高': summary.get('priority_high', 0),
                            '普通': summary.get('priority_normal', 0),
                            '低': summary.get('priority_low', 0)
                        },
                        'from_cache': True
                    }
                
                return {
                    'project_id': project_id,
                    'date': snapshot_date.isoformat(),
                    'total': 0,
                    'today_new': 0,
                    'today_closed': 0,
                    'today_updated': 0,
                    'by_status': {},
                    'by_priority': {},
                    'from_cache': False
                }
    
    def get_high_priority_issues(self, project_id: int, snapshot_date: date, 
                                  limit: int = 20) -> List[Dict]:
        """获取高优先级 Issue"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT issue_id, subject, priority_name, status_name,
                           assigned_to_name, created_at, due_date
                    FROM warehouse.dwd_issue_daily_snapshot
                    WHERE project_id = %s
                      AND snapshot_date = %s
                      AND priority_name IN ('立刻', '紧急', '高')
                    ORDER BY 
                        CASE priority_name 
                            WHEN '立刻' THEN 1 
                            WHEN '紧急' THEN 2 
                            WHEN '高' THEN 3 
                        END
                    LIMIT %s
                """, (project_id, snapshot_date.isoformat(), limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    def get_top_assignees(self, project_id: int, snapshot_date: date, 
                          limit: int = 10) -> List[Dict]:
        """获取人员任务量 TOP N"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        assigned_to_name,
                        COUNT(*) as total,
                        SUM(CASE WHEN status_name IN ('新建', '进行中', '测试中') THEN 1 ELSE 0 END) as in_progress,
                        SUM(CASE WHEN priority_name IN ('立刻', '紧急', '高') THEN 1 ELSE 0 END) as high_priority
                    FROM warehouse.dwd_issue_daily_snapshot
                    WHERE project_id = %s 
                      AND snapshot_date = %s
                      AND assigned_to_name IS NOT NULL
                    GROUP BY assigned_to_name
                    ORDER BY total DESC
                    LIMIT %s
                """, (project_id, snapshot_date.isoformat(), limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    # ========== Contributor Analysis Methods ==========
    
    def upsert_issue_contributors(self, issue_id: int, project_id: int, 
                                   contributors: List[Dict]):
        """插入或更新 Issue 贡献者"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for contrib in contributors:
                    cur.execute("""
                        INSERT INTO warehouse.dws_issue_contributors (
                            issue_id, project_id, user_id, user_name,
                            highest_role_id, highest_role_name, role_category,
                            journal_count, first_contribution, last_contribution,
                            status_change_count, note_count, assigned_change_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (issue_id, user_id) DO UPDATE SET
                            journal_count = EXCLUDED.journal_count,
                            last_contribution = EXCLUDED.last_contribution,
                            status_change_count = EXCLUDED.status_change_count,
                            note_count = EXCLUDED.note_count,
                            assigned_change_count = EXCLUDED.assigned_change_count
                    """, (
                        issue_id, project_id, contrib['user_id'], contrib.get('user_name', ''),
                        contrib.get('highest_role_id'), contrib.get('highest_role_name'),
                        contrib.get('role_category'), contrib.get('journal_count', 0),
                        contrib.get('first_contribution'), contrib.get('last_contribution'),
                        contrib.get('status_change_count', 0), contrib.get('note_count', 0),
                        contrib.get('assigned_change_count', 0)
                    ))
                
                # Refresh summary
                cur.execute("SELECT warehouse.refresh_dws_issue_contributor_summary(%s, %s)", 
                           (issue_id, project_id))
    
    def get_issue_contributors(self, issue_id: int) -> List[Dict]:
        """获取 Issue 贡献者列表"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        user_id, user_name, role_category, highest_role_name,
                        journal_count, first_contribution, last_contribution,
                        status_change_count, note_count
                    FROM warehouse.dws_issue_contributors
                    WHERE issue_id = %s
                    ORDER BY 
                        CASE role_category
                            WHEN 'manager' THEN 1
                            WHEN 'implementation' THEN 2
                            WHEN 'developer' THEN 3
                            WHEN 'tester' THEN 4
                            ELSE 5
                        END,
                        journal_count DESC
                """, (issue_id,))
                return [dict(row) for row in cur.fetchall()]
    
    def get_issue_contributor_summary(self, issue_id: int) -> Optional[Dict]:
        """获取 Issue 贡献者汇总"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.dws_issue_contributor_summary
                    WHERE issue_id = %s
                """, (issue_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    
    def upsert_user_project_roles(self, project_id: int, roles: List[Dict]):
        """批量插入用户项目角色"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for role in roles:
                    cur.execute("""
                        INSERT INTO warehouse.dwd_user_project_role (
                            project_id, user_id, highest_role_id, highest_role_name,
                            role_category, role_priority, all_role_ids, is_direct_member
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (project_id, user_id) DO UPDATE SET
                            highest_role_id = EXCLUDED.highest_role_id,
                            highest_role_name = EXCLUDED.highest_role_name,
                            role_category = EXCLUDED.role_category,
                            role_priority = EXCLUDED.role_priority
                    """, (
                        project_id, role['user_id'], role.get('highest_role_id'),
                        role.get('highest_role_name'), role.get('role_category'),
                        role.get('role_priority'), role.get('all_role_ids'),
                        role.get('is_direct_member', True)
                    ))
    
    def get_user_project_role(self, project_id: int, user_id: int) -> Optional[Dict]:
        """获取用户在项目中的角色"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.dwd_user_project_role
                    WHERE project_id = %s AND user_id = %s
                """, (project_id, user_id))
                row = cur.fetchone()
                return dict(row) if row else None
    
    def get_project_roles(self, project_id: int) -> List[Dict]:
        """获取项目所有用户角色"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.dwd_user_project_role
                    WHERE project_id = %s
                    ORDER BY role_priority ASC
                """, (project_id,))
                return [dict(row) for row in cur.fetchall()]
    
    def refresh_dws_project_role_distribution(self, project_id: int, snapshot_date: date):
        """刷新项目角色分布"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT warehouse.refresh_dws_project_role_distribution(%s, %s)",
                    (project_id, snapshot_date.isoformat())
                )
    
    def get_project_role_distribution(self, project_id: int, snapshot_date: date) -> Optional[Dict]:
        """获取项目角色分布"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.dws_project_role_distribution
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, snapshot_date.isoformat()))
                row = cur.fetchone()
                return dict(row) if row else None
    
    def upsert_user_workload(self, user_id: int, user_name: str, year_month: str,
                             project_id: int, workload: Dict):
        """插入或更新用户工作量"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO warehouse.dws_user_monthly_workload (
                        user_id, user_name, year_month, project_id,
                        total_issues, total_journals,
                        as_manager, as_implementation, as_developer, as_tester,
                        resolved_issues, verified_issues
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, year_month, project_id) DO UPDATE SET
                        total_issues = EXCLUDED.total_issues,
                        total_journals = EXCLUDED.total_journals,
                        as_manager = EXCLUDED.as_manager,
                        as_implementation = EXCLUDED.as_implementation,
                        as_developer = EXCLUDED.as_developer,
                        as_tester = EXCLUDED.as_tester,
                        resolved_issues = EXCLUDED.resolved_issues,
                        verified_issues = EXCLUDED.verified_issues
                """, (
                    user_id, user_name, year_month, project_id,
                    workload.get('total_issues', 0), workload.get('total_journals', 0),
                    workload.get('as_manager', 0), workload.get('as_implementation', 0),
                    workload.get('as_developer', 0), workload.get('as_tester', 0),
                    workload.get('resolved_issues', 0), workload.get('verified_issues', 0)
                ))
    
    def get_user_workload(self, user_id: int, year_month: str, 
                          project_id: Optional[int] = None) -> List[Dict]:
        """获取用户工作量统计"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if project_id:
                    cur.execute("""
                        SELECT * FROM warehouse.dws_user_monthly_workload
                        WHERE user_id = %s AND year_month = %s AND project_id = %s
                    """, (user_id, year_month, project_id))
                else:
                    cur.execute("""
                        SELECT * FROM warehouse.dws_user_monthly_workload
                        WHERE user_id = %s AND year_month = %s
                        ORDER BY project_id
                    """, (user_id, year_month))
                return [dict(row) for row in cur.fetchall()]
    
    def close(self):
        """关闭连接池"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")
