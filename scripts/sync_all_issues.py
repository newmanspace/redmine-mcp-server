#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量同步所有 Issue（包含已关闭的）
"""

import requests
import psycopg2
from datetime import datetime
import sys

REDMINE_URL = 'http://redmine.fa-software.com'
API_KEY = 'adabb6a1089a5ac90e5649f505029d28e1cc9bc7'
HEADERS = {'X-Redmine-API-Key': API_KEY}

DB_CONFIG = {
    'host': 'warehouse-db',
    'port': '5432',
    'dbname': 'redmine_warehouse',
    'user': 'redmine_warehouse',
    'password': 'WarehouseP@ss2026'
}

def sync_all_issues():
    """同步所有 Issue（包含已关闭的）"""
    print(f'开始同步所有 Issue（包含已关闭）...')
    
    # 连接数据库
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 获取总数量
    resp = requests.get(
        f'{REDMINE_URL}/issues.json',
        headers=HEADERS,
        params={'status_id': '*', 'limit': 1},
        timeout=30
    )
    total_count = resp.json().get('total_count', 0)
    print(f'Redmine 总 Issue 数：{total_count:,}')
    
    # 分批同步
    batch_size = 500
    offset = 0
    total_synced = 0
    total_inserted = 0
    
    while offset < total_count:
        try:
            # 获取一批 Issue
            resp = requests.get(
                f'{REDMINE_URL}/issues.json',
                headers=HEADERS,
                params={'status_id': '*', 'offset': offset, 'limit': batch_size},
                timeout=120
            )
            data = resp.json()
            issues = data.get('issues', [])
            
            if not issues:
                break
            
            # 批量插入
            batch_inserted = 0
            for issue in issues:
                try:
                    cur.execute('''
                        INSERT INTO warehouse.ods_issues (
                            issue_id, project_id, tracker_id, status_id, priority_id,
                            author_id, assigned_to_id, parent_issue_id, subject,
                            description, start_date, due_date, done_ratio,
                            estimated_hours, spent_hours, created_on, updated_on,
                            closed_on, sync_time
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (issue_id) DO UPDATE SET
                            project_id = EXCLUDED.project_id,
                            status_id = EXCLUDED.status_id,
                            priority_id = EXCLUDED.priority_id,
                            assigned_to_id = EXCLUDED.assigned_to_id,
                            subject = EXCLUDED.subject,
                            done_ratio = EXCLUDED.done_ratio,
                            updated_on = EXCLUDED.updated_on,
                            closed_on = EXCLUDED.closed_on,
                            sync_time = EXCLUDED.sync_time
                    ''', (
                        issue['id'],
                        issue['project']['id'],
                        issue['tracker']['id'],
                        issue['status']['id'],
                        issue.get('priority', {}).get('id'),
                        issue['author']['id'],
                        issue.get('assigned_to', {}).get('id'),
                        issue.get('parent', {}).get('id') if issue.get('parent') else None,
                        issue.get('subject', ''),
                        issue.get('description', ''),
                        issue.get('start_date'),
                        issue.get('due_date'),
                        issue.get('done_ratio', 0),
                        issue.get('estimated_hours'),
                        issue.get('spent_hours'),
                        issue['created_on'],
                        issue['updated_on'],
                        issue.get('closed_on'),
                        datetime.now()
                    ))
                    batch_inserted += 1
                except Exception as e:
                    print(f'Error syncing issue {issue.get("id")}: {e}')
            
            conn.commit()
            total_synced += len(issues)
            total_inserted += batch_inserted
            
            progress = (offset / total_count) * 100
            print(f'进度：{offset:,}/{total_count:,} ({progress:.1f}%) - 本批插入 {batch_inserted}/{len(issues)} 个')
            
            offset += batch_size
            
        except Exception as e:
            print(f'Error at offset {offset}: {e}')
            break
    
    # 验证 Issue 75002
    cur.execute('SELECT issue_id, project_id, status_id, subject FROM warehouse.ods_issues WHERE issue_id = 75002')
    result = cur.fetchone()
    if result:
        print(f'\n✅ Issue 75002 已同步：{result["subject"]} (状态 ID: {result["status_id"]})')
    else:
        print(f'\n❌ Issue 75002 仍未同步')
    
    # 验证总数
    cur.execute('SELECT COUNT(*) FROM warehouse.ods_issues')
    result = cur.fetchone()
    print(f'\n数据库现在有 {result[0]:,} 个 Issue')
    
    # 按状态统计
    cur.execute('''
        SELECT status_id, COUNT(*) as count
        FROM warehouse.ods_issues
        GROUP BY status_id
        ORDER BY status_id
    ''')
    print('\n按状态分布:')
    for row in cur.fetchall():
        print(f'  状态 {row[0]}: {row[1]:,} 个 Issue')
    
    cur.close()
    conn.close()
    
    print(f'\n同步完成！共同步 {total_synced:,} 个 Issue，新增 {total_inserted:,} 个')

if __name__ == '__main__':
    sync_all_issues()
