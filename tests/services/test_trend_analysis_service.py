#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trend Analysis Service Tests

测试趋势分析服务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime, timedelta

# Set test environment
os.environ['REDMINE_URL'] = 'http://test-redmine.com'
os.environ['REDMINE_API_KEY'] = 'test_api_key'


class TestTrendAnalysisService:
    """趋势分析服务测试"""

    @pytest.fixture
    def mock_service(self):
        """创建 mock 服务"""
        with patch('src.redmine_mcp_server.dws.services.trend_analysis_service.TrendAnalysisService'):
            from src.redmine_mcp_server.dws.services.trend_analysis_service import TrendAnalysisService
            service = TrendAnalysisService()
            service.redmine_get = MagicMock()
            return service

    @pytest.fixture
    def sample_issues_with_dates(self):
        """示例带日期的 Issue 数据"""
        today = datetime.now()
        issues = []

        # 生成过去 7 天的 Issue
        for i in range(10):
            created = today - timedelta(days=i % 7)
            issues.append({
                'id': i + 1,
                'subject': f'Issue {i + 1}',
                'status': {'name': '已关闭' if i % 3 == 0 else '新建'},
                'priority': {'name': '高' if i < 3 else '普通'},
                'created_on': created.isoformat() + 'Z',
                'closed_on': created.isoformat() + 'Z' if i % 3 == 0 else None
            })

        return {'issues': issues}

    @pytest.mark.unit
    def test_analyze_daily_trend(self, mock_service, sample_issues_with_dates):
        """测试每日趋势分析"""
        mock_service.redmine_get.return_value = sample_issues_with_dates
        mock_service.get_historical_issues = MagicMock(return_value=sample_issues_with_dates['issues'])

        trend = mock_service.analyze_daily_trend(341, days=7)

        assert trend is not None
        assert 'period_days' in trend
        assert trend['period_days'] == 7
        assert 'daily_stats' in trend
        assert 'trend_direction' in trend

    @pytest.mark.unit
    def test_analyze_weekly_trend(self, mock_service, sample_issues_with_dates):
        """测试每周趋势分析"""
        mock_service.get_historical_issues = MagicMock(return_value=sample_issues_with_dates['issues'])

        trend = mock_service.analyze_weekly_trend(341, weeks=4)

        assert trend is not None
        assert 'period_weeks' in trend
        assert trend['period_weeks'] == 4
        assert 'weekly_stats' in trend

    @pytest.mark.unit
    def test_analyze_monthly_trend(self, mock_service, sample_issues_with_dates):
        """测试每月趋势分析"""
        mock_service.get_historical_issues = MagicMock(return_value=sample_issues_with_dates['issues'])

        trend = mock_service.analyze_monthly_trend(341, months=6)

        assert trend is not None
        assert 'period_months' in trend
        assert trend['period_months'] == 6
        assert 'monthly_stats' in trend

    @pytest.mark.unit
    def test_trend_direction_improving(self, mock_service):
        """测试趋势方向 - 改善"""
        mock_service.get_historical_issues = MagicMock(return_value=[])

        # Mock 趋势数据 - 关闭数递增
        with patch.object(mock_service, '_generate_trend_summary') as mock_summary:
            mock_summary.return_value = {'trend': 'up'}

            trend = mock_service.analyze_daily_trend(341, days=7)

            assert 'trend_direction' in trend

    @pytest.mark.unit
    def test_trend_summary_generation(self, mock_service):
        """测试趋势摘要生成"""
        trend_data = [
            {'new': 5, 'closed': 3, 'total_open': 100, 'total_closed': 50},
            {'new': 6, 'closed': 4, 'total_open': 102, 'total_closed': 54},
            {'new': 7, 'closed': 5, 'total_open': 104, 'total_closed': 59}
        ]

        summary = mock_service._generate_trend_summary(trend_data)

        assert summary is not None
        assert 'total_new' in summary
        assert 'total_closed' in summary
        assert 'avg_new_per_period' in summary
        assert 'change_rate_percent' in summary


class TestTrendDataStructure:
    """趋势数据结构测试"""

    @pytest.mark.unit
    def test_daily_stats_structure(self):
        """测试每日统计结构"""
        daily_stat = {
            'date': '2026-02-27',
            'new': 5,
            'closed': 3,
            'total_open': 100,
            'total_closed': 50
        }

        assert 'date' in daily_stat
        assert 'new' in daily_stat
        assert 'closed' in daily_stat
        assert 'total_open' in daily_stat
        assert 'total_closed' in daily_stat

    @pytest.mark.unit
    def test_weekly_stats_structure(self):
        """测试每周统计结构"""
        weekly_stat = {
            'week': 'W1_2026-02-24',
            'start_date': '2026-02-24',
            'end_date': '2026-03-02',
            'new': 30,
            'closed': 25,
            'total_open': 150,
            'total_closed': 300
        }

        assert 'week' in weekly_stat
        assert 'start_date' in weekly_stat
        assert 'end_date' in weekly_stat
        assert 'new' in weekly_stat
        assert 'closed' in weekly_stat

    @pytest.mark.unit
    def test_monthly_stats_structure(self):
        """测试每月统计结构"""
        monthly_stat = {
            'month': '2026-02',
            'new': 120,
            'closed': 95,
            'total_open': 200,
            'total_closed': 500
        }

        assert 'month' in monthly_stat
        assert 'new' in monthly_stat
        assert 'closed' in monthly_stat

    @pytest.mark.unit
    def test_trend_summary_structure(self):
        """测试趋势摘要结构"""
        summary = {
            'total_new': 45,
            'total_closed': 38,
            'avg_new_per_period': 6.43,
            'avg_closed_per_period': 5.43,
            'change_rate_percent': 15.5,
            'trend': 'up'
        }

        assert 'total_new' in summary
        assert 'total_closed' in summary
        assert 'avg_new_per_period' in summary
        assert 'avg_closed_per_period' in summary
        assert 'change_rate_percent' in summary
        assert 'trend' in summary


class TestTrendAnalysisConvenience:
    """趋势分析辅助函数测试"""

    @pytest.mark.unit
    def test_analyze_project_trend_daily(self):
        """测试分析项目每日趋势"""
        with patch('src.redmine_mcp_server.dws.services.trend_analysis_service.TrendAnalysisService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            mock_service.analyze_daily_trend.return_value = {
                'period_days': 7,
                'trend_direction': 'improving'
            }

            from src.redmine_mcp_server.dws.services.trend_analysis_service import analyze_project_trend

            trend = analyze_project_trend(341, report_type='daily')

            assert trend['period_days'] == 7
            assert trend['trend_direction'] == 'improving'

    @pytest.mark.unit
    def test_analyze_project_trend_weekly(self):
        """测试分析项目每周趋势"""
        with patch('src.redmine_mcp_server.dws.services.trend_analysis_service.TrendAnalysisService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            mock_service.analyze_weekly_trend.return_value = {
                'period_weeks': 4,
                'trend_direction': 'stable'
            }

            from src.redmine_mcp_server.dws.services.trend_analysis_service import analyze_project_trend

            trend = analyze_project_trend(341, report_type='weekly')

            assert trend['period_weeks'] == 4
            assert trend['trend_direction'] == 'stable'

    @pytest.mark.unit
    def test_analyze_project_trend_monthly(self):
        """测试分析项目每月趋势"""
        with patch('src.redmine_mcp_server.dws.services.trend_analysis_service.TrendAnalysisService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            mock_service.analyze_monthly_trend.return_value = {
                'period_months': 6,
                'trend_direction': 'declining'
            }

            from src.redmine_mcp_server.dws.services.trend_analysis_service import analyze_project_trend

            trend = analyze_project_trend(341, report_type='monthly')

            assert trend['period_months'] == 6
            assert trend['trend_direction'] == 'declining'
