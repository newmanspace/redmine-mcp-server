#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速同步基础数据脚本

同步：
- Roles (角色)
- Trackers (Issue 类型)
- Issue Statuses (Issue 状态)
"""

import os
import sys
import logging
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
REDMINE_URL = os.getenv("REDMINE_URL", "http://redmine.fa-software.com")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")
HEADERS = {"X-Redmine-API-Key": REDMINE_API_KEY}

import psycopg2
from psycopg2.extras import RealDictCursor

WAREHOUSE_DB_HOST = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
WAREHOUSE_DB_PORT = os.getenv("WAREHOUSE_DB_PORT", "5432")
WAREHOUSE_DB_NAME = os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse")
WAREHOUSE_DB_USER = os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse")
WAREHOUSE_DB_PASSWORD = os.getenv("WAREHOUSE_DB_PASSWORD")


def sync_roles():
    """同步角色数据"""
    logger.info("Syncing roles...")
    
    conn = psycopg2.connect(
        host=WAREHOUSE_DB_HOST, port=WAREHOUSE_DB_PORT,
        dbname=WAREHOUSE_DB_NAME, user=WAREHOUSE_DB_USER,
        password=WAREHOUSE_DB_PASSWORD, cursor_factory=RealDictCursor
    )
    cur = conn.cursor()
    
    try:
        resp = requests.get(f"{REDMINE_URL}/roles.json", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        roles = resp.json().get('roles', [])
        
        for role in roles:
            cur.execute("""
                INSERT INTO warehouse.ods_roles (role_id, name, is_builtin, sync_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (role_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    sync_time = EXCLUDED.sync_time
            """, (role['id'], role['name'], role.get('builtin', 0), datetime.now()))
        
        conn.commit()
        logger.info(f"Synced {len(roles)} roles")
        return len(roles)
        
    finally:
        cur.close()
        conn.close()


def sync_trackers():
    """同步 Tracker 数据"""
    logger.info("Syncing trackers...")
    
    conn = psycopg2.connect(
        host=WAREHOUSE_DB_HOST, port=WAREHOUSE_DB_PORT,
        dbname=WAREHOUSE_DB_NAME, user=WAREHOUSE_DB_USER,
        password=WAREHOUSE_DB_PASSWORD, cursor_factory=RealDictCursor
    )
    cur = conn.cursor()
    
    try:
        resp = requests.get(f"{REDMINE_URL}/trackers.json", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        trackers = resp.json().get('trackers', [])
        
        for tracker in trackers:
            cur.execute("""
                INSERT INTO warehouse.ods_trackers (tracker_id, name, position, sync_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tracker_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    sync_time = EXCLUDED.sync_time
            """, (tracker['id'], tracker['name'], tracker.get('position', 0), datetime.now()))
        
        conn.commit()
        logger.info(f"Synced {len(trackers)} trackers")
        return len(trackers)
        
    finally:
        cur.close()
        conn.close()


def sync_issue_statuses():
    """同步 Issue 状态数据"""
    logger.info("Syncing issue statuses...")
    
    conn = psycopg2.connect(
        host=WAREHOUSE_DB_HOST, port=WAREHOUSE_DB_PORT,
        dbname=WAREHOUSE_DB_NAME, user=WAREHOUSE_DB_USER,
        password=WAREHOUSE_DB_PASSWORD, cursor_factory=RealDictCursor
    )
    cur = conn.cursor()
    
    try:
        resp = requests.get(f"{REDMINE_URL}/issue_statuses.json", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        statuses = resp.json().get('issue_statuses', [])
        
        for status in statuses:
            cur.execute("""
                INSERT INTO warehouse.ods_issue_statuses (status_id, name, is_closed, position, sync_time)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (status_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    is_closed = EXCLUDED.is_closed,
                    sync_time = EXCLUDED.sync_time
            """, (status['id'], status['name'], 1 if status.get('is_closed', False) else 0, status.get('position', 0), datetime.now()))
        
        conn.commit()
        logger.info(f"Synced {len(statuses)} issue statuses")
        return len(statuses)
        
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    logger.info("Starting base data sync...")
    
    roles = sync_roles()
    trackers = sync_trackers()
    statuses = sync_issue_statuses()
    
    logger.info(f"Base data sync completed: {roles} roles, {trackers} trackers, {statuses} statuses")
