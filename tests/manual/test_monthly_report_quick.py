#!/usr/bin/env python3
"""快速测试月报推送"""

import sys
sys.path.insert(0, '/docker/redmine-mcp-server/src')

from dotenv import load_dotenv
load_dotenv('.env.docker')

import os
from datetime import datetime

# 配置
PROJECT_ID = 341
TO_EMAIL = os.getenv('EMAIL_SENDER_EMAIL', 'jenkins@fa-software.com')

print("=" * 70)
print("快速测试：月报推送")
print("=" * 70)
print()

# 1. 获取项目数据
print("1. 从 Redmine 获取数据...")
import requests

REDMINE_URL = os.getenv('REDMINE_URL')
API_KEY = os.getenv('REDMINE_API_KEY')

def redmine_get(endpoint, params=None):
    url = f"{REDMINE_URL}/{endpoint}"
    all_params = {'key': API_KEY, **(params or {})}
    resp = requests.get(url, params=all_params, timeout=30)
    resp.raise_for_status()
    return resp.json()

# 获取所有 issues
all_issues = []
offset = 0
limit = 100

while True:
    data = redmine_get("issues.json", {
        'project_id': PROJECT_ID,
        'status_id': '*',
        'limit': limit,
        'offset': offset
    })
    issues = data.get('issues', [])
    all_issues.extend(issues)
    if len(issues) < limit:
        break
    offset += limit
    print(f"   已获取 {len(all_issues)} 个 issues...")

print(f"   ✅ 共获取 {len(all_issues)} 个 issues")
print()

# 2. 统计数据
print("2. 统计数据...")
total = len(all_issues)
open_count = sum(1 for i in all_issues if i.get('status', {}).get('name') != '已关闭')
closed_count = sum(1 for i in all_issues if i.get('status', {}).get('name') == '已关闭')

# 本月统计
now = datetime.now()
month_start = now.replace(day=1)
month_new = sum(1 for i in all_issues if i.get('created_on', '') >= month_start.isoformat())
month_closed = sum(1 for i in all_issues if i.get('closed_on', '') and i.get('closed_on', '') >= month_start.isoformat())

print(f"   Issue 总数：{total}")
print(f"   未关闭：{open_count}")
print(f"   已关闭：{closed_count}")
print(f"   本月新增：{month_new}")
print(f"   本月关闭：{month_closed}")
print()

# 3. 生成邮件
print("3. 生成并发送邮件...")
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
SMTP_USER = os.getenv('EMAIL_SMTP_USER')
SMTP_PASSWORD = os.getenv('EMAIL_SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('EMAIL_SENDER_EMAIL')

# 获取项目名称
project_data = redmine_get(f"projects/{PROJECT_ID}.json")
project_name = project_data['project']['name']

# 生成 HTML
month_str = now.strftime("%Y-%m")
html = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>📊 {project_name} - 项目月报</h2>
    <p>报告月份：{month_str}</p>
    
    <h3>📈 概览</h3>
    <table border="1" cellpadding="8" cellspacing="0">
        <tr style="background-color: #007bff; color: white;">
            <th>指标</th><th>数量</th>
        </tr>
        <tr><td>Issue 总数</td><td>{total}</td></tr>
        <tr style="background-color: #f9f9f9;"><td>本月新增</td><td style="color: #28a745;">+{month_new}</td></tr>
        <tr><td>本月关闭</td><td style="color: #007bff;">{month_closed}</td></tr>
        <tr style="background-color: #f9f9f9;"><td>未关闭</td><td style="color: #dc3545;">{open_count}</td></tr>
        <tr><td>已关闭</td><td>{closed_count}</td></tr>
        <tr style="background-color: #f9f9f9;"><td>完成率</td><td>{round(closed_count/total*100, 1) if total > 0 else 0}%</td></tr>
    </table>
    
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #999; font-size: 12px;">此邮件由 Redmine MCP Server 自动发送</p>
</body>
</html>
"""

# 发送邮件
msg = MIMEMultipart()
subject = f"[Redmine] {project_name} - 项目月报 ({month_str})"
msg['Subject'] = Header(subject, 'utf-8')
msg['From'] = f'{SENDER_EMAIL}'
msg['To'] = TO_EMAIL
msg.attach(MIMEText(html, 'html', 'utf-8'))

server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.starttls()
server.login(SMTP_USER, SMTP_PASSWORD)
server.sendmail(SENDER_EMAIL, [TO_EMAIL], msg.as_string())
server.quit()

print("   ✅ 邮件发送成功!")
print()

print("=" * 70)
print("完成!")
print(f"邮件已发送到：{TO_EMAIL}")
print(f"主题：{subject}")
print("=" * 70)
