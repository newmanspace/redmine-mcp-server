# /docker/redmine-mcp-server/src/redmine_mcp_server/subscription_reporter.py
"""
subscription reportgenerate与pushmodule
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .redmine_warehouse import DataWarehouse
from .subscriptions import SubscriptionManager

logger = logging.getLogger(__name__)

# Import Redmine API
try:
    from .redmine_handler import REDMINE_URL, redmine
    from pyredmine.exceptions import ResourceNotFoundError
except ImportError:
    REDMINE_URL = ""
    redmine = None
    ResourceNotFoundError = Exception


class SubscriptionReporter:
    """subscription reportgenerate器"""
    
    def __init__(self):
        self.warehouse = None
        self._init_warehouse()
    
    def _init_warehouse(self):
        """延迟initialize数仓connection"""
        try:
            self.warehouse = DataWarehouse()
            logger.info("Reporter warehouse connection initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize warehouse: {e}")
            self.warehouse = None
    
    def generate_brief_report(self, project_id: int) -> Dict[str, Any]:
        """
        generatebriefreport
        
        Args:
            project_id: project ID
        
        Returns:
            briefreportdata
        """
        if not self.warehouse:
            return self._generate_brief_from_api(project_id)
        
        today = datetime.now().date()
        
        try:
            # Get statistics from warehouse
            stats = self.warehouse.get_project_daily_stats(project_id, today)
            
            if not stats.get('from_cache', False):
                # Warehouse has no data, fetch from API
                return self._generate_brief_from_api(project_id)
            
            return {
                "project_id": project_id,
                "level": "brief",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_issues": stats.get('total', 0),
                    "new_today": stats.get('today_new', 0),
                    "closed_today": stats.get('today_closed', 0),
                    "updated_today": stats.get('today_updated', 0)
                },
                "priority_highlights": {
                    "immediate": stats.get('by_priority', {}).get('立刻', 0),
                    "urgent": stats.get('by_priority', {}).get('紧急', 0),
                    "high": stats.get('by_priority', {}).get('高', 0)
                },
                "top_issues": stats.get('high_priority_issues', [])[:5]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate brief report: {e}")
            return self._generate_brief_from_api(project_id)
    
    def _generate_brief_from_api(self, project_id: int) -> Dict[str, Any]:
        """从 Redmine API generatebriefreport"""
        if not redmine:
            return {"error": "Redmine client not initialized"}
        
        try:
            # Get project info
            project = redmine.project.get(project_id)
            
            # Get new issues today
            today = datetime.now().strftime('%Y-%m-%d')
            new_issues = list(redmine.issue.filter(
                project_id=project_id,
                created_on=f">={today}",
                limit=10
            ))
            
            # Get high priority issues
            high_priority = list(redmine.issue.filter(
                project_id=project_id,
                priority_id='1,2,3',
                status_id='*',
                limit=10
            ))
            
            return {
                "project_id": project_id,
                "project_name": project.name,
                "level": "brief",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "new_today": len(new_issues)
                },
                "high_priority_count": len(high_priority),
                "top_issues": [
                    {
                        "id": i.id,
                        "subject": i.subject,
                        "priority": i.priority.name if i.priority else "N/A",
                        "status": i.status.name if i.status else "N/A",
                        "assignee": i.assigned_to.name if i.assigned_to else "Unassigned",
                        "url": f"{REDMINE_URL}/issues/{i.id}"
                    }
                    for i in high_priority[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate brief report from API: {e}")
            return {"error": str(e)}
    
    def generate_detailed_report(self, project_id: int) -> Dict[str, Any]:
        """
        generatedetailedreport
        
        Args:
            project_id: project ID
        
        Returns:
            detailedreportdata
        """
        if not self.warehouse:
            return self._generate_detailed_from_api(project_id)
        
        today = datetime.now().date()
        
        try:
            stats = self.warehouse.get_project_daily_stats(project_id, today)
            
            if not stats.get('from_cache', False):
                return self._generate_detailed_from_api(project_id)
            
            # Get assignee workload
            top_assignees = self.warehouse.get_top_assignees(project_id, today, limit=10)
            
            # Get high priority issues
            high_priority = self.warehouse.get_high_priority_issues(project_id, today, limit=20)
            
            # Identify overdue risk issues (>30 days unclosed high priority)
            overdue_risks = []
            for issue in high_priority:
                try:
                    created = datetime.strptime(issue.get('created_at', '')[:10], '%Y-%m-%d')
                    age = (datetime.now() - created).days
                    if age > 30 and issue.get('status_name') not in ['已shutdown', '已解决']:
                        overdue_risks.append({
                            **issue,
                            "age_days": age
                        })
                except:
                    pass
            
            return {
                "project_id": project_id,
                "level": "detailed",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_issues": stats.get('total', 0),
                    "new_today": stats.get('today_new', 0),
                    "closed_today": stats.get('today_closed', 0),
                    "updated_today": stats.get('today_updated', 0)
                },
                "priority_breakdown": stats.get('by_priority', {}),
                "status_breakdown": stats.get('by_status', {}),
                "top_assignees": top_assignees[:10],
                "high_priority_issues": high_priority[:20],
                "overdue_risks": overdue_risks[:10],
                "insights": self._generate_insights(stats, overdue_risks, top_assignees)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate detailed report: {e}")
            return self._generate_detailed_from_api(project_id)
    
    def _generate_detailed_from_api(self, project_id: int) -> Dict[str, Any]:
        """从 Redmine API generatedetailedreport"""
        if not redmine:
            return {"error": "Redmine client not initialized"}
        
        try:
            project = redmine.project.get(project_id)
            
            # Get all issues
            all_issues = list(redmine.issue.filter(project_id=project_id, limit=500))
            
            # Statistics
            by_status = {}
            by_priority = {}
            by_assignee = {}
            
            for issue in all_issues:
                status = issue.status.name if issue.status else 'Unknown'
                priority = issue.priority.name if issue.priority else 'Unknown'
                assignee = issue.assigned_to.name if issue.assigned_to else 'Unassigned'
                
                by_status[status] = by_status.get(status, 0) + 1
                by_priority[priority] = by_priority.get(priority, 0) + 1
                by_assignee[assignee] = by_assignee.get(assignee, 0) + 1
            
            # High priority
            high_priority = [i for i in all_issues if i.priority and i.priority.name in ['立刻', '紧急', '高']]
            
            return {
                "project_id": project_id,
                "project_name": project.name,
                "level": "detailed",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_issues": len(all_issues)
                },
                "priority_breakdown": by_priority,
                "status_breakdown": by_status,
                "assignee_breakdown": dict(sorted(by_assignee.items(), key=lambda x: x[1], reverse=True)[:10]),
                "high_priority_count": len(high_priority),
                "high_priority_issues": [
                    {
                        "id": i.id,
                        "subject": i.subject,
                        "priority": i.priority.name if i.priority else "N/A",
                        "status": i.status.name if i.status else "N/A",
                        "assignee": i.assigned_to.name if i.assigned_to else "Unassigned",
                        "created_on": i.created_on,
                        "url": f"{REDMINE_URL}/issues/{i.id}"
                    }
                    for i in high_priority[:20]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate detailed report from API: {e}")
            return {"error": str(e)}
    
    def _generate_insights(
        self,
        stats: Dict,
        overdue_risks: List,
        top_assignees: List
    ) -> Dict[str, Any]:
        """generateproject洞察"""
        insights = {
            "alerts": [],
            "suggestions": []
        }
        
        # Overdue risk alert
        if overdue_risks:
            insights["alerts"].append({
                "type": "overdue_risk",
                "severity": "high" if len(overdue_risks) > 5 else "medium",
                "message": f"发现 {len(overdue_risks)} 个逾期高priority Issue",
                "count": len(overdue_risks)
            })
        
        # Workload alert
        for assignee in top_assignees[:3]:
            if assignee.get('total', 0) > 30:
                insights["alerts"].append({
                    "type": "workload",
                    "severity": "medium",
                    "message": f"{assignee.get('assigned_to_name')} 负载过高 ({assignee.get('total')} job)",
                    "assignee": assignee.get('assigned_to_name'),
                    "task_count": assignee.get('total')
                })
        
        # Recommendations
        if stats.get('today_new', 0) > 20:
            insights["suggestions"].append("今日新增 Issue 较多，建议安排priority评审")
        
        if stats.get('today_closed', 0) == 0 and stats.get('total', 0) > 100:
            insights["suggestions"].append("今日无shutdown Issue，建议关注进度")
        
        return insights
    
    def format_report_for_message(
        self,
        report: Dict[str, Any],
        channel: str = "dingtalk"
    ) -> str:
        """
        format化report为消息文本
        
        Args:
            report: reportdata
            channel: pushchannel
        
        Returns:
            format化后的消息
        """
        level = report.get('level', 'brief')
        project_id = report.get('project_id')
        summary = report.get('summary', {})
        
        lines = []
        lines.append(f"📊 projectsubscription report")
        lines.append(f"📁 project ID: {project_id}")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("━━━" * 10)
        lines.append("")
        
        # Status snapshot
        lines.append("### 📈 status快照")
        if 'total_issues' in summary:
            lines.append(f"- Issue 总数：{summary.get('total_issues', 'N/A')}")
        if 'new_today' in summary:
            lines.append(f"- 新建 (今日): {summary.get('new_today', 0)}")
        if 'closed_today' in summary:
            lines.append(f"- shutdown (今日): {summary.get('closed_today', 0)}")
        lines.append("")
        
        if level == "detailed":
            # Detailed report content
            if 'priority_breakdown' in report:
                priority = report['priority_breakdown']
                lines.append("**priority分布**:")
                lines.append(f"- 🔴 立刻：{priority.get('立刻', 0)}")
                lines.append(f"- 🟠 紧急：{priority.get('紧急', 0)}")
                lines.append(f"- 🟡 高：{priority.get('高', 0)}")
                lines.append("")
            
            if 'top_assignees' in report:
                lines.append("### 👥 人员job量 TOP5")
                for a in report['top_assignees'][:5]:
                    lines.append(f"- {a.get('assigned_to_name')}: {a.get('total')} job")
                lines.append("")
            
            if 'overdue_risks' in report and report['overdue_risks']:
                lines.append("### ⚠️ 逾期风险")
                for risk in report['overdue_risks'][:5]:
                    lines.append(f"- #{risk.get('issue_id')} {risk.get('subject')[:30]} ({risk.get('age_days')}天)")
                lines.append("")
        
        # High priority Issue
        if 'top_issues' in report or 'high_priority_issues' in report:
            lines.append("### 🔴 高priority Issue")
            issues = report.get('top_issues', report.get('high_priority_issues', []))
            for issue in issues[:10]:
                icon = "🔴" if issue.get('priority_name') == '立刻' else "🟠" if issue.get('priority_name') == '紧急' else "🟡"
                subject = issue.get('subject', '')[:40]
                lines.append(f"- {icon} #{issue.get('issue_id')} {subject}")
        
        lines.append("")
        lines.append("━━━" * 10)
        
        return '\n'.join(lines)


# Global reporter instance
reporter: Optional[SubscriptionReporter] = None


def get_reporter() -> SubscriptionReporter:
    """getreport器单例"""
    global reporter
    if reporter is None:
        reporter = SubscriptionReporter()
    return reporter
