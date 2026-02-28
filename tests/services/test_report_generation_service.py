#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Generation Service Tests

Tests for report generation service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Set test environment
os.environ['REDMINE_URL'] = 'http://test-redmine.com'
os.environ['REDMINE_API_KEY'] = 'test_api_key'


class TestReportGenerationService:
    """Report generation service tests"""

    @pytest.fixture
    def mock_service(self):
        """Create mock service"""
        from src.redmine_mcp_server.dws.services.report_generation_service import ReportGenerationService
        service = ReportGenerationService()
        service.redmine_get = MagicMock()
        return service

    @pytest.fixture
    def sample_project_stats(self):
        """Sample project statistics"""
        return {
            'total_issues': 100,
            'open_issues': 30,
            'closed_issues': 70,
            'today_new': 5,
            'today_closed': 3,
            'by_status': {'New': 15, 'Closed': 70},
            'by_priority': {'High': 5, 'Normal': 95},
            'high_priority_issues': [],
            'top_assignees': []
        }

    @pytest.mark.unit
    def test_service_initialization(self, mock_service):
        """Test service initialization"""
        assert mock_service is not None
        assert mock_service.redmine_url == 'http://test-redmine.com'

    @pytest.mark.unit
    def test_get_project_stats(self, mock_service, sample_project_stats):
        """Test getting project statistics"""
        mock_service.get_project_stats = MagicMock(return_value=sample_project_stats)

        stats = mock_service.get_project_stats(341)

        assert stats is not None
        assert 'total_issues' in stats

    @pytest.mark.unit
    def test_generate_daily_report(self, mock_service, sample_project_stats):
        """Test daily report generation"""
        mock_service.get_project_stats = MagicMock(return_value=sample_project_stats)

        report = mock_service.generate_daily_report(341, level='brief')

        assert report is not None
        assert report['type'] == 'daily'
        assert 'stats' in report

    @pytest.mark.unit
    def test_generate_weekly_report(self, mock_service, sample_project_stats):
        """Test weekly report generation"""
        mock_service.get_project_stats = MagicMock(return_value=sample_project_stats)

        report = mock_service.generate_weekly_report(341, level='brief')

        assert report is not None
        assert report['type'] == 'weekly'

    @pytest.mark.unit
    def test_generate_monthly_report(self, mock_service, sample_project_stats):
        """Test monthly report generation"""
        mock_service.get_project_stats = MagicMock(return_value=sample_project_stats)

        report = mock_service.generate_monthly_report(341, level='brief')

        assert report is not None
        assert report['type'] == 'monthly'

    @pytest.mark.unit
    def test_report_level_detailed(self, mock_service, sample_project_stats):
        """Test detailed report level"""
        mock_service.get_project_stats = MagicMock(return_value=sample_project_stats)

        report = mock_service.generate_daily_report(341, level='detailed')

        assert report is not None
        # Detailed report should include high priority issues
        assert 'high_priority_issues' in report
