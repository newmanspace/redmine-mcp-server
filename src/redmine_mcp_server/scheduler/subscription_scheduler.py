#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅定时调度器

根据订阅配置，在指定时间自动发送日报/周报/月报
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class SubscriptionScheduler:
    """订阅定时调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',  # 使用东八区时间
            job_defaults={
                'coalesce': True,      # 合并错过的执行
                'max_instances': 1,    # 每个任务最多 1 个实例
                'misfire_grace_time': 3600  # 允许错过 1 小时
            }
        )
        self._initialized = False
        logger.info("SubscriptionScheduler initialized")

    def start(self):
        """启动调度器"""
        if not self._initialized:
            self._initialize_jobs()
            self._initialized = True
        
        self.scheduler.start()
        logger.info("SubscriptionScheduler started")

    def shutdown(self, wait=True):
        """关闭调度器"""
        self.scheduler.shutdown(wait=wait)
        logger.info("SubscriptionScheduler shutdown")

    def _initialize_jobs(self):
        """初始化定时任务"""
        # 每日报告 - 每天早上 9:00 执行
        self.scheduler.add_job(
            func=self._send_daily_reports,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_subscription_reports',
            name='Send daily subscription reports',
            replace_existing=True
        )
        logger.info("Scheduled: Daily reports at 09:00")

        # 周报 - 每周一早上 9:00 执行
        self.scheduler.add_job(
            func=self._send_weekly_reports,
            trigger=CronTrigger(hour=9, minute=0, day_of_week='mon'),
            id='weekly_subscription_reports',
            name='Send weekly subscription reports',
            replace_existing=True
        )
        logger.info("Scheduled: Weekly reports on Monday 09:00")

        # 月报 - 每月 1 号早上 10:00 执行
        self.scheduler.add_job(
            func=self._send_monthly_reports,
            trigger=CronTrigger(hour=10, minute=0, day=1),
            id='monthly_subscription_reports',
            name='Send monthly subscription reports',
            replace_existing=True
        )
        logger.info("Scheduled: Monthly reports on 1st day 10:00")

        # 检查器 - 每分钟检查是否有需要发送的报告（处理自定义时间）
        self.scheduler.add_job(
            func=self._check_custom_time_subscriptions,
            trigger=IntervalTrigger(minutes=1),
            id='check_custom_subscriptions',
            name='Check custom time subscriptions',
            replace_existing=True
        )
        logger.info("Scheduled: Check custom subscriptions every minute")

    def _send_daily_reports(self):
        """发送每日报告"""
        try:
            logger.info("Sending daily subscription reports...")
            from .subscription_push_service import SubscriptionPushService
            
            service = SubscriptionPushService()
            result = service.push_due_subscriptions("daily")
            
            logger.info(f"Daily reports sent: {result}")
            
        except Exception as e:
            logger.error(f"Failed to send daily reports: {e}")

    def _send_weekly_reports(self):
        """发送每周报告"""
        try:
            logger.info("Sending weekly subscription reports...")
            from .subscription_push_service import SubscriptionPushService
            
            service = SubscriptionPushService()
            result = service.push_due_subscriptions("weekly")
            
            logger.info(f"Weekly reports sent: {result}")
            
        except Exception as e:
            logger.error(f"Failed to send weekly reports: {e}")

    def _send_monthly_reports(self):
        """发送每月报告"""
        try:
            logger.info("Sending monthly subscription reports...")
            from .subscription_push_service import SubscriptionPushService
            
            service = SubscriptionPushService()
            result = service.push_due_subscriptions("monthly")
            
            logger.info(f"Monthly reports sent: {result}")
            
        except Exception as e:
            logger.error(f"Failed to send monthly reports: {e}")

    def _check_custom_time_subscriptions(self):
        """检查自定义时间的订阅（处理非标准时间的订阅）"""
        try:
            from .subscription_service import get_subscription_manager
            
            manager = get_subscription_manager()
            all_subs = manager.list_all_subscriptions()
            
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_day_of_week = now.strftime("%a")  # Mon, Tue, etc.
            current_day_of_month = now.day
            
            for sub in all_subs:
                if not sub.get('enabled', True):
                    continue
                
                report_type = sub.get('report_type', 'daily')
                send_time = sub.get('send_time', '09:00')
                send_day_of_week = sub.get('send_day_of_week')
                send_day_of_month = sub.get('send_day_of_month')
                
                should_send = False
                
                # 检查时间是否匹配
                if send_time != current_time:
                    continue
                
                # 根据报告类型检查日期
                if report_type == 'daily':
                    should_send = True
                elif report_type == 'weekly':
                    # 检查星期是否匹配
                    if send_day_of_week:
                        should_send = (send_day_of_week[:3].lower() == current_day_of_week.lower())
                    else:
                        should_send = (current_day_of_week.lower() == 'mon')  # 默认周一
                elif report_type == 'monthly':
                    # 检查日期是否匹配
                    if send_day_of_month:
                        should_send = (current_day_of_month == send_day_of_month)
                    else:
                        should_send = (current_day_of_month == 1)  # 默认 1 号
                
                if should_send:
                    # 发送报告
                    self._send_single_subscription(sub)
            
            manager.close()
            
        except Exception as e:
            logger.error(f"Failed to check custom subscriptions: {e}")

    def _send_single_subscription(self, subscription: Dict[str, Any]):
        """发送单个订阅"""
        try:
            from .subscription_push_service import SubscriptionPushService
            
            service = SubscriptionPushService()
            success = service.push_subscription(subscription)
            
            sub_id = subscription.get('subscription_id')
            if success:
                logger.info(f"Sent subscription: {sub_id}")
            else:
                logger.error(f"Failed to send subscription: {sub_id}")
                
        except Exception as e:
            logger.error(f"Error sending subscription {subscription.get('subscription_id')}: {e}")

    def get_job_status(self) -> Dict[str, Any]:
        """获取调度任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'running': self.scheduler.running,
            'job_count': len(jobs),
            'jobs': jobs
        }


# Global scheduler instance
_scheduler: Optional[SubscriptionScheduler] = None


def init_subscription_scheduler() -> SubscriptionScheduler:
    """初始化订阅调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SubscriptionScheduler()
        _scheduler.start()
    return _scheduler


def get_subscription_scheduler() -> Optional[SubscriptionScheduler]:
    """获取订阅调度器实例"""
    return _scheduler


def shutdown_subscription_scheduler():
    """关闭订阅调度器"""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None


# Convenience functions for manual trigger

def send_daily_reports() -> Dict[str, Any]:
    """手动发送每日报告"""
    try:
        from .subscription_push_service import SubscriptionPushService
        service = SubscriptionPushService()
        return service.push_due_subscriptions("daily")
    except Exception as e:
        return {'error': str(e)}


def send_weekly_reports() -> Dict[str, Any]:
    """手动发送每周报告"""
    try:
        from .subscription_push_service import SubscriptionPushService
        service = SubscriptionPushService()
        return service.push_due_subscriptions("weekly")
    except Exception as e:
        return {'error': str(e)}


def send_monthly_reports() -> Dict[str, Any]:
    """手动发送每月报告"""
    try:
        from .subscription_push_service import SubscriptionPushService
        service = SubscriptionPushService()
        return service.push_due_subscriptions("monthly")
    except Exception as e:
        return {'error': str(e)}
