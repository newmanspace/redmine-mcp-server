#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试订阅推送服务
"""

import os
import sys
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv('.env.docker')

print("=" * 70)
print("测试订阅推送服务")
print("=" * 70)
print()

from src.redmine_mcp_server.dws.services.subscription_push_service import SubscriptionPushService

print("初始化订阅推送服务...")
service = SubscriptionPushService()

print()
print("获取项目 341 统计数据...")
stats = service.get_project_stats(341)

if stats:
    print(f"✅ 获取到统计数据:")
    print(f"   Issue 总数：{stats['total_issues']}")
    print(f"   未关闭：{stats['open_issues']}")
    print(f"   已关闭：{stats['closed_issues']}")
    print(f"   今日新增：{stats['today_new']}")
    print(f"   今日关闭：{stats['today_closed']}")
    print()
    
    # 发送邮件
    print("发送邮件到 jenkins@fa-software.com...")
    success = service.send_email_report(
        to_email="jenkins@fa-software.com",
        project_name="江苏新顺 CIM",
        stats=stats,
        level="detailed"
    )
    
    print()
    print("=" * 70)
    if success:
        print("✅ 邮件发送成功!")
    else:
        print("❌ 邮件发送失败")
    print("=" * 70)
else:
    print("❌ 获取统计数据失败")
