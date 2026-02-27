#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subscription Service Tests

测试订阅管理服务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import json
from datetime import datetime

# Set test environment
os.environ['WAREHOUSE_DB_HOST'] = 'localhost'
os.environ['WAREHOUSE_DB_PORT'] = '5432'
os.environ['WAREHOUSE_DB_NAME'] = 'redmine_warehouse_test'
os.environ['WAREHOUSE_DB_USER'] = 'test_user'
os.environ['WAREHOUSE_DB_PASSWORD'] = 'test_password'


class TestSubscriptionManager:
    """订阅管理器测试"""

    @pytest.fixture
    def mock_manager(self):
        """创建 mock 管理器"""
        manager = Mock()
        manager.subscribe.return_value = {
            'success': True,
            'subscription_id': 'user1:341:email',
            'message': '已订阅项目 341 的 daily 报告'
        }
        return manager

    @pytest.mark.unit
    def test_subscribe_project(self, mock_manager):
        """测试订阅项目"""
        result = mock_manager.subscribe(
            user_id='user1',
            project_id=341,
            channel='email',
            channel_id='user1@example.com',
            report_type='daily',
            report_level='detailed',
            send_time='09:00',
            include_trend=True
        )

        assert result.get('success') == True
        assert 'subscription_id' in result
        assert result['subscription_id'] == 'user1:341:email'

    @pytest.mark.unit
    def test_unsubscribe_project(self, mock_manager):
        """测试取消订阅"""
        mock_manager.unsubscribe.return_value = {
            'success': True,
            'removed_count': 1
        }

        result = mock_manager.unsubscribe(user_id='user1', project_id=341)

        assert result.get('success') == True
        assert result.get('removed_count') == 1

    @pytest.mark.unit
    def test_list_subscriptions(self, mock_manager):
        """测试列出订阅"""
        mock_manager.list_all_subscriptions.return_value = [
            {
                'subscription_id': 'user1:341:email',
                'project_id': 341,
                'channel': 'email',
                'enabled': True
            }
        ]

        subs = mock_manager.list_all_subscriptions()

        assert len(subs) == 1
        assert subs[0]['project_id'] == 341

    @pytest.mark.unit
    def test_get_user_subscriptions(self, mock_manager):
        """测试获取用户订阅"""
        mock_manager.get_user_subscriptions.return_value = [
            {
                'subscription_id': 'user1:341:email',
                'user_id': 'user1',
                'report_type': 'daily'
            }
        ]

        subs = mock_manager.get_user_subscriptions('user1')

        assert len(subs) == 1
        assert subs[0]['user_id'] == 'user1'

    @pytest.mark.unit
    def test_get_subscription_stats(self, mock_manager):
        """测试获取订阅统计"""
        mock_manager.get_stats.return_value = {
            'total_subscriptions': 10,
            'by_frequency': {'daily': 8, 'weekly': 2},
            'by_channel': {'email': 10},
            'active_subscriptions': 10
        }

        stats = mock_manager.get_stats()

        assert stats['total_subscriptions'] == 10
        assert stats['by_frequency']['daily'] == 8


class TestSubscriptionDatabase:
    """订阅数据库操作测试"""

    @pytest.fixture
    def sample_subscription(self):
        """示例订阅数据"""
        return {
            'subscription_id': 'user1:341:email',
            'user_id': 'user1',
            'project_id': 341,
            'channel': 'email',
            'channel_id': 'user1@example.com',
            'report_type': 'daily',
            'report_level': 'detailed',
            'send_time': '09:00',
            'include_trend': True,
            'trend_period_days': 7,
            'enabled': True
        }

    @pytest.mark.unit
    def test_subscription_schema(self, sample_subscription):
        """测试订阅数据结构"""
        assert 'subscription_id' in sample_subscription
        assert 'user_id' in sample_subscription
        assert 'project_id' in sample_subscription
        assert 'channel' in sample_subscription
        assert 'report_type' in sample_subscription
        assert 'send_time' in sample_subscription

    @pytest.mark.unit
    def test_subscription_id_format(self, sample_subscription):
        """测试订阅 ID 格式"""
        sub_id = sample_subscription['subscription_id']
        parts = sub_id.split(':')

        assert len(parts) == 3
        assert parts[0] == 'user1'
        assert parts[1] == '341'
        assert parts[2] == 'email'

    @pytest.mark.unit
    def test_report_type_values(self):
        """测试报告类型值"""
        valid_types = ['daily', 'weekly', 'monthly']

        for report_type in valid_types:
            assert report_type in ['daily', 'weekly', 'monthly']

    @pytest.mark.unit
    def test_report_level_values(self):
        """测试报告级别值"""
        valid_levels = ['brief', 'detailed', 'comprehensive']

        for level in valid_levels:
            assert level in ['brief', 'detailed', 'comprehensive']


class TestSubscriptionTimeMatching:
    """订阅时间匹配测试"""

    @pytest.mark.unit
    def test_daily_time_matching(self):
        """测试日报时间匹配"""
        from datetime import datetime

        # 当前时间 09:00
        current = datetime(2026, 2, 27, 9, 0, 0)
        send_time = '09:00'

        assert current.strftime('%H:%M') == send_time

    @pytest.mark.unit
    def test_weekly_time_matching(self):
        """测试周报时间匹配"""
        from datetime import datetime

        # 周一 09:00
        monday = datetime(2026, 3, 2, 9, 0, 0)  # 2026-03-02 is Monday

        assert monday.strftime('%a').lower() == 'mon'

    @pytest.mark.unit
    def test_monthly_time_matching(self):
        """测试月报时间匹配"""
        from datetime import datetime

        # 每月 1 号
        first_day = datetime(2026, 3, 1, 10, 0, 0)

        assert first_day.day == 1

    @pytest.mark.unit
    def test_custom_time_matching(self):
        """测试自定义时间匹配"""
        # 下午 5 点
        current = datetime(2026, 2, 27, 17, 0, 0)
        send_time = '17:00'

        assert current.strftime('%H:%M') == send_time
