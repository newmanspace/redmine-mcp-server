#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ODS 层基础数据同步脚本

同步 Redmine 基础数据：
- Roles (角色)
- Trackers (Issue 类型)
- Issue Statuses (Issue 状态)

更新频率：一次性或每周
"""

import os
import sys
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redmine 配置
REDMINE_URL = os.getenv("REDMINE_URL", "http://redmine.fa-software.com")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

# 数据库配置
WAREHOUSE_DB_HOST = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
WAREHOUSE_DB_PORT = os.getenv("WAREHOUSE_DB_PORT", "5432")
WAREHOUSE_DB_NAME = os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse")
WAREHOUSE_DB_USER = os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse")
WAREHOUSE_DB_PASSWORD = os.getenv("WAREHOUSE_DB_PASSWORD")

import psycopg2
from psycopg2.extras import RealDictCursor


class ODSBaseSync:
    """ODS 层基础数据同步器"""
    
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
            logger.error(f"Failed to connect database: {e}")
            raise
    
    def close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def fetch_redmine_data(self, endpoint: str) -> List[Dict]:
        """从 Redmine API 获取数据"""
        url = f"{self.base_url}/{endpoint}"
        all_data = []
        offset = 0
        limit = 100
        
        while True:
            try:
                resp = requests.get(
                    url,
                    headers=self.headers,
                    params={"offset": offset, "limit": limit},
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get(endpoint.rstrip('s'), [])  # roles -> role, trackers -> tracker
                all_data.extend(items)
                
                if len(items) < limit:
                    break
                offset += limit
                
            except Exception as e:
                logger.error(f"Failed to fetch {endpoint}: {e}")
                break
        
        return all_data
    
    def sync_roles(self) -> int:
        """同步角色数据"""
        logger.info("Syncing roles...")
        
        roles = self.fetch_redmine_data("roles.json")
        count = 0
        
        for role in roles:
            try:
                self.cursor.execute("""
                    INSERT INTO warehouse.ods_roles (
                        role_id, name, is_builtin, permissions, sync_time
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (role_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_builtin = EXCLUDED.is_builtin,
                        permissions = EXCLUDED.permissions,
                        sync_time = EXCLUDED.sync_time
                """, (
                    role['id'],
                    role['name'],
                    role.get('builtin', 0),
                    None,  # permissions 需要额外 API 调用
                    datetime.now()
                ))
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync role {role.get('id')}: {e}")
        
        self.conn.commit()
        logger.info(f"Synced {count} roles")
        return count
    
    def sync_trackers(self) -> int:
        """同步 Tracker 数据"""
        logger.info("Syncing trackers...")
        
        trackers = self.fetch_redmine_data("trackers.json")
        count = 0
        
        for tracker in trackers:
            try:
                self.cursor.execute("""
                    INSERT INTO warehouse.ods_trackers (
                        tracker_id, name, description, is_in_chlog, 
                        is_in_roadmap, position, sync_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tracker_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        is_in_chlog = EXCLUDED.is_in_chlog,
                        is_in_roadmap = EXCLUDED.is_in_roadmap,
                        position = EXCLUDED.position,
                        sync_time = EXCLUDED.sync_time
                """, (
                    tracker['id'],
                    tracker['name'],
                    tracker.get('description', ''),
                    tracker.get('is_in_chlog', 0),
                    tracker.get('is_in_roadmap', 0),
                    tracker.get('position', 0),
                    datetime.now()
                ))
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync tracker {tracker.get('id')}: {e}")
        
        self.conn.commit()
        logger.info(f"Synced {count} trackers")
        return count
    
    def sync_issue_statuses(self) -> int:
        """同步 Issue 状态数据"""
        logger.info("Syncing issue statuses...")
        
        statuses = self.fetch_redmine_data("issue_statuses.json")
        count = 0
        
        for status in statuses:
            try:
                self.cursor.execute("""
                    INSERT INTO warehouse.ods_issue_statuses (
                        status_id, name, is_closed, is_default, 
                        position, sync_time
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (status_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_closed = EXCLUDED.is_closed,
                        is_default = EXCLUDED.is_default,
                        position = EXCLUDED.position,
                        sync_time = EXCLUDED.sync_time
                """, (
                    status['id'],
                    status['name'],
                    status.get('is_closed', 0),
                    status.get('is_default', 0),
                    status.get('position', 0),
                    datetime.now()
                ))
                count += 1
            except Exception as e:
                logger.error(f"Failed to sync status {status.get('id')}: {e}")
        
        self.conn.commit()
        logger.info(f"Synced {count} issue statuses")
        return count
    
    def sync_all(self):
        """同步所有基础数据"""
        logger.info("Starting ODS base data sync...")
        
        self.connect_db()
        
        try:
            roles_count = self.sync_roles()
            trackers_count = self.sync_trackers()
            statuses_count = self.sync_issue_statuses()
            
            logger.info(f"Sync completed: {roles_count} roles, "
                       f"{trackers_count} trackers, {statuses_count} statuses")
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise
        finally:
            self.close_db()


def main():
    """主函数"""
    syncer = ODSBaseSync()
    syncer.sync_all()


if __name__ == "__main__":
    main()
