#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析所有历史 Issue 的开发/测试人员
纯代码逻辑判断，零 Token 消耗！
"""

import os, sys, json, requests, psycopg2, time
from datetime import date
from typing import Set, Tuple, Optional

# Config
REDMINE_URL = 'http://redmine.fa-software.com'
REDMINE_API_KEY = 'adabb6a1089a5ac90e5649f505029d28e1cc9bc7'
HEADERS = {'X-Redmine-API-Key': REDMINE_API_KEY}
RESOLVED_STATUS_ID = 3

def get_db_connection():
    return psycopg2.connect(host='warehouse-db', database='redmine_warehouse', user='redmine_warehouse', password='WarehouseP@ss2026')

def load_dev_team() -> Set[str]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_name FROM dev_team_members WHERE is_active = true")
    members = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return members

def get_all_resolved_issues() -> list:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT issue_id, project_id FROM warehouse.issue_daily_snapshot WHERE status_id = %s ORDER BY issue_id", (RESOLVED_STATUS_ID,))
    issues = [(row[0], row[1]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return issues

def get_issue_with_journals(issue_id: int) -> Optional[Tuple[dict, list]]:
    try:
        resp = requests.get(f"{REDMINE_URL}/issues/{issue_id}.json", headers=HEADERS, params={"include": "journals"}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            issue = data.get('issue', {})
            journals = issue.get('journals', [])
            return issue, journals
    except Exception as e:
        print(f"  Error fetching {issue_id}: {e}")
    return None, []

def identify_dev_tester(issue: dict, journals: list, dev_team: Set[str]) -> Tuple[str, str]:
    if not journals:
        return issue.get('author', {}).get('name', 'Unknown'), 'Unassigned'
    
    sorted_journals = sorted(journals, key=lambda j: j.get('created_on', ''))
    resolver = None
    for journal in sorted_journals:
        for detail in journal.get('details', []):
            if detail.get('name') == 'status_id' and str(detail.get('new_value', '')) == str(RESOLVED_STATUS_ID):
                resolver = journal.get('user', {}).get('name', 'Unknown')
                break
        if resolver:
            break
    
    if not resolver:
        resolver = sorted_journals[-1].get('user', {}).get('name', 'Unknown')
    
    if resolver in dev_team:
        developer = resolver
        tester = issue.get('assigned_to', {}).get('name', 'Unassigned') if issue.get('assigned_to') else 'Unassigned'
    else:
        tester = resolver
        developer = 'Unknown'
        for journal in sorted_journals:
            for detail in journal.get('details', []):
                if detail.get('name') == 'status_id' and str(detail.get('new_value', '')) == '7':
                    developer = journal.get('user', {}).get('name', 'Unknown')
                    break
            if developer != 'Unknown':
                break
        if developer == 'Unknown':
            developer = issue.get('author', {}).get('name', 'Unknown')
    
    return developer, tester

def save_analysis(issue_id, project_id, developer, tester):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        today = date.today()
        cur.execute("SELECT id FROM dev_test_analysis WHERE issue_id = %s AND analyzed_at = %s", (issue_id, today))
        if cur.fetchone():
            cur.execute("UPDATE dev_test_analysis SET developer_name = %s, tester_name = %s WHERE issue_id = %s AND analyzed_at = %s", (developer, tester, issue_id, today))
        else:
            cur.execute("INSERT INTO dev_test_analysis (issue_id, project_id, developer_name, tester_name, analyzed_at) VALUES (%s, %s, %s, %s, %s)", (issue_id, project_id, developer, tester, today))
        conn.commit()
    except Exception as e:
        print(f"Error {issue_id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def print_summary():
    conn = get_db_connection()
    cur = conn.cursor()
    print("")
    print("=" * 70)
    print("📈 分析结果汇总")
    print("=" * 70)
    
    cur.execute("SELECT COUNT(*) FROM dev_test_analysis WHERE analyzed_at = CURRENT_DATE")
    total = cur.fetchone()[0]
    print(f"本次分析：{total} 个 Issue")
    
    cur.execute("SELECT developer_name, COUNT(*) as cnt FROM dev_test_analysis WHERE analyzed_at = CURRENT_DATE GROUP BY developer_name ORDER BY cnt DESC LIMIT 5")
    print("")
    print("👨‍💻 TOP 开发人员:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} 个")
    
    cur.execute("SELECT tester_name, COUNT(*) as cnt FROM dev_test_analysis WHERE analyzed_at = CURRENT_DATE GROUP BY tester_name ORDER BY cnt DESC LIMIT 5")
    print("")
    print("🧪 TOP 测试人员:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} 个")
    
    cur.close()
    conn.close()
    print("=" * 70)

# Main
if __name__ == "__main__":
    print("=" * 70)
    print("📊 批量分析历史 Issue (纯代码逻辑)")
    print("=" * 70)
    
    dev_team = load_dev_team()
    print(f"✅ Loaded {len(dev_team)} dev team members")
    
    issues = get_all_resolved_issues()
    print(f"📊 Total: {len(issues)} issues")
    print(f"💰 Token cost: ¥0")
    print("")
    
    analyzed = 0
    errors = 0
    for i, (issue_id, project_id) in enumerate(issues):
        issue, journals = get_issue_with_journals(issue_id)
        if not issue:
            errors += 1
            continue
        dev, tester = identify_dev_tester(issue, journals, dev_team)
        save_analysis(issue_id, project_id, dev, tester)
        analyzed += 1
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{len(issues)}")
        time.sleep(0.3)
    
    print_summary()
    print(f"\n✅ Done! Analyzed: {analyzed}, Errors: {errors}")
