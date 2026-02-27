#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整解决方案 - 同步 Issues + Journals + 状态历史
"""

import requests
import psycopg2
from datetime import datetime
from psycopg2.extras import RealDictCursor
import sys
import time

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

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)

def sync_issues(project_id):
    """同步项目所有 Issue"""
    print('='*70)
    print(f'阶段 1: 同步项目 {project_id} 的所有 Issue')
    print('='*70)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 获取总数量
    resp = requests.get(
        f'{REDMINE_URL}/issues.json',
        headers=HEADERS,
        params={'project_id': project_id, 'status_id': '*', 'limit': 1},
        timeout=30
    )
    total_count = resp.json().get('total_count', 0)
    print(f'Redmine 总 Issue 数：{total_count:,}')
    
    batch_size = 100
    offset = 0
    total_inserted = 0
    
    while offset < total_count:
        resp = requests.get(
            f'{REDMINE_URL}/issues.json',
            headers=HEADERS,
            params={'project_id': project_id, 'status_id': '*', 'offset': offset, 'limit': batch_size},
            timeout=120
        )
        data = resp.json()
        issues = data.get('issues', [])
        
        if not issues:
            break
        
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
                        status_id = EXCLUDED.status_id,
                        assigned_to_id = EXCLUDED.assigned_to_id,
                        updated_on = EXCLUDED.updated_on,
                        sync_time = EXCLUDED.sync_time
                ''', (
                    issue['id'], issue['project']['id'], issue['tracker']['id'],
                    issue['status']['id'], issue.get('priority', {}).get('id'),
                    issue['author']['id'], issue.get('assigned_to', {}).get('id'),
                    issue.get('parent', {}).get('id') if issue.get('parent') else None,
                    issue.get('subject', ''), issue.get('description', ''),
                    issue.get('start_date'), issue.get('due_date'),
                    issue.get('done_ratio', 0), issue.get('estimated_hours'),
                    issue.get('spent_hours'), issue['created_on'],
                    issue['updated_on'], issue.get('closed_on'), datetime.now()
                ))
                total_inserted += 1
            except Exception as e:
                pass
        
        conn.commit()
        offset += batch_size
        print(f'进度：{offset:,}/{total_count:,} ({offset*100/total_count:.1f}%)')
    
    cur.close()
    conn.close()
    print(f'✅ Issue 同步完成！新增 {total_inserted:,} 个\n')
    return total_inserted

def sync_journals(project_id):
    """同步所有 Issue 的 Journals"""
    print('='*70)
    print(f'阶段 2: 同步项目 {project_id} 所有 Issue 的 Journals')
    print('='*70)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s ORDER BY issue_id', (project_id,))
    issue_ids = [row[0] for row in cur.fetchall()]
    total_issues = len(issue_ids)
    
    print(f'项目 {project_id} 共有 {total_issues} 个 Issue')
    
    total_journals = 0
    total_details = 0
    
    for i, issue_id in enumerate(issue_ids, 1):
        try:
            resp = requests.get(
                f'{REDMINE_URL}/issues/{issue_id}.json',
                headers=HEADERS,
                params={'include': 'journals'},
                timeout=30
            )
            
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            issue = data.get('issue', {})
            journals = issue.get('journals', [])
            
            if not journals:
                continue
            
            for journal in journals:
                journal_id = journal['id']
                user_id = journal['user']['id']
                notes = journal.get('notes', '')
                created_on = journal['created_on']
                
                try:
                    cur.execute('''
                        INSERT INTO warehouse.ods_journals (
                            journal_id, issue_id, user_id, notes, created_on, sync_time
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (journal_id, issue_id, user_id, notes, created_on, datetime.now()))
                    total_journals += 1
                except psycopg2.errors.UniqueViolation:
                    pass
                
                details = journal.get('details', [])
                for detail in details:
                    try:
                        cur.execute('''
                            INSERT INTO warehouse.ods_journal_details (
                                journal_id, property, name, old_value, new_value, sync_time
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (
                            journal_id,
                            detail.get('property', 'attr'),
                            detail.get('name', ''),
                            str(detail.get('old_value', '')) if detail.get('old_value') is not None else None,
                            str(detail.get('new_value', '')) if detail.get('new_value') is not None else None,
                            datetime.now()
                        ))
                        total_details += 1
                    except:
                        pass
            
            conn.commit()
            
            if i % 10 == 0 or i == total_issues:
                print(f'进度：{i}/{total_issues} ({i*100/total_issues:.1f}%) - Journals: {total_journals}, Details: {total_details}')
            
            time.sleep(0.2)
            
        except Exception as e:
            continue
    
    cur.execute('SELECT COUNT(*) FROM warehouse.ods_journals WHERE issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s)', (project_id,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    print(f'\n✅ Journals 同步完成！')
    print(f'  本次新增：{total_journals:,} Journals, {total_details:,} Details')
    print(f'  数据库总计：{result[0]:,}\n')
    return total_journals, total_details

def build_status_history(project_id):
    """从 Journals 构建状态历史"""
    print('='*70)
    print(f'阶段 3: 构建项目 {project_id} 的状态历史')
    print('='*70)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 获取所有状态变更
    cur.execute('''
        SELECT 
            j.issue_id,
            j.journal_id,
            j.user_id,
            u.login as changed_by_login,
            jd.old_value,
            jd.new_value,
            j.created_on
        FROM warehouse.ods_journal_details jd
        JOIN warehouse.ods_journals j ON jd.journal_id = j.journal_id
        JOIN warehouse.ods_users u ON j.user_id = u.user_id
        WHERE jd.name = 'status_id'
        AND j.issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s)
        ORDER BY j.issue_id, j.created_on
    ''', (project_id,))
    
    status_changes = cur.fetchall()
    
    # 获取状态名称映射
    cur.execute('SELECT status_id, name FROM warehouse.ods_issue_statuses')
    status_map = {row['status_id']: row['name'] for row in cur.fetchall()}
    
    # 按 Issue 分组
    issues_dict = {}
    for change in status_changes:
        issue_id = change['issue_id']
        if issue_id not in issues_dict:
            issues_dict[issue_id] = []
        issues_dict[issue_id].append(change)
    
    # 构建状态历史
    total_records = 0
    for issue_id, changes in issues_dict.items():
        # 添加初始状态（Issue 创建时）
        cur.execute('SELECT status_id, created_on FROM warehouse.ods_issues WHERE issue_id = %s', (issue_id,))
        issue_info = cur.fetchone()
        
        if issue_info:
            initial_status = issue_info['status_id']
            created_time = issue_info['created_on']
            
            try:
                cur.execute('''
                    INSERT INTO warehouse.ods_issue_status_history (
                        issue_id, status_id, status_name, started_at, ended_at,
                        duration_hours, changed_by_user_id, changed_by_login, journal_id
                    ) VALUES (%s, %s, %s, %s, NULL, NULL, NULL, NULL, NULL)
                ''', (issue_id, initial_status, status_map.get(initial_status, ''), created_time))
                total_records += 1
            except:
                pass
        
        # 处理每个状态变更
        for i, change in enumerate(changes):
            status_id = int(change['new_value'])
            started_at = change['created_on']
            
            # 计算上一个状态的结束时间
            if i > 0:
                prev_change = changes[i-1]
                prev_status = int(prev_change['new_value'])
                
                try:
                    cur.execute('''
                        UPDATE warehouse.ods_issue_status_history
                        SET ended_at = %s,
                            duration_hours = EXTRACT(EPOCH FROM (%s - started_at)) / 3600
                        WHERE issue_id = %s AND status_id = %s AND ended_at IS NULL
                    ''', (started_at, started_at, issue_id, prev_status))
                except:
                    pass
            
            # 插入新状态
            try:
                cur.execute('''
                    INSERT INTO warehouse.ods_issue_status_history (
                        issue_id, status_id, status_name, started_at, ended_at,
                        duration_hours, changed_by_user_id, changed_by_login, journal_id
                    ) VALUES (%s, %s, %s, %s, NULL, NULL, %s, %s, %s)
                ''', (
                    issue_id, status_id, status_map.get(status_id, ''), started_at,
                    change['user_id'], change['changed_by_login'], change['journal_id']
                ))
                total_records += 1
            except:
                pass
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f'✅ 状态历史构建完成！')
    print(f'  新增记录：{total_records:,}')
    print(f'  涉及 Issue：{len(issues_dict):,}\n')
    return total_records

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'用法：python3 {sys.argv[0]} <project_id>')
        sys.exit(1)
    
    project_id = int(sys.argv[1])
    
    sync_issues(project_id)
    sync_journals(project_id)
    build_status_history(project_id)
    
    print('='*70)
    print('✅ 完整同步完成！可以开始分析')
    print('='*70)
