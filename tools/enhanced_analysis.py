#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强分析 - 同时展示定义角色和实际工作
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DB_CONFIG = {
    'host': 'warehouse-db',
    'port': '5432',
    'dbname': 'redmine_warehouse',
    'user': 'redmine_warehouse',
    'password': 'WarehouseP@ss2026'
}

def analyze_project(project_id):
    """完整的项目分析（包含定义角色和实际工作）"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print('='*90)
    print(f'项目 {project_id} 完整分析报告（增强版）')
    print('='*90)
    
    # 1. 基本信息
    print(f'\n【1. 基本信息】')
    cur.execute('SELECT COUNT(*) as total FROM warehouse.ods_issues WHERE project_id = %s', (project_id,))
    print(f"Issue 总数：{cur.fetchone()['total']}")
    
    # 2. Project Members 角色定义
    print(f'\n【2. Project Members 角色定义】')
    print('  数据来源：warehouse.ods_project_memberships')
    cur.execute(f'''
        SELECT 
            u.login,
            u.firstname || ' ' || u.lastname as name,
            STRING_AGG(r.name, ', ') as roles
        FROM warehouse.ods_project_memberships pm
        JOIN warehouse.ods_users u ON pm.user_id = u.user_id
        JOIN warehouse.ods_project_member_roles mr ON pm.membership_id = mr.membership_id
        JOIN warehouse.ods_roles r ON mr.role_id = r.role_id
        WHERE pm.project_id = {project_id}
        GROUP BY pm.user_id, u.login, u.firstname, u.lastname
        ORDER BY u.login
    ''')
    
    print(f'\n  {"成员":<20} {"姓名":<15} {"角色定义":<50}')
    print('  ' + '-'*85)
    for row in cur.fetchall():
        print(f'  {row["login"]:<20} {row["name"]:<15} {row["roles"]:<50}')
    
    # 3. 基于 Journals 的实际工作
    print(f'\n【3. 基于 Journals 的实际工作】')
    print('  分析逻辑：根据状态变更判断实际工作内容')
    print('  - 开发工作：将状态改为"已解决"（status_id=3）')
    print('  - 测试工作：将状态改为"已关闭"（status_id=5）')
    print('  - 启动工作：将状态从"新建"改为"进行中"（1→2）')
    
    cur.execute(f'''
        WITH status_changes AS (
            SELECT 
                j.issue_id,
                j.user_id,
                u.login as user_login,
                jd.old_value,
                jd.new_value
            FROM warehouse.ods_journal_details jd
            JOIN warehouse.ods_journals j ON jd.journal_id = j.journal_id
            JOIN warehouse.ods_users u ON j.user_id = u.user_id
            WHERE jd.name = 'status_id'
            AND j.issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = {project_id})
        ),
        dev_work AS (
            SELECT user_login, COUNT(DISTINCT issue_id) as dev_count
            FROM status_changes
            WHERE new_value = '3'
            GROUP BY user_login
        ),
        test_work AS (
            SELECT user_login, COUNT(DISTINCT issue_id) as test_count
            FROM status_changes
            WHERE new_value = '5'
            GROUP BY user_login
        ),
        start_work AS (
            SELECT user_login, COUNT(DISTINCT issue_id) as start_count
            FROM status_changes
            WHERE old_value = '1' AND new_value = '2'
            GROUP BY user_login
        )
        SELECT 
            COALESCE(d.user_login, t.user_login, s.user_login) as user_login,
            COALESCE(d.dev_count, 0) as dev_work,
            COALESCE(t.test_count, 0) as test_work,
            COALESCE(s.start_count, 0) as start_work,
            COALESCE(d.dev_count, 0) + COALESCE(t.test_count, 0) + COALESCE(s.start_count, 0) as total_work
        FROM dev_work d
        FULL OUTER JOIN test_work t ON d.user_login = t.user_login
        FULL OUTER JOIN start_work s ON COALESCE(d.user_login, t.user_login) = s.user_login
        ORDER BY total_work DESC
        LIMIT 15
    ''')
    
    print(f'\n  TOP 15 成员实际工作量:')
    print(f'  {"成员":<20} {"开发":>8} {"测试":>8} {"启动":>8} {"总计":>8}')
    print('  ' + '-'*70)
    for row in cur.fetchall():
        print(f'  {row["user_login"]:<20} {row["dev_work"]:>8} {row["test_work"]:>8} {row["start_work"]:>8} {row["total_work"]:>8}')
    
    # 4. 角色对比分析
    print(f'\n【4. 角色定义 vs 实际工作对比】')
    print('  对比 Project Members 角色定义和 Journals 实际工作')
    
    cur.execute(f'''
        WITH member_roles AS (
            SELECT 
                u.login,
                STRING_AGG(r.name, ', ') as roles
            FROM warehouse.ods_project_memberships pm
            JOIN warehouse.ods_users u ON pm.user_id = u.user_id
            JOIN warehouse.ods_project_member_roles mr ON pm.membership_id = mr.membership_id
            JOIN warehouse.ods_roles r ON mr.role_id = r.role_id
            WHERE pm.project_id = {project_id}
            GROUP BY pm.user_id, u.login
        ),
        actual_work AS (
            SELECT 
                j.user_id,
                u.login as user_login,
                COUNT(DISTINCT CASE WHEN jd.new_value = '3' THEN j.issue_id END) as dev_count,
                COUNT(DISTINCT CASE WHEN jd.new_value = '5' THEN j.issue_id END) as test_count,
                COUNT(DISTINCT CASE WHEN jd.old_value = '1' AND jd.new_value = '2' THEN j.issue_id END) as start_count
            FROM warehouse.ods_journal_details jd
            JOIN warehouse.ods_journals j ON jd.journal_id = j.journal_id
            JOIN warehouse.ods_users u ON j.user_id = u.user_id
            WHERE jd.name = 'status_id'
            AND j.issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = {project_id})
            GROUP BY j.user_id, u.login
        )
        SELECT 
            mr.login,
            mr.roles as defined_roles,
            COALESCE(aw.dev_count, 0) as dev_work,
            COALESCE(aw.test_count, 0) as test_work,
            COALESCE(aw.start_count, 0) as start_work,
            COALESCE(aw.dev_count, 0) + COALESCE(aw.test_count, 0) + COALESCE(aw.start_count, 0) as total_work
        FROM member_roles mr
        LEFT JOIN actual_work aw ON mr.login = aw.user_login
        ORDER BY total_work DESC
    ''')
    
    print(f'\n  {"成员":<20} {"角色定义":<50} {"开发":>6} {"测试":>6} {"启动":>6} {"总计":>6}')
    print('  ' + '-'*95)
    for row in cur.fetchall():
        print(f'  {row["login"]:<20} {row["defined_roles"]:<50} {row["dev_work"]:>6} {row["test_work"]:>6} {row["start_work"]:>6} {row["total_work"]:>6}')
    
    print(f'\n  说明：')
    print(f'  - 角色定义：来自 Project Members 配置')
    print(f'  - 开发工作：将状态改为"已解决"的人数')
    print(f'  - 测试工作：将状态改为"已关闭"的人数')
    print(f'  - 启动工作：将状态从"新建"改为"进行中"的人数')
    print(f'  - 曾聚的例子：角色定义是"开发人员"，但实际工作以"启动"为主（20 次）')
    
    cur.close()
    conn.close()
    
    print('\n' + '='*90)
    print('✅ 分析完成！')
    print('='*90)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'用法：python3 {sys.argv[0]} <project_id>')
        sys.exit(1)
    
    project_id = int(sys.argv[1])
    analyze_project(project_id)
