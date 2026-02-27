#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整解决方案 - 基于 Journals 和状态历史的完整分析
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from datetime import datetime

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

def analyze_project(project_id):
    """完整的项目分析"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print('='*80)
    print(f'项目 {project_id} 完整分析报告')
    print(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*80)
    
    # 1. 基本信息
    print('\n【1. 基本信息】')
    cur.execute('''
        SELECT 
            COUNT(*) as total_issues,
            MIN(created_on)::date as first_issue,
            MAX(created_on)::date as last_issue
        FROM warehouse.ods_issues 
        WHERE project_id = %s
    ''', (project_id,))
    result = cur.fetchone()
    print(f"Issue 总数：{result['total_issues']}")
    print(f"时间范围：{result['first_issue']} ~ {result['last_issue']}")
    
    # 2. 状态分布
    print('\n【2. 状态分布】')
    cur.execute('''
        SELECT 
            s.name as status_name,
            COUNT(i.issue_id) as count,
            ROUND(COUNT(i.issue_id) * 100.0 / (SELECT COUNT(*) FROM warehouse.ods_issues WHERE project_id = %s), 2) as percentage
        FROM warehouse.ods_issues i
        JOIN warehouse.ods_issue_statuses s ON i.status_id = s.status_id
        WHERE i.project_id = %s
        GROUP BY s.status_id, s.name
        ORDER BY count DESC
    ''', (project_id, project_id))
    print(f'{"状态":<15} {"数量":>10} {"占比":>10}')
    print('-'*40)
    for row in cur.fetchall():
        print(f'{row["status_name"]:<15} {row["count"]:>10} {row["percentage"]:>9.2f}%')
    
    # 3. Journals 统计
    print('\n【3. Journals 统计】')
    cur.execute('''
        SELECT COUNT(*) as journal_count FROM warehouse.ods_journals 
        WHERE issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s)
    ''', (project_id,))
    journal_count = cur.fetchone()['journal_count']
    
    cur.execute('''
        SELECT COUNT(*) as detail_count FROM warehouse.ods_journal_details 
        WHERE journal_id IN (
            SELECT journal_id FROM warehouse.ods_journals 
            WHERE issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s)
        )
    ''', (project_id,))
    detail_count = cur.fetchone()['detail_count']
    
    print(f"  Journals 总数：{journal_count:,}")
    print(f"  Details 总数：{detail_count:,}")
    print(f"  平均每个 Issue: {detail_count/max(1, cur.execute('SELECT COUNT(*) FROM warehouse.ods_issues WHERE project_id = %s', (project_id,)) or 1):.1f} 次变更")
    
    # 4. 基于 Journals 的角色分析
    print('\n【4. 基于 Journals 的实际工作量分析】')
    print('  分析逻辑：根据状态变更判断实际工作角色')
    print('  - 开发人员：将状态改为"已解决"（status_id=3）')
    print('  - 测试人员：将状态改为"已关闭"（status_id=5）')
    print('  - 实施人员：将状态从"新建"改为"进行中"（1→2）')
    
    cur.execute('''
        WITH status_changes AS (
            SELECT 
                jd.journal_id,
                j.issue_id,
                j.user_id,
                u.login as user_login,
                jd.old_value,
                jd.new_value,
                j.created_on
            FROM warehouse.ods_journal_details jd
            JOIN warehouse.ods_journals j ON jd.journal_id = j.journal_id
            JOIN warehouse.ods_users u ON j.user_id = u.user_id
            WHERE jd.name = 'status_id'
            AND j.issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s)
        ),
        developers AS (
            SELECT user_login, COUNT(DISTINCT issue_id) as resolved_count
            FROM status_changes
            WHERE new_value = '3'
            GROUP BY user_login
        ),
        testers AS (
            SELECT user_login, COUNT(DISTINCT issue_id) as closed_count
            FROM status_changes
            WHERE new_value = '5'
            GROUP BY user_login
        ),
        implementers AS (
            SELECT user_login, COUNT(DISTINCT issue_id) as started_count
            FROM status_changes
            WHERE old_value = '1' AND new_value = '2'
            GROUP BY user_login
        )
        SELECT 
            COALESCE(d.user_login, t.user_login, i.user_login) as user_login,
            COALESCE(d.resolved_count, 0) as developer_work,
            COALESCE(t.closed_count, 0) as tester_work,
            COALESCE(i.started_count, 0) as implementer_work,
            COALESCE(d.resolved_count, 0) + COALESCE(t.closed_count, 0) + COALESCE(i.started_count, 0) as total_work
        FROM developers d
        FULL OUTER JOIN testers t ON d.user_login = t.user_login
        FULL OUTER JOIN implementers i ON COALESCE(d.user_login, t.user_login) = i.user_login
        ORDER BY total_work DESC
        LIMIT 15
    ''', (project_id,))
    
    print(f'\n  TOP 15 成员工作量:')
    print(f'  {"成员":<20} {"开发":>8} {"测试":>8} {"实施":>8} {"总计":>8}')
    print('  ' + '-'*60)
    for row in cur.fetchall():
        print(f'  {row["user_login"]:<20} {row["developer_work"]:>8} {row["tester_work"]:>8} {row["implementer_work"]:>8} {row["total_work"]:>8}')
    
    # 5. 状态耗时分析
    print('\n【5. 状态耗时分析】')
    cur.execute('''
        SELECT 
            sh.status_name,
            COUNT(*) as issue_count,
            ROUND(AVG(sh.duration_hours), 2) as avg_hours,
            ROUND(MIN(sh.duration_hours), 2) as min_hours,
            ROUND(MAX(sh.duration_hours), 2) as max_hours
        FROM warehouse.ods_issue_status_history sh
        WHERE sh.issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s)
        AND sh.duration_hours IS NOT NULL
        GROUP BY sh.status_id, sh.status_name
        ORDER BY avg_hours DESC
    ''', (project_id,))
    
    print(f'  {"状态":<15} {"样本数":>8} {"平均耗时":>12} {"最短":>10} {"最长":>10}')
    print('  ' + '-'*60)
    for row in cur.fetchall():
        avg_hours = row['avg_hours'] or 0
        if avg_hours < 24:
            avg_str = f'{avg_hours:.1f}小时'
        elif avg_hours < 168:
            avg_str = f'{avg_hours/24:.1f}天'
        else:
            avg_str = f'{avg_hours/168:.1f}周'
        print(f'  {row["status_name"]:<15} {row["issue_count"]:>8} {avg_str:>12} {row["min_hours"]:>8.1f}h {row["max_hours"]:>8.1f}h')
    
    # 6. 整体周期分析
    print('\n【6. 整体周期分析】')
    cur.execute('''
        SELECT 
            ROUND(AVG(total_duration_hours), 2) as avg_total,
            ROUND(MIN(total_duration_hours), 2) as min_total,
            ROUND(MAX(total_duration_hours), 2) as max_total,
            COUNT(*) as completed_count
        FROM (
            SELECT 
                issue_id,
                SUM(duration_hours) as total_duration_hours
            FROM warehouse.ods_issue_status_history
            WHERE issue_id IN (SELECT issue_id FROM warehouse.ods_issues WHERE project_id = %s AND status_id = 5)
            GROUP BY issue_id
        ) t
    ''', (project_id,))
    result = cur.fetchone()
    
    if result['avg_total']:
        avg_total = result['avg_total']
        if avg_total < 24:
            avg_str = f'{avg_total:.1f}小时'
        elif avg_total < 168:
            avg_str = f'{avg_total/24:.1f}天'
        else:
            avg_str = f'{avg_total/168:.1f}周'
        
        print(f'  已完成 Issue 数：{result["completed_count"]}')
        print(f'  平均周期：{avg_str}')
        print(f'  最短周期：{result["min_total"]:.1f}小时')
        print(f'  最长周期：{result["max_total"]:.1f}小时')
    
    # 7. 月度趋势
    print('\n【7. 月度趋势】')
    cur.execute('''
        SELECT 
            TO_CHAR(i.created_on, 'YYYY-MM') as month,
            COUNT(i.issue_id) as new_issues,
            COUNT(CASE WHEN i.status_id = 5 THEN 1 END) as closed_issues
        FROM warehouse.ods_issues i
        WHERE i.project_id = %s
        GROUP BY TO_CHAR(i.created_on, 'YYYY-MM')
        ORDER BY month
    ''', (project_id,))
    
    print(f'  {"月份":<10} {"新建":>10} {"关闭":>10} {"净增":>10}')
    print('  ' + '-'*45)
    for row in cur.fetchall():
        net = row['new_issues'] - row['closed_issues']
        net_str = f'+{net}' if net >= 0 else str(net)
        print(f'  {row["month"]:<10} {row["new_issues"]:>10} {row["closed_issues"]:>10} {net_str:>10}')
    
    cur.close()
    conn.close()
    
    print('\n' + '='*80)
    print('✅ 分析完成！')
    print('='*80)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'用法：python3 {sys.argv[0]} <project_id>')
        sys.exit(1)
    
    project_id = int(sys.argv[1])
    analyze_project(project_id)
