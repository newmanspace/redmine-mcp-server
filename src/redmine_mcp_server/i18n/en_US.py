# English (US) Translations
# 英文翻译

REPORT_TYPES = {
    "daily": "Daily Report",
    "weekly": "Weekly Report",
    "monthly": "Monthly Report",
}

REPORT_LEVELS = {
    "brief": "Brief",
    "detailed": "Detailed",
    "comprehensive": "Comprehensive",
}

STATUS_NAMES = {
    "新建": "New",
    "进行中": "In Progress",
    "已解决": "Resolved",
    "已关闭": "Closed",
    "反馈": "Feedback",
}

PRIORITY_NAMES = {
    "立刻": "Immediate",
    "紧急": "Urgent",
    "高": "High",
    "普通": "Normal",
    "低": "Low",
}

# Email subjects
EMAIL_SUBJECTS = {
    "daily": "[Redmine] {project_name} - Daily Report ({date})",
    "weekly": "[Redmine] {project_name} - Weekly Report ({date_range})",
    "monthly": "[Redmine] {project_name} - Monthly Report ({month})",
}

# Email content
EMAIL_CONTENT = {
    "header": "📊 {project_name} - Project {report_type}",
    "report_date": "Report Date: {date}",
    "report_month": "Report Month: {month}",
    "report_week": "Report Period: {start} to {end}",
    "overview": "📈 Overview",
    "status_distribution": "📋 Status Distribution",
    "priority_distribution": "⚡ Priority Distribution",
    "high_priority_issues": "🔥 High Priority Issues",
    "assignees_workload": "👥 Top Assignees",
    "trend_analysis": "📊 Trend Analysis",
    "metrics": {
        "total_issues": "Total Issues",
        "today_new": "New Today",
        "today_closed": "Closed Today",
        "week_new": "New This Week",
        "week_closed": "Closed This Week",
        "month_new": "New This Month",
        "month_closed": "Closed This Month",
        "open_issues": "Open",
        "closed_issues": "Closed",
        "net_change": "Net Change",
        "completion_rate": "Completion Rate",
        "avg_resolution_days": "Avg Resolution Days",
    },
    "trend": {
        "analysis_period": "Analysis Period",
        "trend_direction": "Trend Direction",
        "total_new": "Total New",
        "total_closed": "Total Closed",
        "avg_per_period": "Avg per Period",
        "change_rate": "Change Rate",
        "improving": "Improving",
        "declining": "Declining",
        "stable": "Stable",
    },
    "footer": {
        "auto_sent": "This email was automatically sent by Redmine MCP Server",
        "sent_time": "Sent Time",
        "contact_admin": "Contact system administrator for issues",
    },
}

# Subscription messages
SUBSCRIPTION_MESSAGES = {
    "subscribed": "Subscribed to {report_type} for project {project_id}",
    "unsubscribed": "Cancelled {count} subscriptions",
    "not_found": "No matching subscription found",
}

# Day names
DAYS_OF_WEEK = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday",
}

# Month names
MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
