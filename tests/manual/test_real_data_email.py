#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发送真实的江苏新顺 CIM 项目日报
使用 Redmine API 获取真实数据 (使用 requests 库)
"""

import os
import requests
import logging
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv('.env.docker')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
REDMINE_URL = os.getenv('REDMINE_URL')
API_KEY = os.getenv('REDMINE_API_KEY')
PROJECT_ID = 341  # 江苏新顺 CIM

# SMTP Configuration
SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
SMTP_USER = os.getenv('EMAIL_SMTP_USER')
SMTP_PASSWORD = os.getenv('EMAIL_SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('EMAIL_SENDER_EMAIL')
SENDER_NAME = os.getenv('EMAIL_SENDER_NAME', 'Redmine MCP Server')

print("=" * 70)
print("测试发送真实的江苏新顺 CIM 项目日报")
print("=" * 70)
print()
print(f"Redmine URL: {REDMINE_URL}")
print(f"Project ID: {PROJECT_ID}")
print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
print(f"SMTP Server: {SMTP_SERVER}")
print(f"Sender: {SENDER_EMAIL}")
print()

# Helper function to call Redmine API
def redmine_get(endpoint, params=None):
    """Call Redmine REST API"""
    url = f"{REDMINE_URL}/{endpoint}"
    all_params = {'key': API_KEY, **(params or {})}
    resp = requests.get(url, params=all_params, timeout=30)
    resp.raise_for_status()
    return resp.json()

# Get project info
try:
    logger.info(f"Fetching project {PROJECT_ID} info...")
    project_data = redmine_get(f"projects/{PROJECT_ID}.json")
    project_name = project_data['project']['name']
    logger.info(f"Project: {project_name}")
except Exception as e:
    logger.error(f"Failed to get project: {e}")
    print(f"\n❌ 获取项目信息失败：{e}")
    sys.exit(1)

# Get all issues
try:
    logger.info("Fetching issues...")
    all_issues = []
    offset = 0
    limit = 100
    
    while True:
        data = redmine_get("issues.json", {
            'project_id': PROJECT_ID,
            'status_id': '*',
            'limit': limit,
            'offset': offset,
            'include': 'journals'
        })
        issues = data.get('issues', [])
        all_issues.extend(issues)
        
        if len(issues) < limit:
            break
        
        offset += limit
        logger.info(f"Fetched {len(all_issues)} issues...")
    
    logger.info(f"Total issues: {len(all_issues)}")
except Exception as e:
    logger.error(f"Failed to get issues: {e}")
    print(f"\n❌ 获取 Issue 失败：{e}")
    sys.exit(1)

# Calculate statistics
print()
print("正在统计项目数据...")

total_issues = len(all_issues)

# Status distribution
by_status = {}
for issue in all_issues:
    status = issue.get('status', {}).get('name', 'Unknown')
    by_status[status] = by_status.get(status, 0) + 1

open_issues = sum(1 for i in all_issues if i.get('status', {}).get('name') != '已关闭')
closed_issues = sum(1 for i in all_issues if i.get('status', {}).get('name') == '已关闭')

# Priority distribution
by_priority = {}
for issue in all_issues:
    priority = issue.get('priority', {}).get('name', '普通')
    by_priority[priority] = by_priority.get(priority, 0) + 1

# High priority issues
high_priority_issues = [
    i for i in all_issues 
    if i.get('priority', {}).get('name') in ['立刻', '紧急', '高']
][:5]

# Top assignees
assignee_count = {}
for issue in all_issues:
    assigned_to = issue.get('assigned_to')
    if assigned_to:
        name = assigned_to.get('name', 'Unknown')
        assignee_count[name] = assignee_count.get(name, 0) + 1

top_assignees = sorted(assignee_count.items(), key=lambda x: x[1], reverse=True)[:5]

# Today's stats
today = datetime.now().date()
today_new = 0
today_closed = 0

for issue in all_issues:
    created_on = issue.get('created_on', '')
    if created_on:
        try:
            created_date = datetime.fromisoformat(created_on.replace('Z', '+00:00')).date()
            if created_date == today:
                today_new += 1
        except:
            pass
    
    closed_on = issue.get('closed_on', '')
    if closed_on:
        try:
            closed_date = datetime.fromisoformat(closed_on.replace('Z', '+00:00')).date()
            if closed_date == today:
                today_closed += 1
        except:
            pass

print(f"  Issue 总数：{total_issues}")
print(f"  未关闭：{open_issues}")
print(f"  已关闭：{closed_issues}")
print(f"  今日新增：{today_new}")
print(f"  今日关闭：{today_closed}")
print()

# Generate email HTML
def generate_email_html():
    """生成邮件 HTML 内容"""
    
    report_date = today.strftime("%Y-%m-%d")
    
    # Status rows
    status_rows = ""
    for status, count in sorted(by_status.items()):
        status_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{status}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{count}</td>
        </tr>
        """

    # Priority rows
    priority_rows = ""
    for priority, count in sorted(by_priority.items()):
        priority_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{priority}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{count}</td>
        </tr>
        """

    # High priority issues
    high_priority_html = ""
    if high_priority_issues:
        high_priority_html = """
        <h3 style="color: #dc3545; margin-top: 20px;">🔥 高优先级 Issue</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background-color: #f5f5f5;">
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">主题</th>
                <th style="padding: 10px; border: 1px solid #ddd;">优先级</th>
                <th style="padding: 10px; border: 1px solid #ddd;">状态</th>
                <th style="padding: 10px; border: 1px solid #ddd;">负责人</th>
            </tr>
        """
        for issue in high_priority_issues:
            subject = issue.get('subject', 'N/A')
            subject = subject[:50] + '...' if len(subject) > 50 else subject
            priority = issue.get('priority', {}).get('name', 'N/A')
            status = issue.get('status', {}).get('name', 'N/A')
            assignee = issue.get('assigned_to', {}).get('name', '未分配')
            issue_id = issue.get('id')
            url = f"{REDMINE_URL}/issues/{issue_id}"
            high_priority_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    <a href="{url}" style="color: #007bff; text-decoration: none;">{subject}</a>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #dc3545;">{priority}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{status}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{assignee}</td>
            </tr>
            """
        high_priority_html += "</table>"

    # Top assignees
    assignees_html = ""
    if top_assignees:
        assignees_html = """
        <h3 style="color: #007bff; margin-top: 20px;">👥 人员任务量 TOP</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <tr style="background-color: #f5f5f5;">
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">姓名</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Issue 数</th>
            </tr>
        """
        for name, count in top_assignees:
            assignees_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{name}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{count}</td>
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
            <h2 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                📊 {project_name} - 项目详细状态报告
            </h2>
            <p style="color: #666; font-size: 14px;">报告日期：{report_date}</p>
            
            <h3 style="color: #333; margin-top: 25px; background-color: #f8f9fa; padding: 10px;">📈 概览</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
                <tr style="background-color: #007bff; color: white;">
                    <th style="padding: 12px; border: 1px solid #ddd;">指标</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">数量</th>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #ddd;">Issue 总数</td>
                    <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">{total_issues}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 12px; border: 1px solid #ddd;">今日新增</td>
                    <td style="padding: 12px; border: 1px solid #ddd; color: #28a745; font-weight: bold;">+{today_new}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #ddd;">今日关闭</td>
                    <td style="padding: 12px; border: 1px solid #ddd; color: #007bff; font-weight: bold;">{today_closed}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 12px; border: 1px solid #ddd;">未关闭</td>
                    <td style="padding: 12px; border: 1px solid #ddd; color: #dc3545; font-weight: bold;">{open_issues}</td>
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
                    Redmine: <a href="{REDMINE_URL}/projects/{PROJECT_ID}" style="color: #007bff;">{project_name}</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


# Send email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

def send_email(to_email, subject, html_body):
    """发送邮件"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = f'{SENDER_NAME} <{SENDER_EMAIL}>'
        msg['To'] = to_email
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


# Generate and send
print("正在生成邮件内容...")
html_body = generate_email_html()

subject = f"[Redmine] {project_name} - 项目详细状态报告 ({today.strftime('%Y-%m-%d')})"
to_email = SENDER_EMAIL  # Send to configured email

print(f"正在发送邮件到：{to_email}")
print(f"主题：{subject}")
print()

success = send_email(to_email, subject, html_body)

print()
print("=" * 70)
if success:
    print("✅ 邮件发送成功!")
    print()
    print("数据统计:")
    print(f"  - Issue 总数：{total_issues}")
    print(f"  - 未关闭：{open_issues}")
    print(f"  - 已关闭：{closed_issues}")
    print(f"  - 今日新增：{today_new}")
    print(f"  - 今日关闭：{today_closed}")
    print(f"  - 高优先级：{len(high_priority_issues)}")
    print(f"  - 贡献者：{len(top_assignees)}")
else:
    print("❌ 邮件发送失败，请检查日志")
print("=" * 70)
