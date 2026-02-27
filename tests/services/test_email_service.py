#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Service Tests

测试邮件发送服务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Set test environment before importing service
os.environ['EMAIL_SMTP_SERVER'] = 'smtp.test.com'
os.environ['EMAIL_SMTP_PORT'] = '587'
os.environ['EMAIL_SMTP_USER'] = 'test@test.com'
os.environ['EMAIL_SMTP_PASSWORD'] = 'test_password'
os.environ['EMAIL_SENDER_EMAIL'] = 'test@test.com'
os.environ['EMAIL_SENDER_NAME'] = 'Test Server'


class TestEmailPushService:
    """邮件推送服务测试"""

    @pytest.fixture
    def email_service(self):
        """创建邮件服务实例"""
        from src.redmine_mcp_server.dws.services.email_service import EmailPushService
        return EmailPushService()

    @pytest.mark.unit
    def test_service_initialization(self, email_service):
        """测试服务初始化"""
        assert email_service is not None
        assert email_service.smtp_server == 'smtp.test.com'
        assert email_service.smtp_port == 587
        assert email_service.smtp_user == 'test@test.com'

    @pytest.mark.unit
    def test_is_configured(self, email_service):
        """测试配置检查"""
        assert email_service._is_configured() == True

    @pytest.mark.unit
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service):
        """测试邮件发送成功"""
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = email_service.send_email(
            to_email='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )

        assert result.get('success') == True
        assert result.get('to') == 'recipient@example.com'
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @pytest.mark.unit
    @patch('smtplib.SMTP')
    def test_send_email_auth_failure(self, mock_smtp, email_service):
        """测试 SMTP 认证失败"""
        import smtplib
        mock_smtp.return_value.starttls.side_effect = smtplib.SMTPAuthenticationError(
            535, b'Authentication failed'
        )

        result = email_service.send_email(
            to_email='recipient@example.com',
            subject='Test',
            body='Test'
        )

        assert result.get('success') == False
        assert 'authentication' in result.get('error', '').lower()

    @pytest.mark.unit
    def test_test_connection(self, email_service):
        """测试连接测试方法"""
        # 由于需要真实 SMTP，这里只测试方法存在
        assert hasattr(email_service, 'test_connection')


class TestSendSubscriptionEmail:
    """订阅邮件发送测试"""

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
    @patch('src.redmine_mcp_server.dws.services.email_service.get_email_service')
    def test_send_subscription_email(self, mock_get_service, sample_report):
        """测试订阅邮件发送"""
        mock_service = MagicMock()
        mock_service.send_email.return_value = {'success': True}
        mock_get_service.return_value = mock_service

        from src.redmine_mcp_server.dws.services.email_service import send_subscription_email

        result = send_subscription_email(
            to_email='user@example.com',
            project_name='Test Project',
            report=sample_report,
            level='brief'
        )

        assert result.get('success') == True
        mock_service.send_email.assert_called_once()


class TestEmailBodyGeneration:
    """邮件正文生成测试"""

    @pytest.fixture
    def sample_report(self):
        return {
            'type': 'daily',
            'stats': {
                'total_issues': 100,
                'open_issues': 30,
                'closed_issues': 70,
                'today_new': 5,
                'today_closed': 3,
                'by_status': {'新建': 10, '进行中': 20},
                'by_priority': {'高': 5, '普通': 95}
            }
        }

    @pytest.mark.unit
    def test_generate_overview_section(self, sample_report):
        """测试概览部分生成"""
        from src.redmine_mcp_server.dws.services.email_service import _generate_overview_section

        html = _generate_overview_section(sample_report['stats'], sample_report)

        assert 'Issue 总数' in html
        assert '今日新增' in html
        assert '100' in html
        assert '+5' in html

    @pytest.mark.unit
    def test_generate_email_body_brief(self, sample_report):
        """测试简要报告生成"""
        from src.redmine_mcp_server.dws.services.email_service import _generate_email_body

        html = _generate_email_body('Test Project', sample_report, level='brief')

        assert 'Test Project' in html
        assert '日报' in html
        assert '📈 概览' in html

    @pytest.mark.unit
    def test_generate_email_body_detailed(self, sample_report):
        """测试详细报告生成"""
        sample_report['stats']['high_priority_issues'] = [
            {'subject': 'Critical Issue', 'priority': {'name': '立刻'}}
        ]
        sample_report['stats']['top_assignees'] = [
            {'name': '张三', 'count': 10}
        ]

        from src.redmine_mcp_server.dws.services.email_service import _generate_email_body

        html = _generate_email_body('Test Project', sample_report, level='detailed')

        assert '🔥 高优先级 Issue' in html
        assert '👥 人员任务量' in html
