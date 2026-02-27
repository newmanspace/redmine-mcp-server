#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析所有历史 Issue 的开发/测试人员
Estimated: ~782K tokens, ~¥1.56 cost, 10-15 minutes
"""

import os
import sys
import json
import requests
import psycopg2
from datetime import datetime
from typing import List, Dict, Set, Tuple

# Config
REDMINE_URL = os.getenv("REDMINE_URL", "http://redmine.fa-software.com")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")
DB_HOST = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
DB_NAME = "redmine_warehouse"
DB_USER = "redmine_warehouse"
DB_PASS = "WarehouseP@ss2026"
DB_PORT = "5432"

HEADERS = {"X-Redmine-API-Key": REDMINE_API_KEY}
RESOLVED_STATUS_ID = 3
BATCH_SIZE = 100  # Process in batches to avoid timeout

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
    )

def load_dev_team() -> Set[str]:
    """Load developer team members from warehouse"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_name FROM dev_team_members WHERE is_active = true")
    members = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()
    print(f"✅ Loaded {len(members)} developer team members")
    return members

def get_resolved_issues_from_warehouse() -> List[Tuple[int, int]]:
    """Get all issues that were ever resolved from warehouse snapshots"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT issue_id, project_id 
        FROM issue_daily_snapshot 
        WHERE status_id = %s
        ORDER BY issue_id
    """, (RESOLVED_STATUS_ID,))
    issues = [(row[0], row[1]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    print(f"📊 Found {len(issues)} issues that were resolved")
    return issues

def get_issue_journals(issue_id: int) -> Tuple[Dict, List[Dict]]:
    """Get issue data and journals"""
    try:
        resp = requests.get(
            f"{REDMINE_URL}/issues/{issue_id}.json",
            headers=HEADERS,
            params={"include": "journals"},
            timeout=30
        )
        if resp.status_code != 200:
            return None, []
        data = resp.json()
        issue = data.get('issue', {})
        journals = issue.get('journals', [])
        return issue, journals
    except Exception as e:
        print(f"  Error fetching issue {issue_id}: {e}")
        return None, []

def identify_dev_tester(issue: Dict, journals: List[Dict], dev_team: Set[str]) -> Tuple[str, str]:
    """Identify developer and tester from journals"""
    if not journals:
        author = issue.get('author', {}).get('name', 'Unknown')
        assignee = issue.get('assigned_to', {}).get('name', 'Unassigned') if issue.get('assigned_to') else 'Unassigned'
        return author, assignee
    
    sorted_journals = sorted(journals, key=lambda j: j.get('created_on', ''))
    
    # Find person who changed status to resolved
    resolver = None
    for journal in sorted_journals:
        details = journal.get('details', [])
        for detail in details:
            if detail.get('name') == 'status_id' and str(detail.get('new_value', '')) == str(RESOLVED_STATUS_ID):
                resolver = journal.get('user', {}).get('name', 'Unknown')
                break
        if resolver:
            break
    
    if not resolver:
        resolver = sorted_journals[-1].get('user', {}).get('name', 'Unknown') if sorted_journals else 'Unknown'
    
    # Classify based on team membership
    if resolver in dev_team:
        developer = resolver
        tester = issue.get('assigned_to', {}).get('name', 'Unassigned') if issue.get('assigned_to') else 'Unassigned'
    else:
        # Resolver is tester, find developer from earlier journal (status changed to 测试中)
        developer = 'Unknown'
        for journal in sorted_journals:
            details = journal.get('details', [])
            for detail in details:
                if detail.get('name') == 'status_id' and str(detail.get('new_value', '')) == '7':  # 测试中
                    developer = journal.get('user', {}).get('name', 'Unknown')
                    break
            if developer != 'Unknown':
                break
        
        if developer == 'Unknown':
            developer = issue.get('author', {}).get('name', 'Unknown')
        
        tester = resolver
    
    return developer, tester

def save_analysis(issue_id: int, project_id: int, developer: str, tester: str):
    """Save analysis result to warehouse"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO dev_test_analysis (issue_id, project_id, developer_name, tester_name, analyzed_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (issue_id, CURRENT_DATE) DO UPDATE SET
                developer_name = EXCLUDED.developer_name,
                tester_name = EXCLUDED.tester_name,
                analyzed_at = CURRENT_TIMESTAMP
        """, (issue_id, project_id, developer, tester))
        conn.commit()
    except Exception as e:
        print(f"  Error saving analysis for issue {issue_id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def generate_summary():
    """Generate summary report from analysis results"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("")
    print("=" * 70)
    print("📈 分析结果汇总")
    print("=" * 70)
    
    # Total analyzed
    cur.execute("SELECT COUNT(*) FROM dev_test_analysis WHERE analyzed_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'")
    total = cur.fetchone()[0]
    print(f"本次分析：{total} 个 Issue")
    
    # Developer stats
    cur.execute("""
        SELECT developer_name, COUNT(*) as cnt 
        FROM dev_test_analysis 
        WHERE analyzed_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
        GROUP BY developer_name 
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    print("")
    print("👨‍💻 TOP 开发人员:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} 个")
    
    # Tester stats
    cur.execute("""
        SELECT tester_name, COUNT(*) as cnt 
        FROM dev_test_analysis 
        WHERE analyzed_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
        GROUP BY tester_name 
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    print("")
    print("🧪 TOP 测试人员:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} 个")
    
    cur.close()
    conn.close()
    print("=" * 70)

def main():
    print("=" * 70)
    print("📊 批量分析所有历史 Issue")
    print("=" * 70)
    print("")
    
    # Load dev team
    dev_team = load_dev_team()
    
    # Get issues to analyze
    issues = get_resolved_issues_from_warehouse()
    total = len(issues)
    
    print(f"")
    print(f"📊 分析规模:")
    print(f"  总 Issue 数：{total}")
    print(f"  预估 tokens: ~{total * 460:,}")
    print(f"  预估成本：~¥{total * 460 / 1000 * 0.002:.2f}")
    print(f"  预计耗时：10-15 分钟")
    print(f"")
    
    # Analyze each issue
    analyzed = 0
    errors = 0
    
    for i, (issue_id, project_id) in enumerate(issues):
        if (i + 1) % 100 == 0:
            print(f"⏳ 进度：{i+1}/{total} ({(i+1)/total*100:.1f}%)")
        
        issue, journals = get_issue_journals(issue_id)
        if not issue:
            errors += 1
            continue
        
        developer, tester = identify_dev_tester(issue, journals, dev_team)
        save_analysis(issue_id, project_id, developer, tester)
        analyzed += 1
    
    # Generate summary
    generate_summary()
    
    print("")
    print(f"✅ 分析完成!")
    print(f"  成功：{analyzed}")
    print(f"  失败：{errors}")
    print("=" * 70)

if __name__ == "__main__":
    main()
