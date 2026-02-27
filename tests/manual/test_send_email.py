#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发送江苏新顺项目日报邮件
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

# SMTP 配置
smtp_server = 'smtp.qiye.aliyun.com'
smtp_port = 587
smtp_user = 'jenkins@fa-software.com'
smtp_password = 'qDsitTkeZINB8pbc'
sender_email = 'jenkins@fa-software.com'
sender_name = 'Redmine MCP Server'

# 江苏新顺 CIM 项目数据（模拟）
project_name = "江苏新顺 CIM"
report_date = datetime.now().strftime("%Y-%m-%d")

# 模拟项目统计数据
stats = {
    'total_issues': 156,
    'new_issues': 5,
    'closed_issues': 3,
    'open_issues': 42,
    'by_status': {
        '新建': 15,
        '进行中': 20,
        '已解决': 8,
        '已关闭': 113
    },
    'by_priority': {
        '立刻': 2,
        '紧急': 5,
        '高': 12,
        '普通': 120,
        '低': 17
    },
    'high_priority_issues': [
        {'subject': '系统登录失败问题', 'priority': '立刻', 'assignee': '张三'},
        {'subject': '数据同步异常', 'priority': '紧急', 'assignee': '李四'},
        {'subject': '报表导出功能优化', 'priority': '高', 'assignee': '王五'},
    ],
    'top_assignees': [
        {'name': '张三', 'total': 25, 'in_progress': 8},
        {'name': '李四', 'total': 20, 'in_progress': 6},
        {'name': '王五', 'total': 18, 'in_progress': 5},
    ]
}

def generate_email_body():
    """生成详细报告邮件内容"""
    
    # 状态分布行
    status_rows = ""
    for status, count in stats['by_status'].items():
        status_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{status}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{count}</td>
        </tr>
        """

    # 优先级分布行
    priority_rows = ""
    for priority, count in stats['by_priority'].items():
        priority_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{priority}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{count}</td>
        </tr>
        """

    # 高优先级 Issue
    high_priority_html = """
    <h3 style="color: #dc3545; margin-top: 20px;">🔥 高优先级 Issue</h3>
    <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr style="background-color: #f5f5f5;">
            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">主题</th>
            <th style="padding: 10px; border: 1px solid #ddd;">优先级</th>
            <th style="padding: 10px; border: 1px solid #ddd;">负责人</th>
        </tr>
    """
    for issue in stats['high_priority_issues']:
        high_priority_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{issue['subject']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #dc3545;">{issue['priority']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{issue['assignee']}</td>
        </tr>
        """
    high_priority_html += "</table>"

    # 人员任务量 TOP
    assignees_html = """
    <h3 style="color: #007bff; margin-top: 20px;">👥 人员任务量 TOP</h3>
    <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr style="background-color: #f5f5f5;">
            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">姓名</th>
            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">总数</th>
            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">进行中</th>
        </tr>
    """
    for assignee in stats['top_assignees']:
        assignees_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{assignee['name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{assignee['total']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{assignee['in_progress']}</td>
        </tr>
        """
    assignees_html += "</table>"

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">📊 {project_name} - 项目详细状态报告</h2>
            <p style="color: #666; font-size: 14px;">报告日期：{report_date}</p>
            
            <h3 style="color: #333; margin-top: 25px; background-color: #f8f9fa; padding: 10px;">📈 概览</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #007bff; color: white;">
                    <th style="padding: 12px; border: 1px solid #ddd;">指标</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">数量</th>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #ddd;">Issue 总数</td>
                    <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">{stats['total_issues']}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 12px; border: 1px solid #ddd;">今日新增</td>
                    <td style="padding: 12px; border: 1px solid #ddd; color: #28a745; font-weight: bold;">+{stats['new_issues']}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #ddd;">今日关闭</td>
                    <td style="padding: 12px; border: 1px solid #ddd; color: #007bff; font-weight: bold;">{stats['closed_issues']}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 12px; border: 1px solid #ddd;">未关闭</td>
                    <td style="padding: 12px; border: 1px solid #ddd; color: #dc3545; font-weight: bold;">{stats['open_issues']}</td>
                </tr>
            </table>

            <h3 style="color: #333; margin-top: 25px; background-color: #f8f9fa; padding: 10px;">📊 状态分布</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #007bff; color: white;">
                    <th style="padding: 10px; border: 1px solid #ddd;">状态</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">数量</th>
                </tr>
                {status_rows}
            </table>

            <h3 style="color: #333; margin-top: 25px; background-color: #f8f9fa; padding: 10px;">⚡ 优先级分布</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #007bff; color: white;">
                    <th style="padding: 10px; border: 1px solid #ddd;">优先级</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">数量</th>
                </tr>
                {priority_rows}
            </table>

            {high_priority_html}
            {assignees_html}

            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                <p style="color: #666; font-size: 12px; margin: 0;">
                    <strong>📧 此邮件由 Redmine MCP Server 自动发送</strong><br>
                    发送时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
                    如有问题，请联系系统管理员
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_email(to_email, subject, html_body):
    """发送邮件"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = f'{sender_name} <{sender_email}>'
        msg['To'] = to_email
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # 连接并发送
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(sender_email, [to_email], msg.as_string())
        server.quit()
        
        print(f'✅ 邮件发送成功!')
        print(f'   收件人：{to_email}')
        print(f'   主题：{subject}')
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f'❌ SMTP 认证失败：{e}')
        return False
    except smtplib.SMTPException as e:
        print(f'❌ SMTP 错误：{e}')
        return False
    except Exception as e:
        print(f'❌ 发送失败：{e}')
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("发送江苏新顺 CIM 项目日报邮件")
    print("=" * 60)
    print()
    
    # 生成邮件内容
    print("正在生成邮件内容...")
    html_body = generate_email_body()
    
    # 发送邮件
    subject = f"[Redmine] {project_name} - 项目详细状态报告 ({report_date})"
    
    print("正在发送邮件...")
    print()
    
    # 发送到指定邮箱
    to_email = "jenkins@fa-software.com"
    success = send_email(to_email, subject, html_body)
    
    print()
    print("=" * 60)
    if success:
        print("发送完成!")
    else:
        print("发送失败，请检查日志")
    print("=" * 60)
