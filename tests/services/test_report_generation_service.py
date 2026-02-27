#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Generation Service Tests

测试报告生成服务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import json

# Set test environment
os.environ['REDMINE_URL'] = 'http://test-redmine.com'
os.environ['REDMINE_API_KEY'] = 'test_api_key'


class TestReportGenerationService:
    """报告生成服务测试"""

    @pytest.fixture
    def mock_service(self):
        """创建 mock 服务"""
        with patch('src.redmine_mcp_server.dws.services.report_generation_service.ReportGenerationService'):
            from src.redmine_mcp_server.dws.services.report_generation_service import ReportGenerationService
            service = ReportGenerationService()
            service.redmine_get = MagicMock()
            return service

    @pytest.fixture
    def sample_issues_response(self):
        """示例 Issue API 响应"""
        return {
            'issues': [
                {
                    'id': 1,
                    'subject': 'Test Issue 1',
                    'status': {'id': 1, 'name': '新建'},
                    'priority': {'id': 1, 'name': '高'},
                    'created_on': '2026-02-27T09:00:00Z',
                    'updated_on': '2026-02-27T10:00:00Z'
                },
                {
                    'id': 2,
                    'subject': 'Test Issue 2',
                    'status': {'id': 3, 'name': '已关闭'},
                    'priority': {'id': 4, 'name': '普通'},
                    'created_on': '2026-02-26T09:00:00Z',
                    'closed_on': '2026-02-27T08:00:00Z'
                }
            ]
        }

    @pytest.mark.unit
    def test_get_project_stats(self, mock_service, sample_issues_response):
        """测试获取项目统计"""
        mock_service.redmine_get.return_value = sample_issues_response

        stats = mock_service.get_project_stats(341)

        assert stats is not None
        assert 'total_issues' in stats
        assert 'by_status' in stats
        assert 'by_priority' in stats

    @pytest.mark.unit
    def test_generate_daily_report(self, mock_service, sample_issues_response):
        """测试生成日报"""
        mock_service.redmine_get.return_value = sample_issues_response
        mock_service.get_project_stats = MagicMock(return_value={
            'total_issues': 2,
            'open_issues': 1,
            'closed_issues': 1,
            'today_new': 1,
            'today_closed': 1,
            'by_status': {'新建': 1, '已关闭': 1},
            'by_priority': {'高': 1, '普通': 1}
        })

        report = mock_service.generate_daily_report(341, level='brief')

        assert report is not None
        assert report['type'] == 'daily'
        assert 'stats' in report

    @pytest.mark.unit
    def test_generate_weekly_report(self, mock_service, sample_issues_response):
        """测试生成周报"""
        mock_service.get_project_stats = MagicMock(return_value={
            'total_issues': 10,
            'open_issues': 5,
            'closed_issues': 5
        })

        report = mock_service.generate_weekly_report(341, level='detailed')

        assert report is not None
        assert report['type'] == 'weekly'
        assert 'weekly_summary' in report

    @pytest.mark.unit
    def test_generate_monthly_report(self, mock_service, sample_issues_response):
        """测试生成月报"""
        mock_service.get_project_stats = MagicMock(return_value={
            'total_issues': 50,
            'open_issues': 20,
            'closed_issues': 30
        })

        report = mock_service.generate_monthly_report(341, level='comprehensive')

        assert report is not None
        assert report['type'] == 'monthly'
        assert 'monthly_summary' in report

    @pytest.mark.unit
    def test_report_level_brief(self, mock_service):
        """测试简要报告级别"""
        mock_service.get_project_stats = MagicMock(return_value={
            'total_issues': 10,
            'open_issues': 5,
            'closed_issues': 5
        })

        report = mock_service.generate_daily_report(341, level='brief')

        # Brief 报告不应包含高优先级 Issue 详情
        assert 'high_priority_issues' not in report or report.get('high_priority_issues') is None

    @pytest.mark.unit
    def test_report_level_detailed(self, mock_service):
        """测试详细报告级别"""
        mock_service.get_project_stats = MagicMock(return_value={
            'total_issues': 10,
            'open_issues': 5,
            'closed_issues': 5,
            'by_status': {'新建': 3, '已关闭': 5},
            'by_priority': {'高': 2, '普通': 8},
            'high_priority_issues': [{'id': 1, 'subject': 'Critical'}],
            'top_assignees': [{'name': '张三', 'count': 5}]
        })

        report = mock_service.generate_daily_report(341, level='detailed')

        # Detailed 报告应包含高优先级 Issue
        assert 'high_priority_issues' in report


class TestReportDataStructure:
    """报告数据结构测试"""

    @pytest.fixture
    def sample_report(self):
        """示例报告数据"""
        return {
            'type': 'daily',
            'project_id': 341,
            'date': '2026-02-27',
            'stats': {
                'total_issues': 100,
                'open_issues': 30,
                'closed_issues': 70,
                'today_new': 5,
                'today_closed': 3
            }
        }

    @pytest.mark.unit
    def test_report_type_field(self, sample_report):
        """测试报告类型字段"""
        assert 'type' in sample_report
        assert sample_report['type'] in ['daily', 'weekly', 'monthly']

    @pytest.mark.unit
    def test_report_timestamp(self, sample_report):
        """测试报告时间戳"""
        assert 'date' in sample_report or 'generated_at' in sample_report

    @pytest.mark.unit
    def test_stats_structure(self, sample_report):
        """测试统计数据结构"""
        stats = sample_report['stats']

        assert 'total_issues' in stats
        assert 'open_issues' in stats
        assert 'closed_issues' in stats

    @pytest.mark.unit
    def test_trend_analysis_structure(self):
        """测试趋势分析结构"""
        report_with_trend = {
            'type': 'daily',
            'trend_analysis': {
                'period_days': 7,
                'trend_direction': 'improving',
                'summary': {
                    'total_new': 30,
                    'total_closed': 25
                }
            }
        }

        assert 'trend_analysis' in report_with_trend
        assert 'trend_direction' in report_with_trend['trend_analysis']


class TestReportGenerationConvenience:
    """报告生成辅助函数测试"""

    @pytest.mark.unit
    def test_generate_project_report_daily(self):
        """测试生成项目日报"""
        with patch('src.redmine_mcp_server.dws.services.report_generation_service.ReportGenerationService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            mock_service.generate_report.return_value = {
                'type': 'daily',
                'project_id': 341
            }

            from src.redmine_mcp_server.dws.services.report_generation_service import generate_project_report

            report = generate_project_report(341, report_type='daily')

            assert report['type'] == 'daily'
            mock_service.generate_report.assert_called_once()

    @pytest.mark.unit
    def test_generate_project_report_weekly(self):
        """测试生成项目周报"""
        with patch('src.redmine_mcp_server.dws.services.report_generation_service.ReportGenerationService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            mock_service.generate_report.return_value = {
                'type': 'weekly',
                'project_id': 341
            }

            from src.redmine_mcp_server.dws.services.report_generation_service import generate_project_report

            report = generate_project_report(341, report_type='weekly')

            assert report['type'] == 'weekly'
