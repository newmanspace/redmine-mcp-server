#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将订阅数据从 JSON 文件迁移到 PostgreSQL 数据库

使用方法:
    python scripts/migrate_subscriptions_to_db.py

前提条件:
    1. 已执行 init-scripts/07-ads-user-subscriptions.sql 创建表
    2. 数据库连接配置正确 (WAREHOUSE_DB_HOST 等环境变量)
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_subscriptions_from_json(json_path: str) -> dict:
    """从 JSON 文件加载订阅数据"""
    if not os.path.exists(json_path):
        logger.warning(f"JSON file not found: {json_path}")
        return {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} subscriptions from {json_path}")
    return data


def migrate_to_database(subscriptions: dict) -> dict:
    """迁移订阅数据到数据库"""
    from redmine_mcp_server.dws.repository import DataWarehouse
    
    warehouse = None
    migrated = 0
    errors = 0
    
    try:
        warehouse = DataWarehouse()
        logger.info("Connected to warehouse database")
        
        with warehouse.get_connection() as conn:
            with conn.cursor() as cur:
                for sub_id, sub in subscriptions.items():
                    try:
                        # Parse timestamps
                        created_at = sub.get('created_at')
                        updated_at = sub.get('updated_at')
                        
                        if created_at:
                            try:
                                created_at = datetime.fromisoformat(created_at)
                            except:
                                created_at = datetime.now()
                        else:
                            created_at = datetime.now()
                        
                        if updated_at:
                            try:
                                updated_at = datetime.fromisoformat(updated_at)
                            except:
                                updated_at = datetime.now()
                        else:
                            updated_at = datetime.now()
                        
                        # Insert or update
                        cur.execute("""
                            INSERT INTO warehouse.ads_user_subscriptions (
                                subscription_id, user_id, project_id, channel,
                                channel_id, frequency, level, push_time,
                                enabled, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (subscription_id) DO UPDATE SET
                                user_id = EXCLUDED.user_id,
                                project_id = EXCLUDED.project_id,
                                channel = EXCLUDED.channel,
                                channel_id = EXCLUDED.channel_id,
                                frequency = EXCLUDED.frequency,
                                level = EXCLUDED.level,
                                push_time = EXCLUDED.push_time,
                                enabled = EXCLUDED.enabled,
                                updated_at = EXCLUDED.updated_at
                        """, (
                            sub_id,
                            sub.get('user_id'),
                            sub.get('project_id'),
                            sub.get('channel'),
                            sub.get('channel_id'),
                            sub.get('frequency'),
                            sub.get('level'),
                            sub.get('push_time'),
                            sub.get('enabled', True),
                            created_at,
                            updated_at
                        ))
                        
                        migrated += 1
                        logger.debug(f"Migrated: {sub_id}")
                        
                    except Exception as e:
                        errors += 1
                        logger.error(f"Failed to migrate {sub_id}: {e}")
        
        logger.info(f"Migration completed: {migrated} succeeded, {errors} failed")
        
        return {
            "success": True,
            "migrated": migrated,
            "errors": errors,
            "total": len(subscriptions)
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "migrated": migrated,
            "errors": errors
        }
    
    finally:
        if warehouse:
            warehouse.close()


def verify_migration(subscriptions: dict) -> dict:
    """验证迁移结果"""
    from redmine_mcp_server.dws.services.subscription_service import SubscriptionManager
    
    manager = None
    try:
        manager = SubscriptionManager()
        db_subscriptions = manager.list_all_subscriptions()
        
        json_count = len(subscriptions)
        db_count = len(db_subscriptions)
        
        # Check counts
        if json_count != db_count:
            logger.warning(f"Count mismatch: JSON={json_count}, DB={db_count}")
        
        # Check each subscription
        missing_in_db = []
        for sub_id in subscriptions.keys():
            found = any(s['subscription_id'] == sub_id for s in db_subscriptions)
            if not found:
                missing_in_db.append(sub_id)
        
        if missing_in_db:
            logger.warning(f"Missing in DB: {missing_in_db}")
        
        return {
            "json_count": json_count,
            "db_count": db_count,
            "match": json_count == db_count and len(missing_in_db) == 0,
            "missing_in_db": missing_in_db
        }
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    
    finally:
        if manager:
            manager.close()


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Starting subscription migration from JSON to PostgreSQL")
    logger.info("=" * 60)
    
    # Get JSON path
    json_path = os.getenv(
        "SUBSCRIPTIONS_FILE",
        "./data/subscriptions.json"
    )
    
    # Load from JSON
    logger.info(f"Loading subscriptions from {json_path}...")
    subscriptions = load_subscriptions_from_json(json_path)
    
    if not subscriptions:
        logger.warning("No subscriptions to migrate")
        return
    
    # Migrate to database
    logger.info("Migrating to database...")
    result = migrate_to_database(subscriptions)
    
    if result.get("success"):
        logger.info(f"✓ Migration successful: {result['migrated']}/{result['total']} migrated")
        
        # Verify
        logger.info("Verifying migration...")
        verify_result = verify_migration(subscriptions)
        
        if verify_result.get("match"):
            logger.info(f"✓ Verification passed: {verify_result['db_count']} subscriptions in DB")
        else:
            logger.warning(f"✗ Verification failed: {verify_result}")
    else:
        logger.error(f"✗ Migration failed: {result.get('error')}")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
