# /docker/redmine-mcp-server/src/redmine_mcp_server/dws/services/subscription_service.py
"""
项目订阅管理模块
支持用户订阅项目，接收定期报告（简要/详细）
使用 PostgreSQL 数据库存储订阅信息
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal
from pathlib import Path

logger = logging.getLogger(__name__)

# Subscription frequency options
SUBSCRIPTION_FREQUENCIES = Literal["realtime", "daily", "weekly", "monthly"]

# Subscription content level
SUBSCRIPTION_LEVELS = Literal["brief", "detailed"]

# Push channel
PUSH_CHANNELS = Literal["dingtalk", "telegram", "email"]

# Fallback JSON file path (for offline mode)
SUBSCRIPTIONS_FILE = os.getenv(
    "SUBSCRIPTIONS_FILE",
    "./data/subscriptions.json"
)


class SubscriptionManager:
    """订阅管理器 - 使用 PostgreSQL 数据库存储订阅信息"""

    def __init__(self):
        self.warehouse = None
        self.subscriptions_file = Path(SUBSCRIPTIONS_FILE)
        self._init_warehouse()

    def _init_warehouse(self):
        """初始化数据仓库连接"""
        try:
            from ..repository import DataWarehouse
            self.warehouse = DataWarehouse()
            logger.info("SubscriptionManager: Warehouse connection initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize warehouse connection: {e}")
            logger.warning("Falling back to JSON file storage")
            self.warehouse = None

    def _db_exists(self) -> bool:
        """检查数据库表是否存在"""
        if not self.warehouse:
            return False
        try:
            with self.warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'warehouse' 
                            AND table_name = 'ads_user_subscriptions'
                        )
                    """)
                    result = cur.fetchone()
                    return result['exists'] if result else False
        except Exception:
            return False

    def _load_subscriptions_from_db(self) -> Dict[str, Any]:
        """从数据库加载订阅配置"""
        if not self.warehouse or not self._db_exists():
            return {}

        try:
            with self.warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT subscription_id, user_id, project_id, channel,
                               channel_id, frequency, level, push_time,
                               enabled, created_at, updated_at
                        FROM warehouse.ads_user_subscriptions
                        ORDER BY created_at DESC
                    """)
                    rows = cur.fetchall()
                    subscriptions = {}
                    for row in rows:
                        sub_id = row['subscription_id']
                        subscriptions[sub_id] = {
                            'subscription_id': sub_id,
                            'user_id': row['user_id'],
                            'project_id': row['project_id'],
                            'channel': row['channel'],
                            'channel_id': row['channel_id'],
                            'frequency': row['frequency'],
                            'level': row['level'],
                            'push_time': row['push_time'],
                            'enabled': row['enabled'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                            'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                        }
                    logger.info(f"Loaded {len(subscriptions)} subscriptions from database")
                    return subscriptions
        except Exception as e:
            logger.error(f"Failed to load subscriptions from database: {e}")
            return {}

    def _save_subscription_to_db(self, subscription: Dict[str, Any]):
        """保存单个订阅到数据库"""
        if not self.warehouse or not self._db_exists():
            return

        try:
            with self.warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO warehouse.ads_user_subscriptions (
                            subscription_id, user_id, project_id, channel,
                            channel_id, frequency, level, push_time,
                            enabled, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (subscription_id) DO UPDATE SET
                            project_id = EXCLUDED.project_id,
                            channel_id = EXCLUDED.channel_id,
                            frequency = EXCLUDED.frequency,
                            level = EXCLUDED.level,
                            push_time = EXCLUDED.push_time,
                            enabled = EXCLUDED.enabled,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        subscription['subscription_id'],
                        subscription['user_id'],
                        subscription['project_id'],
                        subscription['channel'],
                        subscription['channel_id'],
                        subscription['frequency'],
                        subscription['level'],
                        subscription.get('push_time'),
                        subscription.get('enabled', True),
                        subscription.get('created_at'),
                        subscription['updated_at']
                    ))
        except Exception as e:
            logger.error(f"Failed to save subscription to database: {e}")
            raise

    def _delete_subscription_from_db(self, subscription_id: str):
        """从数据库删除订阅"""
        if not self.warehouse or not self._db_exists():
            return

        try:
            with self.warehouse.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM warehouse.ads_user_subscriptions
                        WHERE subscription_id = %s
                    """, (subscription_id,))
        except Exception as e:
            logger.error(f"Failed to delete subscription from database: {e}")

    def _load_subscriptions(self) -> Dict[str, Any]:
        """从数据库加载订阅配置"""
        return self._load_subscriptions_from_db()
    
    def subscribe(
        self,
        user_id: str,
        project_id: int,
        channel: str,
        channel_id: str,
        report_type: str = "daily",         # daily/weekly/monthly
        report_level: str = "brief",        # brief/detailed/comprehensive
        send_time: str = "09:00",           # 发送时间
        send_day_of_week: Optional[str] = None,  # Mon-Sun (周报用)
        send_day_of_month: Optional[int] = None, # 1-31 (月报用)
        include_trend: bool = True,
        trend_period_days: int = 7
    ) -> Dict[str, Any]:
        """
        订阅项目报告

        Args:
            user_id: 用户 ID
            project_id: 项目 ID
            channel: 推送渠道 (dingtalk/telegram/email)
            channel_id: 渠道 ID (钉钉用户 ID/Telegram chat ID/邮箱)
            report_type: 报告类型 (daily/weekly/monthly)
            report_level: 报告级别 (brief/detailed/comprehensive)
            send_time: 发送时间 (HH:MM 格式)
            send_day_of_week: 周报发送星期 (Mon/Tue/Wed/Thu/Fri/Sat/Sun)
            send_day_of_month: 月报发送日期 (1-31)
            include_trend: 是否包含趋势分析
            trend_period_days: 趋势分析周期 (天数)

        Returns:
            订阅结果
        """
        subscription_id = f"{user_id}:{project_id}:{channel}"
        now = datetime.now()

        subscription = {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "project_id": project_id,
            "channel": channel,
            "channel_id": channel_id,
            "report_type": report_type,
            "report_level": report_level,
            "send_time": send_time,
            "send_day_of_week": send_day_of_week,
            "send_day_of_month": send_day_of_month,
            "include_trend": include_trend,
            "trend_period_days": trend_period_days,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "enabled": True
        }

        # Save to database
        self._save_subscription_to_db(subscription)

        logger.info(f"User {user_id} subscribed to project {project_id} ({report_type} report)")

        return {
            "success": True,
            "subscription_id": subscription_id,
            "message": f"已订阅项目 {project_id} 的{report_type}报告",
            "subscription": subscription
        }

    def unsubscribe(
        self,
        user_id: str,
        project_id: Optional[int] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        取消订阅

        Args:
            user_id: 用户 ID
            project_id: 项目 ID (可选，不传则取消该项目所有订阅)
            channel: 渠道 (可选)

        Returns:
            取消结果
        """
        removed = []

        # Load from database
        subscriptions = self._load_subscriptions()

        for sub_id in list(subscriptions.keys()):
            sub = subscriptions[sub_id]
            if sub["user_id"] != user_id:
                continue

            if project_id is not None and sub["project_id"] != project_id:
                continue

            if channel is not None and sub["channel"] != channel:
                continue

            removed.append(sub_id)
            self._delete_subscription_from_db(sub_id)

        if removed:
            logger.info(f"User {user_id} unsubscribed from {len(removed)} subscriptions")
            return {
                "success": True,
                "removed_count": len(removed),
                "removed_subscriptions": removed,
                "message": f"已取消 {len(removed)} 个订阅"
            }
        else:
            return {
                "success": False,
                "message": "未找到匹配的订阅"
            }

    def get_user_subscriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有订阅"""
        subscriptions = self._load_subscriptions()
        return [
            sub for sub in subscriptions.values()
            if sub["user_id"] == user_id and sub.get("enabled", True)
        ]

    def get_project_subscribers(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目的所有订阅者"""
        subscriptions = self._load_subscriptions()
        return [
            sub for sub in subscriptions.values()
            if sub["project_id"] == project_id and sub.get("enabled", True)
        ]
    
    def get_due_subscriptions(
        self,
        frequency: str,
        current_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取当前应该推送的订阅

        Args:
            frequency: 频率类型 (daily/weekly/monthly)
            current_time: 当前时间

        Returns:
            应该推送的订阅列表
        """
        if current_time is None:
            current_time = datetime.now()

        due_subs = []
        subscriptions = self._load_subscriptions()

        for sub in subscriptions.values():
            if not sub.get("enabled", True):
                continue

            if sub["frequency"] != frequency:
                continue

            push_time = sub.get("push_time")
            if not push_time:
                # No time set, push by default
                due_subs.append(sub)
                continue

            # Parse push time
            if frequency == "daily":
                # Format: "09:00"
                try:
                    hour, minute = map(int, push_time.split(":"))
                    if current_time.hour == hour and current_time.minute >= minute:
                        due_subs.append(sub)
                except:
                    pass

            elif frequency == "weekly":
                # Format: "Mon 09:00"
                try:
                    day_str, time_str = push_time.split(" ", 1)
                    hour, minute = map(int, time_str.split(":"))

                    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    if days[current_time.weekday()] == day_str:
                        if current_time.hour == hour and current_time.minute >= minute:
                            due_subs.append(sub)
                except:
                    pass

        return due_subs

    def update_subscription(
        self,
        subscription_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """更新订阅配置"""
        subscriptions = self._load_subscriptions()
        
        if subscription_id not in subscriptions:
            return {
                "success": False,
                "message": "订阅不存在"
            }

        sub = subscriptions[subscription_id]

        # Update allowed fields
        allowed_fields = ["frequency", "level", "push_time", "enabled"]
        for key, value in kwargs.items():
            if key in allowed_fields:
                sub[key] = value

        sub["updated_at"] = datetime.now().isoformat()
        
        # Save to database
        self._save_subscription_to_db(sub)

        return {
            "success": True,
            "message": "订阅已更新",
            "subscription": sub
        }

    def list_all_subscriptions(self) -> List[Dict[str, Any]]:
        """列出所有订阅"""
        subscriptions = self._load_subscriptions()
        return list(subscriptions.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取订阅统计"""
        subscriptions = self._load_subscriptions()
        subs = list(subscriptions.values())

        by_frequency = {}
        by_channel = {}
        by_project = {}

        for sub in subs:
            freq = sub.get("frequency", "unknown")
            channel = sub.get("channel", "unknown")
            project = sub.get("project_id", "unknown")

            by_frequency[freq] = by_frequency.get(freq, 0) + 1
            by_channel[channel] = by_channel.get(channel, 0) + 1
            by_project[project] = by_project.get(project, 0) + 1

        return {
            "total_subscriptions": len(subs),
            "by_frequency": by_frequency,
            "by_channel": by_channel,
            "by_project": by_project,
            "active_subscriptions": sum(1 for s in subs if s.get("enabled", True))
        }

    def close(self):
        """Close warehouse connection"""
        if self.warehouse:
            self.warehouse.close()
            logger.info("SubscriptionManager: Warehouse connection closed")


# Global subscription manager instance
subscription_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """获取订阅管理器单例"""
    global subscription_manager
    if subscription_manager is None:
        subscription_manager = SubscriptionManager()
    return subscription_manager


def init_subscription_manager():
    """初始化订阅管理器"""
    global subscription_manager
    subscription_manager = SubscriptionManager()
    logger.info("Subscription manager initialized")
