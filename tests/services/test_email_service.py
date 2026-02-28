#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Service Tests

Tests for email service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Set test environment
os.environ['EMAIL_SMTP_SERVER'] = 'smtp.test.com'
os.environ['EMAIL_SMTP_PORT'] = '587'
os.environ['EMAIL_SMTP_USER'] = 'test@test.com'
os.environ['EMAIL_SMTP_PASSWORD'] = 'test_password'


class TestEmailPushService:
    """Email push service tests"""

    @pytest.fixture
    def email_service(self):
        """Create email service instance"""
        from src.redmine_mcp_server.dws.services.email_service import EmailPushService
        return EmailPushService()

    @pytest.mark.unit
    def test_service_initialization(self, email_service):
        """Test service initialization"""
        assert email_service is not None
        assert email_service.smtp_server == 'smtp.test.com'
        assert email_service.smtp_port == 587


class TestSendSubscriptionEmail:
    """Send subscription email tests"""

    @pytest.fixture
    def sample_report(self):
        """Sample report data"""
        return {
            'type': 'daily',
            'project_id': 341,
            'date': '2026-02-28',
            'stats': {
                'total_issues': 100,
                'open_issues': 30,
                'closed_issues': 70,
                'today_new': 5,
                'today_closed': 3
            }
        }

    @pytest.mark.unit
    def test_send_subscription_email(self, sample_report):
        """Test sending subscription email"""
        from src.redmine_mcp_server.dws.services.email_service import send_subscription_email

        with patch('src.redmine_mcp_server.dws.services.email_service.get_email_service') as mock_get_service, \
             patch('src.redmine_mcp_server.dws.services.email_service._generate_email_body') as mock_generate:
            mock_service = MagicMock()
            mock_service.send_email.return_value = {'success': True}
            mock_get_service.return_value = mock_service
            mock_generate.return_value = '<html>Test</html>'

            result = send_subscription_email(
                to_email='user@example.com',
                project_name='Test Project',
                report=sample_report,
                level='brief',
                language='en_US'
            )

            assert result is not None
            # Function should call send_email
            mock_service.send_email.assert_called_once()


class TestEmailBodyGeneration:
    """Email body generation tests"""

    @pytest.fixture
    def sample_report(self):
        """Sample report data"""
        return {
            'type': 'daily',
            'project_id': 341,
            'date': '2026-02-28',
            'stats': {
                'total_issues': 100,
                'open_issues': 30,
                'closed_issues': 70,
                'today_new': 5,
                'today_closed': 3,
                'by_status': {'New': 15, 'Closed': 70},
                'by_priority': {'High': 5, 'Normal': 95}
            }
        }

    @pytest.mark.unit
    def test_generate_email_body_brief(self, sample_report):
        """Test brief email body generation"""
        with patch('src.redmine_mcp_server.dws.services.email_service._generate_email_body') as mock_generate:
            mock_generate.return_value = '<html>Test</html>'
            
            from src.redmine_mcp_server.dws.services.email_service import _generate_email_body

            html = _generate_email_body('Test Project', sample_report, level='brief', language='en_US')

            assert html is not None
            assert 'html' in html.lower()

    @pytest.mark.unit
    def test_generate_email_body_detailed(self, sample_report):
        """Test detailed email body generation"""
        with patch('src.redmine_mcp_server.dws.services.email_service._generate_email_body') as mock_generate:
            mock_generate.return_value = '<html>Detailed</html>'
            
            from src.redmine_mcp_server.dws.services.email_service import _generate_email_body

            # Add more data for detailed report
            sample_report['stats']['high_priority_issues'] = [
                {'subject': 'Critical Issue', 'priority': {'name': 'High'}}
            ]
            sample_report['stats']['top_assignees'] = [
                {'name': 'John Doe', 'count': 10}
            ]

            html = _generate_email_body('Test Project', sample_report, level='detailed', language='en_US')

            assert html is not None
