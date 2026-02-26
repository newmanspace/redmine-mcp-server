#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev/Test Workload Analyzer - CORRECTED VERSION

Corrected Logic:
- Developer: Person who changes issue status TO "测试中" (ready for testing)
- Tester: Person who changes issue status FROM "测试中" TO "已解决" (testing completed)

Status Flow:
新建 (1) → 进行中 (2) → 代码审查 (10) → 测试中 (7) → 已解决 (3) → 已关闭 (5)
                                    ↑              ↑
                                开发人员        测试人员
"""

import logging
import requests
import os
from typing import Dict, List, Optional, Tuple

REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

logger = logging.getLogger(__name__)

class DevTestAnalyzer:
    def __init__(self):
        self.base_url = REDMINE_URL
        self.api_key = REDMINE_API_KEY
        self.headers = {"X-Redmine-API-Key": self.api_key}
        self.status_testing_id = 7    # "测试中"
        self.status_resolved_id = 3   # "已解决"
        
    def analyze_project(self, project_id: int) -> Dict:
        """Analyze developer/tester workload for a project"""
        logger.info(f"Analyzing dev/test workload for project {project_id}")
        
        try:
            issues = self._get_resolved_issues(project_id)
            logger.info(f"Found {len(issues)} resolved issues")
        except Exception as e:
            logger.error(f"Failed to get resolved issues: {e}")
            return {"developers": {}, "testers": {}, "collaborations": {}, "total_issues": 0, "error": str(e)}
        
        if not issues:
            return {"developers": {}, "testers": {}, "collaborations": {}, "total_issues": 0}
        
        developers = {}
        testers = {}
        collaborations = {}
        
        for i, issue in enumerate(issues):
            if i % 50 == 0:
                logger.info(f"Processing issue {i+1}/{len(issues)}")
            
            issue_id = issue['id']
            
            try:
                journals = self._get_issue_journals(issue_id)
                dev_name, tester_name = self._identify_dev_tester(journals, issue)
                
                if dev_name:
                    if dev_name not in developers:
                        developers[dev_name] = {"resolved_count": 0, "issues": []}
                    developers[dev_name]["resolved_count"] += 1
                    developers[dev_name]["issues"].append(issue_id)
                
                if tester_name:
                    if tester_name not in testers:
                        testers[tester_name] = {"test_count": 0, "issues": []}
                    testers[tester_name]["test_count"] += 1
                    testers[tester_name]["issues"].append(issue_id)
                
                if dev_name and tester_name:
                    key = f"{dev_name} → {tester_name}"
                    if key not in collaborations:
                        collaborations[key] = {"count": 0, "issues": []}
                    collaborations[key]["count"] += 1
                    collaborations[key]["issues"].append(issue_id)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze issue {issue_id}: {e}")
                continue
        
        return {"developers": developers, "testers": testers, "collaborations": collaborations, "total_issues": len(issues)}
    
    def _identify_dev_tester(self, journals: List[Dict], issue: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Identify developer and tester from journals
        
        Returns:
            (developer_name, tester_name)
        """
        if not journals:
            # No journals, fallback to author and assignee
            author = issue.get('author', {}).get('name', 'Unknown')
            assignee = issue.get('assigned_to', {}).get('name', 'Unassigned') if issue.get('assigned_to') else 'Unassigned'
            return author, assignee
        
        # Sort journals by creation time
        sorted_journals = sorted(journals, key=lambda j: j.get('created_on', ''))
        
        developer = None
        tester = None
        
        # Find the journal where status changed to "测试中" (developer)
        # and the journal where status changed from "测试中" to "已解决" (tester)
        for journal in sorted_journals:
            user_name = journal.get('user', {}).get('name', 'Unknown')
            details = journal.get('details', [])
            
            for detail in details:
                if detail.get('name') == 'status_id':
                    old_status = detail.get('old_value', '')
                    new_status = detail.get('new_value', '')
                    
                    # Developer: changed status TO "测试中" (7)
                    if new_status == str(self.status_testing_id):
                        developer = user_name
                    
                    # Tester: changed status FROM "测试中" (7) TO "已解决" (3)
                    if old_status == str(self.status_testing_id) and new_status == str(self.status_resolved_id):
                        tester = user_name
        
        # Fallback if not found
        if not developer:
            # Use the person who assigned to tester as developer
            for journal in sorted_journals:
                details = journal.get('details', [])
                for detail in details:
                    if detail.get('name') == 'assigned_to_id':
                        developer = journal.get('user', {}).get('name', 'Unknown')
                        break
                if developer:
                    break
        
        if not developer:
            developer = issue.get('author', {}).get('name', 'Unknown')
        
        if not tester:
            tester = issue.get('assigned_to', {}).get('name', 'Unassigned') if issue.get('assigned_to') else 'Unassigned'
        
        return developer, tester
    
    def _get_resolved_issues(self, project_id: int) -> List[Dict]:
        """Get all resolved issues for a project"""
        all_issues = []
        offset = 0
        limit = 100
        
        while True:
            resp = requests.get(
                f"{self.base_url}/issues.json",
                headers=self.headers,
                params={"project_id": project_id, "status_id": self.status_resolved_id, "limit": limit, "offset": offset},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            if len(issues) < limit:
                break
            offset += limit
        
        return all_issues
    
    def _get_issue_journals(self, issue_id: int) -> List[Dict]:
        """Get journals for an issue"""
        resp = requests.get(
            f"{self.base_url}/issues/{issue_id}.json",
            headers=self.headers,
            params={"include": "journals"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        issue = data.get('issue', {})
        return issue.get('journals', [])
    
    def format_report(self, result: Dict, project_id: int) -> str:
        """Format analysis as readable report"""
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        total = result["total_issues"]
        if total == 0:
            return f"📊 Project {project_id}: No resolved issues found"
        
        lines = []
        lines.append("=" * 70)
        lines.append(f"📊 Project {project_id} - Dev/Test Workload Analysis")
        lines.append("=" * 70)
        lines.append(f"Total Resolved Issues: {total}")
        lines.append("")
        
        lines.append("👨💻 Developers (changed status TO '测试中'):")
        lines.append("-" * 50)
        if result["developers"]:
            for name, data in sorted(result["developers"].items(), key=lambda x: x[1]["resolved_count"], reverse=True)[:10]:
                lines.append(f"{name:<25} | {data['resolved_count']:>3} issues")
        else:
            lines.append("No data")
        lines.append("")
        
        lines.append("🧪 Testers (changed '测试中' TO '已解决'):")
        lines.append("-" * 50)
        if result["testers"]:
            for name, data in sorted(result["testers"].items(), key=lambda x: x[1]["test_count"], reverse=True)[:10]:
                lines.append(f"{name:<25} | {data['test_count']:>3} issues")
        else:
            lines.append("No data")
        lines.append("")
        
        lines.append("🤝 Collaborations:")
        lines.append("-" * 50)
        if result["collaborations"]:
            for collab, data in sorted(result["collaborations"].items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
                lines.append(f"{collab:<35} | {data['count']:>3} issues")
        else:
            lines.append("No data")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate formatted report"""
        return self.format_report(analysis, 0)


# Global instance
_analyzer = DevTestAnalyzer()

def analyze_project(project_id: int) -> Dict:
    """Analyze a single project"""
    return _analyzer.analyze_project(project_id)

def analyze_projects(project_ids: List[int]) -> Dict:
    """Analyze multiple projects"""
    all_results = {"developers": {}, "testers": {}, "collaborations": {}, "total_issues": 0}
    for pid in project_ids:
        result = _analyzer.analyze_project(pid)
        all_results["total_issues"] += result.get("total_issues", 0)
        for dev, data in result.get("developers", {}).items():
            if dev not in all_results["developers"]:
                all_results["developers"][dev] = {"resolved_count": 0, "issues": []}
            all_results["developers"][dev]["resolved_count"] += data["resolved_count"]
            all_results["developers"][dev]["issues"].extend(data["issues"])
        for tester, data in result.get("testers", {}).items():
            if tester not in all_results["testers"]:
                all_results["testers"][tester] = {"test_count": 0, "issues": []}
            all_results["testers"][tester]["test_count"] += data["test_count"]
            all_results["testers"][tester]["issues"].extend(data["issues"])
        for collab, data in result.get("collaborations", {}).items():
            if collab not in all_results["collaborations"]:
                all_results["collaborations"][collab] = {"count": 0, "issues": []}
            all_results["collaborations"][collab]["count"] += data["count"]
            all_results["collaborations"][collab]["issues"].extend(data["issues"])
    return all_results
