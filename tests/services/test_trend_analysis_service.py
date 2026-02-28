#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trend Analysis Service Tests

Tests for trend analysis service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime, timedelta

# Set test environment
os.environ['REDMINE_URL'] = 'http://test-redmine.com'
os.environ['REDMINE_API_KEY'] = 'test_api_key'


class TestTrendAnalysisService:
    """Trend analysis service tests"""

    @pytest.fixture
    def mock_service(self):
        """Create mock service"""
        from src.redmine_mcp_server.dws.services.trend_analysis_service import TrendAnalysisService
        service = TrendAnalysisService()
        service.redmine_get = MagicMock()
        return service

    @pytest.fixture
    def sample_issues_with_dates(self):
        """Sample issue data with dates"""
        today = datetime.now()
        issues = []

        # Generate issues for past 7 days
        for i in range(10):
            created = today - timedelta(days=i % 7)
            issues.append({
                'id': i + 1,
                'subject': f'Issue {i + 1}',
                'status': {'name': 'Closed' if i % 3 == 0 else 'New'},
                'priority': {'name': 'High' if i < 3 else 'Normal'},
                'created_on': created.isoformat() + 'Z',
                'closed_on': created.isoformat() + 'Z' if i % 3 == 0 else None
            })

        return {'issues': issues}

    @pytest.mark.unit
    def test_service_initialization(self, mock_service):
        """Test service initialization"""
        assert mock_service is not None
        assert mock_service.redmine_url == 'http://test-redmine.com'

    @pytest.mark.unit
    def test_analyze_daily_trend(self, mock_service, sample_issues_with_dates):
        """Test daily trend analysis"""
        mock_service.get_historical_issues = MagicMock(return_value=sample_issues_with_dates['issues'])

        trend = mock_service.analyze_daily_trend(341, days=7)

        assert trend is not None
        assert 'period_days' in trend
        assert 'daily_stats' in trend or 'summary' in trend

    @pytest.mark.unit
    def test_analyze_weekly_trend(self, mock_service, sample_issues_with_dates):
        """Test weekly trend analysis"""
        mock_service.get_historical_issues = MagicMock(return_value=sample_issues_with_dates['issues'])

        trend = mock_service.analyze_weekly_trend(341, weeks=4)

        assert trend is not None
        assert 'period_weeks' in trend

    @pytest.mark.unit
    def test_analyze_monthly_trend(self, mock_service, sample_issues_with_dates):
        """Test monthly trend analysis"""
        mock_service.get_historical_issues = MagicMock(return_value=sample_issues_with_dates['issues'])

        trend = mock_service.analyze_monthly_trend(341, months=6)

        assert trend is not None
        assert 'period_months' in trend or 'monthly_stats' in trend

    @pytest.mark.unit
    def test_trend_direction_improving(self, mock_service):
        """Test trend direction - improving"""
        mock_service.get_historical_issues = MagicMock(return_value=[])

        # Mock trend data - increasing closures
        with patch.object(mock_service, '_generate_trend_summary') as mock_summary:
            mock_summary.return_value = {'trend': 'up'}

            trend = mock_service.analyze_daily_trend(341, days=7)

            # Trend should be mocked
            assert trend is not None

    @pytest.mark.unit
    def test_trend_summary_generation(self, mock_service):
        """Test trend summary generation"""
        trend_data = [
            {'new': 5, 'closed': 3, 'total_open': 100, 'total_closed': 50},
            {'new': 6, 'closed': 4, 'total_open': 102, 'total_closed': 54},
            {'new': 7, 'closed': 5, 'total_open': 104, 'total_closed': 59}
        ]

        summary = mock_service._generate_trend_summary(trend_data)

        assert summary is not None
        # Summary should contain calculated values
        assert isinstance(summary, dict)
