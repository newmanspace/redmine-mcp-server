#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试月报推送功能

测试完整的月报生成和邮件发送流程
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from dotenv import load_dotenv
load_dotenv('.env.docker')

print("=" * 80)
print("测试月报推送功能")
print("=" * 80)
print()

# Configuration
PROJECT_ID = 341  # 江苏新顺 CIM
TO_EMAIL = os.getenv('EMAIL_SENDER_EMAIL', 'jenkins@fa-software.com')
REPORT_TYPE = 'monthly'
REPORT_LEVEL = 'comprehensive'
INCLUDE_TREND = True

print(f"配置信息:")
print(f"  项目 ID: {PROJECT_ID}")
print(f"  收件邮箱：{TO_EMAIL}")
print(f"  报告类型：{REPORT_TYPE}")
print(f"  报告级别：{REPORT_LEVEL}")
print(f"  包含趋势：{INCLUDE_TREND}")
print()

# Step 1: Generate monthly report
print("=" * 80)
print("步骤 1: 生成月报")
print("=" * 80)

# Import using direct path
sys.path.insert(0, '/docker/redmine-mcp-server/src')
from redmine_mcp_server.dws.services.report_generation_service import ReportGenerationService

service = ReportGenerationService()

print("正在从 Redmine 获取数据...")
report = service.generate_report(
    project_id=PROJECT_ID,
    report_type=REPORT_TYPE,
    report_level=REPORT_LEVEL,
    include_trend=INCLUDE_TREND,
    trend_period=180  # 6 个月趋势
)

if not report or 'error' in report:
    print(f"❌ 报告生成失败：{report.get('error', 'Unknown error')}")
    sys.exit(1)

print("✅ 月报生成成功!")
print()

# Display report summary
stats = report.get('stats', {})
monthly = report.get('monthly_summary', {})

print("📊 月报概览:")
print(f"  月份：{report.get('month', 'N/A')}")
print(f"  Issue 总数：{stats.get('total_issues', 0)}")
print(f"  本月新增：{monthly.get('month_new', 0)}")
print(f"  本月关闭：{monthly.get('month_closed', 0)}")
print(f"  净变化：{monthly.get('month_net_change', 0)}")
print(f"  未关闭：{stats.get('open_issues', 0)}")
print(f"  已关闭：{stats.get('closed_issues', 0)}")

if report.get('completion_rate'):
    print(f"  完成率：{report['completion_rate']}%")

if report.get('avg_resolution_days'):
    print(f"  平均解决天数：{report['avg_resolution_days']}天")

print()

# Display status distribution
by_status = stats.get('by_status', {})
if by_status:
    print("📋 状态分布:")
    for status, count in sorted(by_status.items()):
        print(f"    {status}: {count}")
    print()

# Display priority distribution
by_priority = stats.get('by_priority', {})
if by_priority:
    print("⚡ 优先级分布:")
    for priority, count in sorted(by_priority.items()):
        print(f"    {priority}: {count}")
    print()

# Display high priority issues
high_priority = stats.get('high_priority_issues', [])
if high_priority:
    print("🔥 高优先级 Issue:")
    for issue in high_priority[:5]:
        subject = issue.get('subject', 'N/A')[:50]
        priority = issue.get('priority', {}).get('name', 'N/A')
        assignee = issue.get('assigned_to', {}).get('name', '未分配')
        print(f"    [{priority}] {subject} - {assignee}")
    print()

# Display trend analysis
if INCLUDE_TREND and report.get('trend_analysis'):
    trend = report['trend_analysis']
    print("📈 趋势分析:")
    print(f"    分析周期：{trend.get('period_months', 0)} 个月")
    print(f"    趋势方向：{trend.get('trend_direction', 'stable')}")
    
    summary = trend.get('summary', {})
    print(f"    总新增：{summary.get('total_new', 0)}")
    print(f"    总关闭：{summary.get('total_closed', 0)}")
    print(f"    平均每月新增：{summary.get('avg_new_per_period', 0):.2f}")
    print(f"    平均每月关闭：{summary.get('avg_closed_per_period', 0):.2f}")
    print(f"    变化率：{summary.get('change_rate_percent', 0):.2f}%")
    print()

# Step 2: Send email
print("=" * 80)
print("步骤 2: 发送邮件")
print("=" * 80)

# Import email service
from redmine_mcp_server.dws.services.email_service import send_subscription_email

try:
    # Get project name
    project_data = service.redmine_get(f"projects/{PROJECT_ID}.json")
    project_name = project_data['project']['name']
    print(f"项目名称：{project_name}")
except Exception as e:
    project_name = f"Project {PROJECT_ID}"
    print(f"无法获取项目名称，使用默认：{project_name}")

print(f"正在发送邮件到：{TO_EMAIL}")
print(f"邮件主题：[Redmine] {project_name} - 项目月报 ({report.get('month', 'N/A')})")
print()

result = send_subscription_email(
    to_email=TO_EMAIL,
    project_name=project_name,
    report=report,
    level=REPORT_LEVEL
)

if result.get('success'):
    print("✅ 邮件发送成功!")
    print(f"   收件人：{result.get('to', TO_EMAIL)}")
    print(f"   主题：[Redmine] {project_name} - 项目月报 ({report.get('month', 'N/A')})")
else:
    print(f"❌ 邮件发送失败：{result.get('error', 'Unknown error')}")
    sys.exit(1)

print()
print("=" * 80)
print("测试完成!")
print("=" * 80)
print()
print("下一步:")
print("  1. 检查邮箱，查看月报邮件")
print("  2. 验证邮件内容是否正确")
print("  3. 确认趋势分析数据显示正常")
print("  4. 确认所有统计指标准确")
print()
