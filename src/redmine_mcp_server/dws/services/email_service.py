#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件推送服务

支持通过邮件发送订阅报告（多语言支持）
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailPushService:
    """邮件推送服务"""

    def __init__(self):
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER", "")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("EMAIL_SMTP_USER", "")
        self.smtp_password = os.getenv("EMAIL_SMTP_PASSWORD", "")
        self.sender_email = os.getenv("EMAIL_SENDER_EMAIL", self.smtp_user)
        self.sender_name = os.getenv("EMAIL_SENDER_NAME", "Redmine MCP Server")
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        
        self._validate_config()

    def _validate_config(self):
        """验证邮件配置"""
        if not self.smtp_server:
            logger.warning("EMAIL_SMTP_SERVER not configured")
        if not self.smtp_user:
            logger.warning("EMAIL_SMTP_USER not configured")
        if not self.smtp_password:
            logger.warning("EMAIL_SMTP_PASSWORD not configured")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            html: 是否为 HTML 格式

        Returns:
            发送结果
        """
        if not self._is_configured():
            return {
                "success": False,
                "error": "Email service not configured properly"
            }

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email

            # Attach body
            content_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))

            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.sender_email, [to_email], msg.as_string())
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")

            return {
                "success": True,
                "message": f"Email sent to {to_email}",
                "to": to_email,
                "subject": subject
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {
                "success": False,
                "error": f"SMTP authentication failed: {str(e)}"
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }

    def _is_configured(self) -> bool:
        """检查邮件服务是否已正确配置"""
        return bool(self.smtp_server and self.smtp_user and self.smtp_password)

    def test_connection(self) -> Dict[str, Any]:
        """测试邮件服务连接"""
        if not self._is_configured():
            return {
                "success": False,
                "error": "Email service not configured"
            }

        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.smtp_user, self.smtp_password)
            server.quit()

            return {
                "success": True,
                "message": "SMTP connection successful",
                "server": self.smtp_server,
                "port": self.smtp_port
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global service instance
_email_service: Optional[EmailPushService] = None


def get_email_service() -> EmailPushService:
    """获取邮件服务实例"""
    global _email_service
    if _email_service is None:
        _email_service = EmailPushService()
    return _email_service


def send_subscription_email(
    to_email: str,
    project_name: str,
    report: Dict[str, Any],
    level: str = "brief",
    language: str = "zh_CN"
) -> Dict[str, Any]:
    """
    发送订阅报告邮件（多语言支持）

    Args:
        to_email: 收件人邮箱
        project_name: 项目名称
        report: 报告数据（包含 stats 和可选的 trend_analysis）
        level: 报告级别 (brief/detailed/comprehensive)
        language: 语言 (zh_CN/en_US)

    Returns:
        发送结果
    """
    service = get_email_service()

    # Generate subject based on report type and language
    report_type = report.get('type', 'daily')
    
    # Format date info based on report type
    if report_type == 'daily':
        date_info = report.get('date', datetime.now().strftime("%Y-%m-%d"))
    elif report_type == 'weekly':
        date_info = f"{report.get('week_start', '')} {_('to', language)} {report.get('week_end', '')}"
    else:
        date_info = report.get('month', datetime.now().strftime("%Y-%m"))
    
    # Import i18n
    from ..i18n import format_email_subject
    subject = format_email_subject(report_type, project_name, date_info, language)
    
    # Generate email body
    body = _generate_email_body(project_name, report, level, language)

    return service.send_email(to_email, subject, body, html=True)


def _generate_email_body(
    project_name: str,
    report: Dict[str, Any],
    level: str = "brief",
    language: str = "zh_CN"
) -> str:
    """生成邮件 HTML 内容（多语言支持）"""
    stats = report.get('stats', {})
    report_type = report.get('type', 'daily')
    
    # Import i18n translations
    from ..i18n import (
        get_translations, get_report_type_name, get_section_name,
        get_metric_name, get_trend_name, get_status_name, get_priority_name
    )
    
    t = get_translations(language)
    
    # Header
    report_type_name = get_report_type_name(report_type, language)
    date_str = report.get('date', report.get('week_start', report.get('month', '')))
    
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 900px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                📊 {project_name} - {report_type_name}
            </h2>
            <p style="color: #666; font-size: 14px;">{t['EMAIL_CONTENT']['report_date' if report_type == 'daily' else 'report_month' if report_type == 'monthly' else 'report_week'].format(
                date=date_str,
                month=date_str,
                start=report.get('week_start', ''),
                end=report.get('week_end', '')
            )}</p>
    """
    
    # 概览部分
    html += _generate_overview_section(stats, report, language)
    
    # 状态分布
    if stats.get('by_status'):
        html += _generate_status_section(stats['by_status'], language)
    
    # 优先级分布
    if stats.get('by_priority'):
        html += _generate_priority_section(stats['by_priority'], language)
    
    # 高优先级 Issue
    if level in ['detailed', 'comprehensive'] and stats.get('high_priority_issues'):
        html += _generate_high_priority_section(stats['high_priority_issues'], language)
    
    # 人员任务量
    if level in ['detailed', 'comprehensive'] and stats.get('top_assignees'):
        html += _generate_assignees_section(stats['top_assignees'], language)
    
    # 趋势分析
    if level == 'comprehensive' and report.get('trend_analysis'):
        html += _generate_trend_section(report['trend_analysis'], language)
    
    # Footer
    html += f"""
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                <p style="color: #666; font-size: 12px; margin: 0;">
                    <strong>📧 {t['EMAIL_CONTENT']['footer']['auto_sent']}</strong><br>
                    {t['EMAIL_CONTENT']['footer']['sent_time']}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def _generate_overview_section(stats: Dict, report: Dict) -> str:
    """生成概览部分"""
    report_type = report.get('type', 'daily')
    
    # 根据报告类型显示不同的指标
    if report_type == 'daily':
        metrics = [
            ('Issue 总数', stats.get('total_issues', 0)),
            ('今日新增', f"+{stats.get('today_new', 0)}"),
            ('今日关闭', stats.get('today_closed', 0)),
            ('未关闭', stats.get('open_issues', 0))
        ]
    elif report_type == 'weekly':
        weekly = report.get('weekly_summary', {})
        metrics = [
            ('Issue 总数', stats.get('total_issues', 0)),
            ('本周新增', weekly.get('week_new', 0)),
            ('本周关闭', weekly.get('week_closed', 0)),
            ('净变化', f"+{weekly.get('week_net_change', 0)}")
        ]
    else:  # monthly
        monthly = report.get('monthly_summary', {})
        metrics = [
            ('Issue 总数', stats.get('total_issues', 0)),
            ('本月新增', monthly.get('month_new', 0)),
            ('本月关闭', monthly.get('month_closed', 0)),
            ('净变化', f"+{monthly.get('month_net_change', 0)}")
        ]
        if report.get('completion_rate'):
            metrics.append(('完成率', f"{report['completion_rate']}%"))
        if report.get('avg_resolution_days'):
            metrics.append(('平均解决天数', report['avg_resolution_days']))

    rows = ""
    for label, value in metrics:
        color = ''
        if '新增' in label and str(value).startswith('+'):
            color = 'color: #28a745;'
        elif '关闭' in label:
            color = 'color: #007bff;'
        elif '未关闭' in label:
            color = 'color: #dc3545;'
        
        rows += f"""
        <tr>
            <td style="padding: 12px; border: 1px solid #ddd;">{label}</td>
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; {color}">{value}</td>
        </tr>
        """

    return f"""
    <h3 style="color: #333; margin-top: 25px; background-color: #f8f9fa; padding: 10px;">📈 概览</h3>
    <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr style="background-color: #007bff; color: white;">
            <th style="padding: 12px; border: 1px solid #ddd;">指标</th>
            <th style="padding: 12px; border: 1px solid #ddd;">数量</th>
        </tr>
        {rows}
    </table>
    """
