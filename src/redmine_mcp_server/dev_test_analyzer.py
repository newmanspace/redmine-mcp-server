#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev/Test Workload Analyzer - Simplified Version

Logic:
- Developer: User belongs to "Semi Dev Team" or "Semi SPC Team"
- Tester (Implementation): All other users

This is a simplified approach based on user groups rather than journal analysis.
"""

import logging
import requests
import os
from typing import Dict, List, Set, Optional, Tuple

REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

logger = logging.getLogger(__name__)

class DevTestAnalyzer:
    def __init__(self):
        self.base_url = REDMINE_URL
        self.api_key = REDMINE_API_KEY
        self.headers = {"X-Redmine-API-Key": self.api_key}
        self.status_resolved_id = 3  # "已解决"
        self.dev_teams: Set[str] = set()
        self._load_dev_teams()
        
    def _load_dev_teams(self):
        """Load developer team members"""
        try:
            # Get Semi Dev Team
            dev_team = self._get_team_members("Semi Dev Team")
            self.dev_teams.update(dev_team)
            
            # Get Semi SPC Team
            spc_team = self._get_team_members("Semi SPC Team")
            self.dev_teams.update(spc_team)
            
            logger.info(f"Loaded {len(self.dev_teams)} developer team members")
        except Exception as e:
            logger.error(f"Failed to load developer teams: {e}")
    
    def _get_team_members(self, team_name: str) -> Set[str]:
        """Get member names from a team/group"""
        members = set()
        try:
            # Search for group by name
            resp = requests.get(
                f"{self.base_url}/groups.json",
                headers=self.headers,
                params={"name": team_name},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                groups = data.get('groups', [])
                if groups:
                    group_id = groups[0]['id']
                    # Get group details with members
                    resp2 = requests.get(
                        f"{self.base_url}/groups/{group_id}.json",
                        headers=self.headers,
                        params={"include": "users,memberships"},
                        timeout=30
                    )
                    if resp2.status_code == 200:
                        group_data = resp2.json()
                        group = group_data.get('group', {})
                        users = group.get('users', [])
                        for user in users:
                            members.add(user.get('name', ''))
        except Exception as e:
            logger.error(f"Failed to get team {team_name} members: {e}")
        return members
    
    def is_developer(self, user_name: str) -> bool:
        """Check if user is a developer"""
        return user_name in self.dev_teams
    
    def analyze_project(self, project_id: int) -> Dict:
        """Analyze developer/tester workload for a project"""
        logger.info(f"Analyzing dev/test workload for project {project_id}")
        
        # Reload teams to ensure fresh data
        self._load_dev_teams()
        
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
            
            # Get the person who resolved the issue
            resolver = self._get_resolver(issue)
            
            # Classify as developer or tester based on team
            if resolver and self.is_developer(resolver):
                # Developer
                if resolver not in developers:
                    developers[resolver] = {"resolved_count": 0, "issues": []}
                developers[resolver]["resolved_count"] += 1
                developers[resolver]["issues"].append(issue_id)
            elif resolver:
                # Tester (Implementation team)
                if resolver not in testers:
                    testers[resolver] = {"test_count": 0, "issues": []}
                testers[resolver]["test_count"] += 1
                testers[resolver]["issues"].append(issue_id)
        
        # Generate collaborations (developer → tester pairs per issue)
        # For simplicity, we'll show top developers and testers
        for dev in developers:
            for tester in testers:
                key = f"{dev} → {tester}"
                collaborations[key] = {"count": 0, "issues": []}
        
        return {
            "developers": developers, 
            "testers": testers, 
            "collaborations": collaborations, 
            "total_issues": len(issues),
            "dev_team_members": list(self.dev_teams)
        }
    
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
    
    def _get_resolver(self, issue: Dict) -> Optional[str]:
        """Get the person who resolved the issue"""
        journals = self._get_issue_journals(issue['id'])
        if not journals:
            return issue.get('author', {}).get('name', 'Unknown')
        
        # Sort journals by creation time
        sorted_journals = sorted(journals, key=lambda j: j.get('created_on', ''))
        
        # Find the journal where status changed to resolved
        for journal in sorted_journals:
            details = journal.get('details', [])
            for detail in details:
                if detail.get('name') == 'status_id' and str(detail.get('new_value', '')) == str(self.status_resolved_id):
                    return journal.get('user', {}).get('name', 'Unknown')
        
        # Fallback to last journal user
        if sorted_journals:
            return sorted_journals[-1].get('user', {}).get('name', 'Unknown')
        
        return issue.get('author', {}).get('name', 'Unknown')
    
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
        lines.append(f"Developer Team Members: {len(result.get('dev_team_members', []))}")
        lines.append("")
        
        lines.append("👨💻 Developers (Semi Dev Team / Semi SPC Team):")
        lines.append("-" * 50)
        if result["developers"]:
            for name, data in sorted(result["developers"].items(), key=lambda x: x[1]["resolved_count"], reverse=True):
                lines.append(f"{name:<25} | {data['resolved_count']:>3} issues")
        else:
            lines.append("No data")
        lines.append("")
        
        lines.append("🧪 Testers/Implementation (Other teams):")
        lines.append("-" * 50)
        if result["testers"]:
            for name, data in sorted(result["testers"].items(), key=lambda x: x[1]["test_count"], reverse=True):
                lines.append(f"{name:<25} | {data['test_count']:>3} issues")
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
    return all_results
