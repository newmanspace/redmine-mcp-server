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
from datetime import datetime

REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

logger = logging.getLogger(__name__)

# Role category mapping based on Redmine role names
ROLE_CATEGORY_MAP = {
    # Manager roles
    'project manager': 'manager',
    'manager': 'manager',
    '负责人': 'manager',
    '项目经理': 'manager',
    
    # Implementation roles
    'implementation': 'implementation',
    '实施': 'implementation',
    '实施人员': 'implementation',
    
    # Developer roles
    'developer': 'developer',
    '开发': 'developer',
    '开发人员': 'developer',
    'engineer': 'developer',
    
    # Tester roles
    'tester': 'tester',
    '测试': 'tester',
    '测试人员': 'tester',
    'qa': 'tester',
    
    # Other roles
    'viewer': 'other',
    '报告者': 'other',
    'reporter': 'other',
}

# Role priority (lower is higher priority)
ROLE_PRIORITY = {
    'manager': 1,
    'implementation': 2,
    'developer': 3,
    'tester': 4,
    'other': 5,
}

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
    
    def _get_role_category(self, role_name: str) -> str:
        """Get role category from role name"""
        if not role_name:
            return 'other'
        
        role_lower = role_name.lower()
        for key, category in ROLE_CATEGORY_MAP.items():
            if key in role_lower:
                return category
        return 'other'
    
    def _get_role_priority(self, category: str) -> int:
        """Get role priority (lower is higher priority)"""
        return ROLE_PRIORITY.get(category, 5)
    
    def extract_contributors_from_journals(self, journals: List[Dict], issue_id: int, 
                                           project_id: int) -> List[Dict]:
        """
        Extract contributors from issue journals
        
        Args:
            journals: List of journal entries
            issue_id: Issue ID
            project_id: Project ID
        
        Returns:
            List of contributor dictionaries
        """
        if not journals:
            return []
        
        contributors = {}  # user_id -> contributor data
        
        for journal in journals:
            user = journal.get('user', {})
            user_id = user.get('id')
            user_name = user.get('name', 'Unknown')
            
            if not user_id:
                continue
            
            if user_id not in contributors:
                contributors[user_id] = {
                    'user_id': user_id,
                    'user_name': user_name,
                    'journal_count': 0,
                    'status_change_count': 0,
                    'note_count': 0,
                    'assigned_change_count': 0,
                    'first_contribution': journal.get('created_on'),
                    'last_contribution': journal.get('created_on'),
                    'highest_role_id': None,
                    'highest_role_name': None,
                    'role_category': None,
                    'role_priority': 999,
                }
            
            contrib = contributors[user_id]
            contrib['journal_count'] += 1
            contrib['last_contribution'] = journal.get('created_on', contrib['last_contribution'])
            
            # Analyze journal details
            details = journal.get('details', [])
            for detail in details:
                prop_name = detail.get('name', '')
                
                if prop_name == 'status_id':
                    contrib['status_change_count'] += 1
                elif prop_name == 'notes' and detail.get('new_value'):
                    contrib['note_count'] += 1
                elif prop_name == 'assigned_to_id':
                    contrib['assigned_change_count'] += 1
        
        # Get user roles from project
        project_roles = self.get_project_member_roles(project_id)
        user_role_map = {r['user_id']: r for r in project_roles}
        
        # Enrich contributors with role information
        result = []
        for user_id, contrib in contributors.items():
            role_info = user_role_map.get(user_id, {})
            
            # Update with role info if available
            if role_info:
                contrib['highest_role_id'] = role_info.get('highest_role_id')
                contrib['highest_role_name'] = role_info.get('highest_role_name')
                contrib['role_category'] = role_info.get('role_category')
            else:
                # Fallback: classify based on team membership
                if self.is_developer(contrib['user_name']):
                    contrib['role_category'] = 'developer'
                else:
                    contrib['role_category'] = 'implementation'
            
            result.append(contrib)
        
        return result
    
    def get_project_member_roles(self, project_id: int) -> List[Dict]:
        """
        Get all member roles for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            List of user role dictionaries
        """
        roles = []
        seen_users = {}  # user_id -> role data
        
        try:
            # Get project details with memberships
            resp = requests.get(
                f"{self.base_url}/projects/{project_id}.json",
                headers=self.headers,
                params={"include": "memberships"},
                timeout=30
            )
            
            if resp.status_code != 200:
                logger.warning(f"Failed to get project {project_id} memberships: {resp.status_code}")
                return roles
            
            data = resp.json()
            project = data.get('project', {})
            memberships = project.get('memberships', [])
            
            for membership in memberships:
                user = membership.get('user', {})
                user_id = user.get('id')
                user_name = user.get('name', 'Unknown')
                
                if not user_id:
                    continue
                
                # Get all roles for this user
                member_roles = membership.get('roles', [])
                role_ids = [r.get('id') for r in member_roles]
                role_names = [r.get('name') for r in member_roles]
                
                # Determine highest priority role
                highest_role = None
                highest_priority = 999
                highest_category = 'other'
                
                for role in member_roles:
                    role_name = role.get('name', '')
                    category = self._get_role_category(role_name)
                    priority = self._get_role_priority(category)
                    
                    if priority < highest_priority:
                        highest_priority = priority
                        highest_role = role
                        highest_category = category
                
                # Update or create user entry
                if user_id in seen_users:
                    existing = seen_users[user_id]
                    if highest_priority < existing.get('role_priority', 999):
                        existing['highest_role_id'] = highest_role.get('id') if highest_role else None
                        existing['highest_role_name'] = highest_role.get('name') if highest_role else None
                        existing['role_category'] = highest_category
                        existing['role_priority'] = highest_priority
                        existing['all_role_ids'] = ','.join(map(str, role_ids))
                else:
                    seen_users[user_id] = {
                        'user_id': user_id,
                        'user_name': user_name,
                        'highest_role_id': highest_role.get('id') if highest_role else None,
                        'highest_role_name': highest_role.get('name') if highest_role else None,
                        'role_category': highest_category,
                        'role_priority': highest_priority,
                        'all_role_ids': ','.join(map(str, role_ids)),
                        'is_direct_member': True,
                    }
            
            roles = list(seen_users.values())
            logger.info(f"Retrieved {len(roles)} member roles for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to get project member roles: {e}")
        
        return roles


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
