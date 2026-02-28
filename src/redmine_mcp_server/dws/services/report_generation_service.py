#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Generation Service

Generates daily/weekly/monthly reports with trend analysis.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """Report Generation Service"""

    def __init__(self):
        self.redmine_url = os.getenv('REDMINE_URL')
        self.api_key = os.getenv('REDMINE_API_KEY')
        
        # Import trend analysis service
        from .trend_analysis_service import TrendAnalysisService
        self.trend_service = TrendAnalysisService()
        
        logger.info("ReportGenerationService initialized")

    def redmine_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Call Redmine REST API"""
        url = f"{self.redmine_url}/{endpoint}"
        all_params = {'key': self.api_key, **(params or {})}
        resp = requests.get(url, params=all_params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get basic project statistics"""
        try:
            all_issues = []
            offset = 0
            limit = 100

            while True:
                data = self.redmine_get("issues.json", {
                    'project_id': project_id,
                    'status_id': '*',
                    'limit': limit,
                    'offset': offset
                })
                issues = data.get('issues', [])
                all_issues.extend(issues)

                if len(issues) < limit:
                    break
                offset += limit

            # Basic statistics
            total = len(all_issues)
            open_count = sum(1 for i in all_issues if i.get('status', {}).get('name') != '已shutdown')
            closed_count = sum(1 for i in all_issues if i.get('status', {}).get('name') == '已shutdown')
            
            # status分布
            by_status = {}
            for issue in all_issues:
                status = issue.get('status', {}).get('name', 'Unknown')
                by_status[status] = by_status.get(status, 0) + 1
            
            # priority分布
            by_priority = {}
            for issue in all_issues:
                priority = issue.get('priority', {}).get('name', '普通')
                by_priority[priority] = by_priority.get(priority, 0) + 1
            
            # 高priority Issue
            high_priority = [
                i for i in all_issues 
                if i.get('priority', {}).get('name') in ['立刻', '紧急', '高']
            ][:10]
            
            # 人员job量
            assignee_count = {}
            for issue in all_issues:
                assigned_to = issue.get('assigned_to')
                if assigned_to:
                    name = assigned_to.get('name', 'Unknown')
                    assignee_count[name] = assignee_count.get(name, 0) + 1
            
            top_assignees = [
                {'name': name, 'count': count}
                for name, count in sorted(assignee_count.items(), key=lambda x: x[1], reverse=True)
            ][:10]
            
            # 今日statistics
            today = datetime.now().date()
            today_new = 0
            today_closed = 0
            
            for issue in all_issues:
                created_on = issue.get('created_on', '')
                if created_on:
                    try:
                        created_date = datetime.fromisoformat(created_on.replace('Z', '+00:00')).date()
                        if created_date == today:
                            today_new += 1
                    except:
                        pass
                
                closed_on = issue.get('closed_on', '')
                if closed_on:
                    try:
                        closed_date = datetime.fromisoformat(closed_on.replace('Z', '+00:00')).date()
                        if closed_date == today:
                            today_closed += 1
                    except:
                        pass
            
            return {
                'project_id': project_id,
                'total_issues': total,
                'open_issues': open_count,
                'closed_issues': closed_count,
                'today_new': today_new,
                'today_closed': today_closed,
                'by_status': by_status,
                'by_priority': by_priority,
                'high_priority_issues': high_priority,
                'top_assignees': top_assignees
            }
            
        except Exception as e:
            logger.error(f"Failed to get project stats: {e}")
            return None

    def generate_daily_report(
        self,
        project_id: int,
        level: str = "brief",
        include_trend: bool = True,
        trend_days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate daily report

        Args:
            project_id: Project ID
            level: Report level (brief/detailed/comprehensive)
            include_trend: Include trend analysis
            trend_days: Trend analysis period in days

        Returns:
            Daily report data
        """
        stats = self.get_project_stats(project_id)
        if not stats:
            return None

        report = {
            'type': 'daily',
            'project_id': project_id,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'generated_at': datetime.now().isoformat(),
            'stats': stats
        }

        # Add content based on level
        if level in ['detailed', 'comprehensive']:
            # Detailed report includes high priority issues and team workload
            report['high_priority_issues'] = stats['high_priority_issues']
            report['top_assignees'] = stats['top_assignees']

        if level == 'comprehensive':
            # Comprehensive report includes trend analysis
            if include_trend:
                trend_data = self.trend_service.analyze_daily_trend(project_id, trend_days)
                report['trend_analysis'] = trend_data

        return report

    def generate_weekly_report(
        self,
        project_id: int,
        level: str = "brief",
        include_trend: bool = True,
        trend_weeks: int = 4
    ) -> Dict[str, Any]:
        """
        Generate weekly report

        Args:
            project_id: project ID
            level: reportlevel
            include_trend: 是否包含trend
            trend_weeks: trendanalysis周数

        Returns:
            周报data
        """
        stats = self.get_project_stats(project_id)
        if not stats:
            return None

        # 本周statistics（过去 7 天）
        today = datetime.now().date()
        week_start = today - timedelta(days=6)
        
        week_new = 0
        week_closed = 0
        
        # 重新get Issue 来计算本周data
        all_issues = []
        offset = 0
        limit = 100
        
        while True:
            data = self.redmine_get("issues.json", {
                'project_id': project_id,
                'status_id': '*',
                'limit': limit,
                'offset': offset
            })
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            if len(issues) < limit:
                break
            offset += limit
        
        for issue in all_issues:
            created_on = issue.get('created_on', '')
            closed_on = issue.get('closed_on', '')
            
            if created_on:
                try:
                    created_date = datetime.fromisoformat(created_on.replace('Z', '+00:00')).date()
                    if week_start <= created_date <= today:
                        week_new += 1
                except:
                    pass
            
            if closed_on:
                try:
                    closed_date = datetime.fromisoformat(closed_on.replace('Z', '+00:00')).date()
                    if week_start <= closed_date <= today:
                        week_closed += 1
                except:
                    pass

        report = {
            'type': 'weekly',
            'project_id': project_id,
            'week_start': week_start.isoformat(),
            'week_end': today.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'stats': stats,
            'weekly_summary': {
                'week_new': week_new,
                'week_closed': week_closed,
                'week_net_change': week_new - week_closed
            }
        }

        if level in ['detailed', 'comprehensive']:
            report['high_priority_issues'] = stats['high_priority_issues']
            report['top_assignees'] = stats['top_assignees']

        if level == 'comprehensive' and include_trend:
            trend_data = self.trend_service.analyze_weekly_trend(project_id, trend_weeks)
            report['trend_analysis'] = trend_data

        return report

    def generate_monthly_report(
        self,
        project_id: int,
        level: str = "brief",
        include_trend: bool = True,
        trend_months: int = 6
    ) -> Dict[str, Any]:
        """
        generate月报

        Args:
            project_id: project ID
            level: reportlevel
            include_trend: 是否包含trend
            trend_months: trendanalysis月数

        Returns:
            月报data
        """
        stats = self.get_project_stats(project_id)
        if not stats:
            return None

        # 本月statistics
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        month_new = 0
        month_closed = 0
        
        # get Issue 计算本月data
        all_issues = []
        offset = 0
        limit = 100
        
        while True:
            data = self.redmine_get("issues.json", {
                'project_id': project_id,
                'status_id': '*',
                'limit': limit,
                'offset': offset
            })
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            if len(issues) < limit:
                break
            offset += limit
        
        for issue in all_issues:
            created_on = issue.get('created_on', '')
            closed_on = issue.get('closed_on', '')
            
            if created_on:
                try:
                    created_date = datetime.fromisoformat(created_on.replace('Z', '+00:00')).date()
                    if created_date >= month_start:
                        month_new += 1
                except:
                    pass
            
            if closed_on:
                try:
                    closed_date = datetime.fromisoformat(closed_on.replace('Z', '+00:00')).date()
                    if closed_date >= month_start:
                        month_closed += 1
                except:
                    pass

        report = {
            'type': 'monthly',
            'project_id': project_id,
            'month': today.strftime("%Y-%m"),
            'month_start': month_start.isoformat(),
            'month_end': today.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'stats': stats,
            'monthly_summary': {
                'month_new': month_new,
                'month_closed': month_closed,
                'month_net_change': month_new - month_closed
            }
        }

        if level in ['detailed', 'comprehensive']:
            report['high_priority_issues'] = stats['high_priority_issues']
            report['top_assignees'] = stats['top_assignees']
            
            # 月报添加更多analysis
            if level == 'comprehensive':
                # 计算完成率
                if stats['total_issues'] > 0:
                    report['completion_rate'] = round(
                        stats['closed_issues'] / stats['total_issues'] * 100, 2
                    )
                
                # 计算平均解决time（如果有data）
                report['avg_resolution_days'] = self._calculate_avg_resolution_time(all_issues)

        if level == 'comprehensive' and include_trend:
            trend_data = self.trend_service.analyze_monthly_trend(project_id, trend_months)
            report['trend_analysis'] = trend_data

        return report

    def _calculate_avg_resolution_time(self, issues: List[Dict]) -> Optional[float]:
        """计算平均解决time（天）"""
        resolution_times = []
        
        for issue in issues:
            if issue.get('status', {}).get('name') == '已shutdown':
                created_on = issue.get('created_on', '')
                closed_on = issue.get('closed_on', '')
                
                if created_on and closed_on:
                    try:
                        created = datetime.fromisoformat(created_on.replace('Z', '+00:00'))
                        closed = datetime.fromisoformat(closed_on.replace('Z', '+00:00'))
                        days = (closed - created).total_seconds() / 86400
                        resolution_times.append(days)
                    except:
                        pass
        
        if resolution_times:
            return round(sum(resolution_times) / len(resolution_times), 1)
        return None

    def generate_report(
        self,
        project_id: int,
        report_type: str,
        report_level: str,
        include_trend: bool,
        trend_period: int
    ) -> Dict[str, Any]:
        """
        generatereport（unifiedentry）

        Args:
            project_id: project ID
            report_type: reportclass型 (daily/weekly/monthly)
            report_level: reportlevel (brief/detailed/comprehensive)
            include_trend: 是否包含trend
            trend_period: trendperiod

        Returns:
            reportdata
        """
        if report_type == 'daily':
            return self.generate_daily_report(
                project_id, report_level, include_trend, trend_period
            )
        elif report_type == 'weekly':
            return self.generate_weekly_report(
                project_id, report_level, include_trend, trend_period
            )
        elif report_type == 'monthly':
            return self.generate_monthly_report(
                project_id, report_level, include_trend, trend_period
            )
        else:
            return {'error': f'Invalid report type: {report_type}'}


# Convenience functions

def generate_project_report(
    project_id: int,
    report_type: str = "daily",
    report_level: str = "brief",
    include_trend: bool = True,
    trend_period: int = 7
) -> Dict[str, Any]:
    """generateprojectreport"""
    service = ReportGenerationService()
    return service.generate_report(
        project_id, report_type, report_level, include_trend, trend_period
    )
