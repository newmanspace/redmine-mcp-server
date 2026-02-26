#!/usr/bin/env python3
"""
Manual sync script for Redmine warehouse
Usage: python manual-sync.py [project_id]
"""

import os
import sys
import requests
from datetime import date

sys.path.insert(0, '/docker/redmine-mcp-server/src')
from redmine_mcp_server.redmine_warehouse import DataWarehouse

REDMINE_URL = os.getenv("REDMINE_URL", "http://redmine.fa-software.com")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

def sync_project(project_id: int):
    """Sync all issues for a project"""
    print(f"\n{'='*60}")
    print(f"Syncing Project ID: {project_id}")
    print(f"{'='*60}")
    
    warehouse = DataWarehouse()
    today = date.today()
    
    # Fetch all issues from Redmine API
    api_url = f"{REDMINE_URL}/issues.json"
    headers = {"X-Redmine-API-Key": REDMINE_API_KEY}
    
    all_issues = []
    offset = 0
    limit = 100
    
    print(f"Fetching issues from Redmine API...")
    while True:
        try:
            resp = requests.get(
                api_url,
                headers=headers,
                params={'project_id': project_id, 'status_id': '*', 'limit': limit, 'offset': offset},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            print(f"  Fetched {len(all_issues)} issues (offset: {offset})")
            
            if len(issues) < limit:
                break
            
            offset += limit
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    print(f"Total issues fetched: {len(all_issues)}")
    
    # Get yesterday's snapshot for comparison
    yesterday = today.__sub__(__import__('datetime').timedelta(days=1))
    try:
        previous_issues = warehouse.get_issues_snapshot(project_id, yesterday)
        previous_map = {i['issue_id']: i for i in previous_issues}
        print(f"Previous day snapshots: {len(previous_map)}")
    except Exception as e:
        print(f"  No previous snapshot: {e}")
        previous_map = {}
    
    # Upsert to warehouse
    print(f"Upserting to warehouse...")
    warehouse.upsert_issues_batch(project_id, all_issues, today, previous_map)
    print(f"✅ Sync complete for project {project_id}")
    
    # Verify
    count = warehouse.get_issues_snapshot(project_id, today)
    print(f"   Total snapshots in DB: {len(count)}")
    
    warehouse.close()
    return len(all_issues)

if __name__ == "__main__":
    projects = [341, 372]  # 新顺 CIM + 上海工研院 MES
    
    if len(sys.argv) > 1:
        projects = [int(sys.argv[1])]
    
    total = 0
    for pid in projects:
        total += sync_project(pid)
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total} issues synced")
    print(f"{'='*60}")
