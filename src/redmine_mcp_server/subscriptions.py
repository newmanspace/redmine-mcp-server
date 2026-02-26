# /docker/redmine-mcp-server/src/redmine_mcp_server/subscriptions.py
"""
项目订阅管理模块
支持用户订阅项目，接收定期报告（简要/详细）
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal
from pathlib import Path

logger = logging.getLogger(__name__)

# Subscription config storage path
SUBSCRIPTIONS_FILE = os.getenv(
    "SUBSCRIPTIONS_FILE", 
    "./data/subscriptions.json"
)

# Subscription frequency options
SUBSCRIPTION_FREQUENCIES = Literal["realtime", "daily", "weekly", "monthly"]

# Subscription content level
SUBSCRIPTION_LEVELS = Literal["brief", "detailed"]

# Push channel
PUSH_CHANNELS = Literal["dingtalk", "telegram", "email"]


class SubscriptionManager:
    """订阅管理器"""
    
    def __init__(self):
        self.subscriptions_file = Path(SUBSCRIPTIONS_FILE)
        self.subscriptions: Dict[str, Any] = {}
        self._load_subscriptions()
    
    def _load_subscriptions(self):
        """从文件加载订阅配置"""
        try:
            if self.subscriptions_file.exists():
                with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                    self.subscriptions = json.load(f)
                logger.info(f"Loaded {len(self.subscriptions)} subscriptions")
            else:
                self.subscriptions = {}
                self._save_subscriptions()
        except Exception as e:
            logger.error(f"Failed to load subscriptions: {e}")
            self.subscriptions = {}
    
    def _save_subscriptions(self):
        """保存订阅配置到文件"""
        try:
            self.subscriptions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.subscriptions)} subscriptions")
        except Exception as e:
            logger.error(f"Failed to save subscriptions: {e}")
    
    def subscribe(
        self,
        user_id: str,
        project_id: int,
        channel: str,
        channel_id: str,
        frequency: str = "daily",
        level: str = "brief",
        push_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        订阅项目
        
        Args:
            user_id: 用户 ID
            project_id: 项目 ID
            channel: 推送渠道 (dingtalk/telegram)
            channel_id: 渠道 ID (钉钉用户 ID/Telegram chat ID)
            frequency: 推送频率 (realtime/daily/weekly/monthly)
            level: 报告级别 (brief/detailed)
            push_time: 推送时间 (daily 用 "09:00", weekly 用 "Mon 09:00")
        
        Returns:
            订阅结果
        """
        subscription_id = f"{user_id}:{project_id}:{channel}"
        
        subscription = {
            "user_id": user_id,
            "project_id": project_id,
            "channel": channel,
            "channel_id": channel_id,
            "frequency": frequency,
            "level": level,
            "push_time": push_time,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "enabled": True
        }
        
        self.subscriptions[subscription_id] = subscription
        self._save_subscriptions()
        
        logger.info(f"User {user_id} subscribed to project {project_id} via {channel}")
        
        return {
            "success": True,
            "subscription_id": subscription_id,
            "message": f"已订阅项目 {project_id}",
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
        
        for sub_id in list(self.subscriptions.keys()):
            sub = self.subscriptions[sub_id]
            if sub["user_id"] != user_id:
                continue
            
            if project_id is not None and sub["project_id"] != project_id:
                continue
            
            if channel is not None and sub["channel"] != channel:
                continue
            
            removed.append(sub_id)
            del self.subscriptions[sub_id]
        
        self._save_subscriptions()
        
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
        return [
            sub for sub in self.subscriptions.values()
            if sub["user_id"] == user_id and sub.get("enabled", True)
        ]
    
    def get_project_subscribers(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目的所有订阅者"""
        return [
            sub for sub in self.subscriptions.values()
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
        
        for sub in self.subscriptions.values():
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
        if subscription_id not in self.subscriptions:
            return {
                "success": False,
                "message": "订阅不存在"
            }
        
        sub = self.subscriptions[subscription_id]
        
        # Update allowed fields
        allowed_fields = ["frequency", "level", "push_time", "enabled"]
        for key, value in kwargs.items():
            if key in allowed_fields:
                sub[key] = value
        
        sub["updated_at"] = datetime.now().isoformat()
        self._save_subscriptions()
        
        return {
            "success": True,
            "message": "订阅已更新",
            "subscription": sub
        }
    
    def list_all_subscriptions(self) -> List[Dict[str, Any]]:
        """列出所有订阅"""
        return list(self.subscriptions.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取订阅统计"""
        subs = list(self.subscriptions.values())
        
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
