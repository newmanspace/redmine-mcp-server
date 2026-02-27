#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅推送服务

根据订阅配置，定时向用户发送项目状态报告
支持渠道：Email, DingTalk, Telegram
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

logger = logging.getLogger(__name__)


class SubscriptionPushService:
    """订阅推送服务"""

    def __init__(self):
        self.redmine_url = os.getenv('REDMINE_URL')
        self.api_key = os.getenv('REDMINE_API_KEY')
        
        # Email service
        from .email_service import EmailPushService
        self.email_service = EmailPushService()
        
        logger.info("SubscriptionPushService initialized")

    def redmine_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Call Redmine REST API"""
        url = f"{self.redmine_url}/{endpoint}"
        all_params = {'key': self.api_key, **(params or {})}
        resp = requests.get(url, params=all_params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """获取项目统计数据（向后兼容）"""
        from .report_generation_service import ReportGenerationService
        service = ReportGenerationService()
        return service.get_project_stats(project_id)

    def generate_report(
        self,
        project_id: int,
        report_type: str,
        report_level: str,
        include_trend: bool,
        trend_period: int
    ) -> Dict[str, Any]:
        """生成报告"""
        from .report_generation_service import ReportGenerationService
        service = ReportGenerationService()
        return service.generate_report(
            project_id, report_type, report_level, include_trend, trend_period
        )

    def send_email_report(
        self,
        to_email: str,
        project_name: str,
        stats: Dict[str, Any],
        level: str = "brief"
    ) -> bool:
        """发送电子邮件报告"""
        try:
            from .email_service import send_subscription_email
            result = send_subscription_email(to_email, project_name, stats, level)
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def push_subscription(self, subscription: Dict[str, Any]) -> bool:
        """推送单个订阅"""
        try:
            project_id = subscription.get('project_id')
            channel = subscription.get('channel')
            channel_id = subscription.get('channel_id')
            report_type = subscription.get('report_type', 'daily')
            report_level = subscription.get('report_level', 'brief')
            include_trend = subscription.get('include_trend', True)
            trend_period = subscription.get('trend_period_days', 7)
            
            # Generate report
            report = self.generate_report(
                project_id,
                report_type,
                report_level,
                include_trend,
                trend_period
            )
            
            if not report or 'error' in report:
                logger.error(f"Failed to generate report for project {project_id}")
                return False
            
            # Get project name
            try:
                project_data = self.redmine_get(f"projects/{project_id}.json")
                project_name = project_data['project']['name']
            except:
                project_name = f"Project {project_id}"
            
            # Push based on channel
            if channel == 'email':
                return self.send_email_report(
                    channel_id, project_name, report, report_level
                )
            
            elif channel == 'dingtalk':
                # TODO: Implement DingTalk push
                logger.info(f"DingTalk push to {channel_id} - not implemented yet")
                return True
            
            elif channel == 'telegram':
                # TODO: Implement Telegram push
                logger.info(f"Telegram push to {channel_id} - not implemented yet")
                return True
            
            else:
                logger.warning(f"Unknown channel: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to push subscription: {e}")
            return False

    def push_due_subscriptions(self, frequency: str = "daily") -> Dict[str, Any]:
        """推送所有到期的订阅"""
        try:
            from .subscription_service import get_subscription_manager
            manager = get_subscription_manager()
            
            # Get due subscriptions
            due_subs = manager.get_due_subscriptions(frequency)
            
            logger.info(f"Found {len(due_subs)} due subscriptions for {frequency}")
            
            results = {
                'total': len(due_subs),
                'success': 0,
                'failed': 0,
                'details': []
            }
            
            for sub in due_subs:
                sub_id = sub.get('subscription_id')
                success = self.push_subscription(sub)
                
                if success:
                    results['success'] += 1
                    logger.info(f"Pushed subscription {sub_id}")
                else:
                    results['failed'] += 1
                    logger.error(f"Failed to push subscription {sub_id}")
                
                results['details'].append({
                    'subscription_id': sub_id,
                    'success': success
                })
            
            # Close manager
            manager.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to push due subscriptions: {e}")
            return {
                'error': str(e),
                'total': 0,
                'success': 0,
                'failed': 0
            }

    def push_daily_subscriptions(self) -> Dict[str, Any]:
        """推送所有每日订阅"""
        return self.push_due_subscriptions("daily")

    def push_weekly_subscriptions(self) -> Dict[str, Any]:
        """推送所有每周订阅"""
        return self.push_due_subscriptions("weekly")

    def push_monthly_subscriptions(self) -> Dict[str, Any]:
        """推送所有每月订阅"""
        return self.push_due_subscriptions("monthly")


# Convenience functions

def push_daily_reports() -> Dict[str, Any]:
    """推送每日报告"""
    service = SubscriptionPushService()
    return service.push_daily_subscriptions()


def push_weekly_reports() -> Dict[str, Any]:
    """推送每周报告"""
    service = SubscriptionPushService()
    return service.push_weekly_subscriptions()


def push_monthly_reports() -> Dict[str, Any]:
    """推送每月报告"""
    service = SubscriptionPushService()
    return service.push_monthly_subscriptions()
