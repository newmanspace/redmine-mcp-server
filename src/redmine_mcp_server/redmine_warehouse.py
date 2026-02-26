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
    
    # ========== 写操作（仅 Scheduler 调用）==========
    
    def upsert_issue(self, issue: Dict[str, Any], snapshot_date: date, 
                     is_new: bool = False, is_closed: bool = False, 
                     is_updated: bool = False):
        """插入或更新单个 Issue 快照"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO warehouse.issue_daily_snapshot (
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
                    1 if is_new else 0,
                    1 if is_closed else 0,
                    1 if is_updated else 0
                ))
    
    def refresh_daily_summary(self, project_id: int, snapshot_date: date):
        """刷新项目每日汇总表"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT warehouse.refresh_daily_summary(%s, %s)",
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
                
                # 刷新汇总表
                self.refresh_daily_summary(project_id, snapshot_date)
    
    # ========== 读操作（仅 MCP Tools 调用）==========
    
    def get_issues_snapshot(self, project_id: int, snapshot_date: date) -> List[Dict]:
        """获取指定日期的 Issue 快照"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.issue_daily_snapshot
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, snapshot_date.isoformat()))
                
                return [dict(row) for row in cur.fetchall()]
    
    def get_project_daily_stats(self, project_id: int, snapshot_date: date) -> Dict[str, Any]:
        """获取项目每日统计（从汇总表）"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.project_daily_summary
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
                        'today_updated': summary['updated_issues'],
                        'by_status': {
                            '新建': summary['status_new'],
                            '进行中': summary['status_in_progress'],
                            '已解决': summary['status_resolved'],
                            '已关闭': summary['status_closed'],
                            '反馈': summary['status_feedback']
                        },
                        'by_priority': {
                            '立刻': summary['priority_immediate'],
                            '紧急': summary['priority_urgent'],
                            '高': summary['priority_high'],
                            '普通': summary['priority_normal'],
                            '低': summary['priority_low']
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
                    FROM warehouse.issue_daily_snapshot
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
                    FROM warehouse.issue_daily_snapshot
                    WHERE project_id = %s 
                      AND snapshot_date = %s
                      AND assigned_to_name IS NOT NULL
                    GROUP BY assigned_to_name
                    ORDER BY total DESC
                    LIMIT %s
                """, (project_id, snapshot_date.isoformat(), limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    def close(self):
        """关闭连接池"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")
