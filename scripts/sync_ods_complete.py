#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ODS 层完整数据同步脚本

同步 Redmine 完整数据到 ODS 层：
- Projects (项目)
- Users (用户)
- Issues (Issue)
- Journals (变更日志)

支持增量同步和全量同步
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
REDMINE_URL = os.getenv("REDMINE_URL", "http://redmine.fa-software.com")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

WAREHOUSE_DB_HOST = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
WAREHOUSE_DB_PORT = os.getenv("WAREHOUSE_DB_PORT", "5432")
WAREHOUSE_DB_NAME = os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse")
WAREHOUSE_DB_USER = os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse")
WAREHOUSE_DB_PASSWORD = os.getenv("WAREHOUSE_DB_PASSWORD")

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch


class ODSSync:
    """ODS 层数据同步器"""
    
    def __init__(self):
        self.base_url = REDMINE_URL
        self.api_key = REDMINE_API_KEY
        self.headers = {"X-Redmine-API-Key": self.api_key}
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
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def fetch_all(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """分页获取所有数据"""
        all_data = []
        offset = 0
        limit = 100
        
        while True:
            try:
                req_params = {"offset": offset, "limit": limit}
                if params:
                    req_params.update(params)
                
                url = f"{self.base_url}/{endpoint}"
                logger.debug(f"Fetching {url} with params {req_params}")
                
                resp = requests.get(
                    url,
                    headers=self.headers,
                    params=req_params,
                    timeout=60
                )
                
                if resp.status_code != 200:
                    logger.error(f"API error: {resp.status_code} - {resp.text[:200]}")
                    break
                
                resp.raise_for_status()
                data = resp.json()
                logger.debug(f"Response keys: {list(data.keys())}")
                
                # 提取数据列表（处理复数形式）
                # projects.json -> projects, issues.json -> issues
                key = endpoint
                if key.endswith('.json'):
                    key = key[:-5]  # 移除 .json
                
                items = data.get(key, [])
                
                if not items and len(data) > 0:
                    # 尝试第一个 key
                    first_key = list(data.keys())[0]
                    items = data.get(first_key, [])
                
                all_data.extend(items)
                
                logger.info(f"Fetched {len(items)} items from {endpoint} (offset={offset})")
                
                if len(items) < limit:
                    break
                offset += limit
                
            except Exception as e:
                logger.error(f"Failed to fetch {endpoint}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        return all_data
    
    def sync_projects(self, full_sync: bool = False) -> int:
        """
        同步项目数据
        
        Args:
            full_sync: 是否全量同步
        """
        logger.info(f"Syncing projects (full_sync={full_sync})...")
        
        projects = self.fetch_all("projects.json", {"include": "trackers,issue_categories,enabled_modules"})
        count = 0
        
        for proj in projects:
            try:
                self.cursor.execute("""
                    INSERT INTO warehouse.ods_projects (
                        project_id, name, identifier, description, status,
                        created_on, updated_on, parent_project_id, sync_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (project_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        identifier = EXCLUDED.identifier,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        updated_on = EXCLUDED.updated_on,
                        parent_project_id = EXCLUDED.parent_project_id,
                        sync_time = EXCLUDED.sync_time
                """, (
                    proj['id'],
                    proj['name'],
                    proj['identifier'],
                    proj.get('description', ''),
                    proj.get('status', 1),
                    proj.get('created_on'),
                    proj.get('updated_on'),
                    proj.get('parent', {}).get('id') if proj.get('parent') else None,
                    datetime.now()
                ))
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync project {proj.get('id')}: {e}")
        
        self.conn.commit()
        logger.info(f"Synced {count} projects")
        return count
    
    def sync_users(self, full_sync: bool = False) -> int:
        """同步用户数据"""
        logger.info(f"Syncing users (full_sync={full_sync})...")
        
        users = self.fetch_all("users.json")
        count = 0
        
        for user in users:
            try:
                self.cursor.execute("""
                    INSERT INTO warehouse.ods_users (
                        user_id, login, firstname, lastname, mail,
                        status, created_on, last_login_on, sync_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        login = EXCLUDED.login,
                        firstname = EXCLUDED.firstname,
                        lastname = EXCLUDED.lastname,
                        mail = EXCLUDED.mail,
                        status = EXCLUDED.status,
                        last_login_on = EXCLUDED.last_login_on,
                        sync_time = EXCLUDED.sync_time
                """, (
                    user['id'],
                    user['login'],
                    user.get('firstname', ''),
                    user.get('lastname', ''),
                    user.get('mail', ''),
                    user.get('status', 1),
                    user.get('created_on'),
                    user.get('last_login_on'),
                    datetime.now()
                ))
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync user {user.get('id')}: {e}")
        
        self.conn.commit()
        logger.info(f"Synced {count} users")
        return count
    
    def sync_issues_batch(self, project_id: Optional[int] = None, updated_after: Optional[datetime] = None) -> int:
        """
        同步 Issues（支持所有项目或指定项目，包含已关闭的 Issue）
        
        Args:
            project_id: 项目 ID（可选，None 表示同步所有项目）
            updated_after: 只同步此时间后更新的 Issue
        """
        params = {"status_id": "*"}  # 获取所有状态的 Issue（包括已关闭的）
        if project_id is not None:
            params["project_id"] = project_id
        if updated_after:
            params["updated_on"] = f">={updated_after.isoformat()}"
        
        issues = self.fetch_all("issues.json", params)
        count = 0
        
        for issue in issues:
            try:
                self.cursor.execute("""
                    INSERT INTO warehouse.ods_issues (
                        issue_id, project_id, tracker_id, status_id, priority_id,
                        author_id, assigned_to_id, parent_issue_id, subject,
                        description, start_date, due_date, done_ratio,
                        estimated_hours, spent_hours, created_on, updated_on,
                        closed_on, sync_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (issue_id) DO UPDATE SET
                        project_id = EXCLUDED.project_id,
                        status_id = EXCLUDED.status_id,
                        priority_id = EXCLUDED.priority_id,
                        assigned_to_id = EXCLUDED.assigned_to_id,
                        subject = EXCLUDED.subject,
                        done_ratio = EXCLUDED.done_ratio,
                        updated_on = EXCLUDED.updated_on,
                        closed_on = EXCLUDED.closed_on,
                        sync_time = EXCLUDED.sync_time
                """, (
                    issue['id'],
                    issue['project']['id'],
                    issue['tracker']['id'],
                    issue['status']['id'],
                    issue.get('priority', {}).get('id'),
                    issue['author']['id'],
                    issue.get('assigned_to', {}).get('id') if issue.get('assigned_to') else None,
                    issue.get('parent', {}).get('id') if issue.get('parent') else None,
                    issue.get('subject', ''),
                    issue.get('description', ''),
                    issue.get('start_date'),
                    issue.get('due_date'),
                    issue.get('done_ratio', 0),
                    issue.get('estimated_hours'),
                    issue.get('spent_hours'),
                    issue['created_on'],
                    issue['updated_on'],
                    issue.get('closed_on'),
                    datetime.now()
                ))
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync issue {issue.get('id')}: {e}")
        
        self.conn.commit()
        return count
    
    def sync_all_issues(self, project_ids: List[int] = None, updated_after: Optional[datetime] = None) -> int:
        """
        同步所有项目 Issues
        
        Args:
            project_ids: 项目 ID 列表（可选，默认所有项目）
            updated_after: 增量同步时间点
        """
        if not project_ids:
            # 获取所有项目
            self.cursor.execute("SELECT project_id FROM warehouse.ods_projects")
            project_ids = [row['project_id'] for row in self.cursor.fetchall()]
        
        total_count = 0
        for pid in project_ids:
            try:
                count = self.sync_issues_batch(pid, updated_after)
                total_count += count
                logger.info(f"Project {pid}: synced {count} issues")
            except Exception as e:
                logger.error(f"Failed to sync project {pid}: {e}")
        
        return total_count
    
    def sync_journals_batch(self, issue_ids: List[int]) -> int:
        """
        同步 Issues 的 Journals
        
        Args:
            issue_ids: Issue ID 列表
        """
        total_count = 0
        
        for issue_id in issue_ids:
            try:
                # 获取 Issue 详情（包含 journals）
                resp = requests.get(
                    f"{self.base_url}/issues/{issue_id}.json",
                    headers=self.headers,
                    params={"include": "journals"},
                    timeout=30
                )
                
                if resp.status_code != 200:
                    continue
                
                issue_data = resp.json().get('issue', {})
                journals = issue_data.get('journals', [])
                
                for journal in journals:
                    # 插入 journal
                    self.cursor.execute("""
                        INSERT INTO warehouse.ods_journals (
                            journal_id, issue_id, user_id, notes, created_on, sync_time
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (journal_id) DO NOTHING
                    """, (
                        journal['id'],
                        issue_id,
                        journal['user']['id'],
                        journal.get('notes', ''),
                        journal['created_on'],
                        datetime.now()
                    ))
                    
                    # 插入 journal details
                    for detail in journal.get('details', []):
                        self.cursor.execute("""
                            INSERT INTO warehouse.ods_journal_details (
                                journal_id, property, name, old_value, new_value, sync_time
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            journal['id'],
                            detail.get('property', 'attr'),
                            detail.get('name', ''),
                            detail.get('old_value'),
                            detail.get('new_value'),
                            datetime.now()
                        ))
                    
                    total_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to sync journals for issue {issue_id}: {e}")
        
        self.conn.commit()
        return total_count
    
    def sync_recent_journals(self, since: datetime) -> int:
        """同步最近更新的 journals"""
        logger.info(f"Syncing journals since {since}...")
        
        # 获取最近更新的 issues
        self.cursor.execute("""
            SELECT issue_id FROM warehouse.ods_issues
            WHERE updated_on > %s
        """, (since,))
        
        issue_ids = [row['issue_id'] for row in self.cursor.fetchall()]
        
        if not issue_ids:
            logger.info("No recent issues to sync journals")
            return 0
        
        # 分批同步（每批 100 个）
        total = 0
        batch_size = 100
        
        for i in range(0, len(issue_ids), batch_size):
            batch = issue_ids[i:i+batch_size]
            count = self.sync_journals_batch(batch)
            total += count
            logger.info(f"Synced {count} journals (batch {i//batch_size + 1})")
        
        return total
    
    def sync_project_memberships(self, full_sync: bool = False) -> int:
        """
        同步项目成员数据（按项目获取）
        
        Args:
            full_sync: 是否全量同步
        """
        logger.info(f"Syncing project memberships (full_sync={full_sync})...")
        
        # 获取所有项目
        self.cursor.execute("SELECT project_id FROM warehouse.ods_projects")
        project_ids = [row['project_id'] for row in self.cursor.fetchall()]
        
        total_count = 0
        
        for project_id in project_ids:
            try:
                # 获取项目成员
                url = f"{self.base_url}/projects/{project_id}/memberships.json"
                all_memberships = []
                offset = 0
                limit = 100
                
                while True:
                    # Redmine memberships API 不支持 offset/limit，直接获取所有
                    resp = requests.get(
                        url,
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if resp.status_code != 200:
                        break
                    
                    data = resp.json()
                    memberships = data.get('memberships', [])
                    all_memberships.extend(memberships)
                    
                    if len(memberships) < limit:
                        break
                    offset += limit
                
                # 插入成员数据
                for membership in all_memberships:
                    try:
                        # 插入 membership
                        self.cursor.execute("""
                            INSERT INTO warehouse.ods_project_memberships (
                                membership_id, project_id, user_id, group_id,
                                created_on, sync_time
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (membership_id) DO UPDATE SET
                                project_id = EXCLUDED.project_id,
                                user_id = EXCLUDED.user_id,
                                group_id = EXCLUDED.group_id,
                                sync_time = EXCLUDED.sync_time
                        """, (
                            membership['id'],
                            membership['project']['id'],
                            membership.get('user', {}).get('id'),
                            membership.get('group', {}).get('id'),
                            membership.get('created_on'),
                            datetime.now()
                        ))
                        
                        # 插入 roles
                        roles = membership.get('roles', [])
                        for role in roles:
                            self.cursor.execute("""
                                INSERT INTO warehouse.ods_project_member_roles (
                                    membership_id, role_id, sync_time
                                ) VALUES (%s, %s, %s)
                                ON CONFLICT (membership_id, role_id) DO NOTHING
                            """, (
                                membership['id'],
                                role['id'],
                                datetime.now()
                            ))
                        
                        total_count += 1
                        
                    except Exception as e:
                        logger.debug(f"Failed to sync membership {membership.get('id')}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Failed to sync memberships for project {project_id}: {e}")
        
        self.conn.commit()
        logger.info(f"Synced {total_count} project memberships")
        return total_count
    
    def full_sync(self):
        """执行全量同步"""
        logger.info("Starting FULL sync...")
        
        self.connect_db()
        
        try:
            # 1. 同步基础数据
            self.sync_projects(full_sync=True)
            self.sync_users(full_sync=True)
            
            # 2. 同步项目成员和角色
            self.sync_project_memberships(full_sync=True)
            
            # 3. 同步所有 issues
            self.sync_all_issues()
            
            # 4. 同步所有 journals（最近更新的 issues）
            since = datetime.now() - timedelta(days=30)
            self.sync_recent_journals(since)
            
            logger.info("FULL sync completed successfully")
            
        except Exception as e:
            logger.error(f"FULL sync failed: {e}")
            raise
        finally:
            self.close_db()
    
    def incremental_sync(self):
        """执行增量同步"""
        logger.info("Starting INCREMENTAL sync...")
        
        self.connect_db()
        
        try:
            # 获取上次同步时间
            self.cursor.execute("""
                SELECT MAX(sync_time) as last_sync FROM warehouse.ods_issues
            """)
            result = self.cursor.fetchone()
            last_sync = result['last_sync'] if result and result['last_sync'] else datetime.now() - timedelta(days=1)
            
            logger.info(f"Last sync: {last_sync}")
            
            # 同步最近更新的 issues
            self.sync_all_issues(updated_after=last_sync)
            
            # 同步 journals
            self.sync_recent_journals(last_sync)
            
            logger.info("INCREMENTAL sync completed successfully")
            
        except Exception as e:
            logger.error(f"INCREMENTAL sync failed: {e}")
            raise
        finally:
            self.close_db()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ODS 层数据同步')
    parser.add_argument('--full', action='store_true', help='全量同步')
    parser.add_argument('--incremental', action='store_true', help='增量同步（默认）')
    args = parser.parse_args()
    
    syncer = ODSSync()
    
    if args.full:
        syncer.full_sync()
    else:
        syncer.incremental_sync()


if __name__ == "__main__":
    main()
