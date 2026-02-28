#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trendanalysisservice

analysisproject Issue 的trend变化，support日报/周报/月报
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class TrendAnalysisService:
    """trendanalysisservice"""

    def __init__(self):
        self.redmine_url = os.getenv("REDMINE_URL")
        self.api_key = os.getenv("REDMINE_API_KEY")
        logger.info("TrendAnalysisService initialized")

    def redmine_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Call Redmine REST API"""
        url = f"{self.redmine_url}/{endpoint}"
        all_params = {"key": self.api_key, **(params or {})}
        resp = requests.get(url, params=all_params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_historical_issues(
        self, project_id: int, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        get历史 Issue data（用于trendanalysis）

        Args:
            project_id: project ID
            days: analysis天数

        Returns:
            Issue list
        """
        all_issues = []
        offset = 0
        limit = 100

        # get所有 Issue（包含历史记录）
        while True:
            try:
                data = self.redmine_get(
                    "issues.json",
                    {
                        "project_id": project_id,
                        "status_id": "*",
                        "limit": limit,
                        "offset": offset,
                        "include": "journals",
                    },
                )
                issues = data.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < limit:
                    break
                offset += limit

            except Exception as e:
                logger.error(f"Failed to fetch issues: {e}")
                break

        return all_issues

    def analyze_daily_trend(self, project_id: int, days: int = 7) -> Dict[str, Any]:
        """
        analysis每日trend（过去 N 天）

        Args:
            project_id: project ID
            days: analysis天数

        Returns:
            trendanalysisresult
        """
        issues = self.get_historical_issues(project_id, days)

        # 按datestatistics
        daily_stats = {}
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # initialize每日statistics
        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            daily_stats[date_str] = {
                "date": date_str,
                "new": 0,
                "closed": 0,
                "total_open": 0,
                "total_closed": 0,
            }
            current += timedelta(days=1)

        # statistics每日新增和shutdown
        for issue in issues:
            created_on = issue.get("created_on", "")
            closed_on = issue.get("closed_on", "")
            status = issue.get("status", {}).get("name", "")

            # statistics新增
            if created_on:
                try:
                    created_date = datetime.fromisoformat(
                        created_on.replace("Z", "+00:00")
                    ).date()
                    if start_date <= created_date <= end_date:
                        date_str = created_date.isoformat()
                        if date_str in daily_stats:
                            daily_stats[date_str]["new"] += 1
                except:
                    pass

            # statisticsshutdown
            if closed_on and status == "已shutdown":
                try:
                    closed_date = datetime.fromisoformat(
                        closed_on.replace("Z", "+00:00")
                    ).date()
                    if start_date <= closed_date <= end_date:
                        date_str = closed_date.isoformat()
                        if date_str in daily_stats:
                            daily_stats[date_str]["closed"] += 1
                except:
                    pass

        # 计算累计value
        total_open = 0
        total_closed = 0
        for date_str in sorted(daily_stats.keys()):
            stats = daily_stats[date_str]
            total_open += stats["new"] - stats["closed"]
            total_closed += stats["closed"]
            stats["total_open"] = total_open
            stats["total_closed"] = total_closed

        # 转换为list
        trend_data = [daily_stats[k] for k in sorted(daily_stats.keys())]

        # 计算trend指标
        if len(trend_data) >= 2:
            latest = trend_data[-1]
            previous = trend_data[-2]

            new_change = latest["new"] - previous["new"]
            closed_change = latest["closed"] - previous["closed"]

            trend_direction = (
                "improving"
                if closed_change > 0
                else "declining" if closed_change < 0 else "stable"
            )
        else:
            trend_direction = "stable"

        return {
            "project_id": project_id,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_stats": trend_data,
            "trend_direction": trend_direction,
            "summary": self._generate_trend_summary(trend_data),
        }

    def analyze_weekly_trend(self, project_id: int, weeks: int = 4) -> Dict[str, Any]:
        """
        analysis每周trend（过去 N 周）

        Args:
            project_id: project ID
            weeks: analysis周数

        Returns:
            trendanalysisresult
        """
        issues = self.get_historical_issues(project_id, weeks * 7)

        # 按周statistics
        weekly_stats = {}
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks)

        # initialize每周statistics
        current = start_date
        week_num = 1
        while current < end_date:
            week_end = current + timedelta(days=6)
            if week_end > end_date:
                week_end = end_date

            week_key = f"W{week_num}_{current.isoformat()}"
            weekly_stats[week_key] = {
                "week": week_key,
                "start_date": current.isoformat(),
                "end_date": week_end.isoformat(),
                "new": 0,
                "closed": 0,
                "total_open": 0,
                "total_closed": 0,
            }

            current += timedelta(days=7)
            week_num += 1

        # statistics每周data
        for issue in issues:
            created_on = issue.get("created_on", "")
            closed_on = issue.get("closed_on", "")
            status = issue.get("status", {}).get("name", "")

            if created_on:
                try:
                    created_date = datetime.fromisoformat(
                        created_on.replace("Z", "+00:00")
                    ).date()
                    for week_key, stats in weekly_stats.items():
                        week_start = datetime.fromisoformat(stats["start_date"]).date()
                        week_end = datetime.fromisoformat(stats["end_date"]).date()
                        if week_start <= created_date <= week_end:
                            stats["new"] += 1
                            break
                except:
                    pass

            if closed_on and status == "已shutdown":
                try:
                    closed_date = datetime.fromisoformat(
                        closed_on.replace("Z", "+00:00")
                    ).date()
                    for week_key, stats in weekly_stats.items():
                        week_start = datetime.fromisoformat(stats["start_date"]).date()
                        week_end = datetime.fromisoformat(stats["end_date"]).date()
                        if week_start <= closed_date <= week_end:
                            stats["closed"] += 1
                            break
                except:
                    pass

        # 计算累计value
        total_open = 0
        total_closed = 0
        for week_key in sorted(weekly_stats.keys()):
            stats = weekly_stats[week_key]
            total_open += stats["new"] - stats["closed"]
            total_closed += stats["closed"]
            stats["total_open"] = total_open
            stats["total_closed"] = total_closed

        # 转换为list
        trend_data = [weekly_stats[k] for k in sorted(weekly_stats.keys())]

        # 计算trend
        if len(trend_data) >= 2:
            latest = trend_data[-1]
            previous = trend_data[-2]

            velocity = latest["closed"] - previous["closed"]
            trend_direction = (
                "improving"
                if velocity > 0
                else "declining" if velocity < 0 else "stable"
            )
        else:
            trend_direction = "stable"

        return {
            "project_id": project_id,
            "period_weeks": weeks,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "weekly_stats": trend_data,
            "trend_direction": trend_direction,
            "summary": self._generate_trend_summary(trend_data, "weekly"),
        }

    def analyze_monthly_trend(self, project_id: int, months: int = 6) -> Dict[str, Any]:
        """
        analysis每月trend（过去 N 月）

        Args:
            project_id: project ID
            months: analysis月数

        Returns:
            trendanalysisresult
        """
        issues = self.get_historical_issues(project_id, months * 30)

        # 按月statistics
        monthly_stats = {}
        now = datetime.now()

        for i in range(months):
            month_date = now.date() - timedelta(days=i * 30)
            month_key = month_date.strftime("%Y-%m")

            # 计算月初和月末
            if i == 0:
                start = now.date().replace(day=1)
                end = now.date()
            else:
                start = (now.date().replace(day=1) - timedelta(days=1)).replace(day=1)
                end = now.date().replace(day=1) - timedelta(days=1)

            monthly_stats[month_key] = {
                "month": month_key,
                "new": 0,
                "closed": 0,
                "total_open": 0,
                "total_closed": 0,
            }

        # statistics每月data
        for issue in issues:
            created_on = issue.get("created_on", "")
            closed_on = issue.get("closed_on", "")
            status = issue.get("status", {}).get("name", "")

            if created_on:
                try:
                    created_date = datetime.fromisoformat(
                        created_on.replace("Z", "+00:00")
                    ).date()
                    month_key = created_date.strftime("%Y-%m")
                    if month_key in monthly_stats:
                        monthly_stats[month_key]["new"] += 1
                except:
                    pass

            if closed_on and status == "已shutdown":
                try:
                    closed_date = datetime.fromisoformat(
                        closed_on.replace("Z", "+00:00")
                    ).date()
                    month_key = closed_date.strftime("%Y-%m")
                    if month_key in monthly_stats:
                        monthly_stats[month_key]["closed"] += 1
                except:
                    pass

        # 计算累计value
        total_open = 0
        total_closed = 0
        for month_key in sorted(monthly_stats.keys()):
            stats = monthly_stats[month_key]
            total_open += stats["new"] - stats["closed"]
            total_closed += stats["closed"]
            stats["total_open"] = total_open
            stats["total_closed"] = total_closed

        # 转换为list
        trend_data = [monthly_stats[k] for k in sorted(monthly_stats.keys())]

        # 计算trend
        if len(trend_data) >= 2:
            latest = trend_data[-1]
            previous = trend_data[-2]

            velocity = latest["closed"] - previous["closed"]
            trend_direction = (
                "improving"
                if velocity > 0
                else "declining" if velocity < 0 else "stable"
            )
        else:
            trend_direction = "stable"

        return {
            "project_id": project_id,
            "period_months": months,
            "monthly_stats": trend_data,
            "trend_direction": trend_direction,
            "summary": self._generate_trend_summary(trend_data, "monthly"),
        }

    def _generate_trend_summary(
        self, trend_data: List[Dict], period: str = "daily"
    ) -> Dict[str, Any]:
        """generatetrend摘要"""
        if not trend_data:
            return {}

        latest = trend_data[-1]

        # 计算平均value
        avg_new = sum(d["new"] for d in trend_data) / len(trend_data)
        avg_closed = sum(d["closed"] for d in trend_data) / len(trend_data)

        # 计算变化率
        if len(trend_data) >= 2:
            first = trend_data[0]
            change_rate = (
                (latest["total_closed"] - first["total_closed"])
                / max(first["total_closed"], 1)
            ) * 100
        else:
            change_rate = 0

        return {
            "total_new": sum(d["new"] for d in trend_data),
            "total_closed": sum(d["closed"] for d in trend_data),
            "avg_new_per_period": round(avg_new, 2),
            "avg_closed_per_period": round(avg_closed, 2),
            "change_rate_percent": round(change_rate, 2),
            "trend": (
                "up" if change_rate > 5 else "down" if change_rate < -5 else "stable"
            ),
        }


# Convenience functions


def analyze_project_trend(
    project_id: int, report_type: str = "daily", period: int = 7
) -> Dict[str, Any]:
    """
    analysisprojecttrend

    Args:
        project_id: project ID
        report_type: reportclass型 (daily/weekly/monthly)
        period: period (天数/周数/月数)

    Returns:
        trendanalysisresult
    """
    service = TrendAnalysisService()

    if report_type == "daily":
        return service.analyze_daily_trend(project_id, period)
    elif report_type == "weekly":
        return service.analyze_weekly_trend(project_id, period)
    elif report_type == "monthly":
        return service.analyze_monthly_trend(project_id, period)
    else:
        return {"error": f"Invalid report type: {report_type}"}
