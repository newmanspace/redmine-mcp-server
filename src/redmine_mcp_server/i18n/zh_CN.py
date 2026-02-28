# Chinese (Simplified) Translations
# 简体中文翻译

REPORT_TYPES = {"daily": "日报", "weekly": "周报", "monthly": "月报"}

REPORT_LEVELS = {"brief": "简要", "detailed": "详细", "comprehensive": "完整"}

STATUS_NAMES = {
    "新建": "新建",
    "进行中": "进行中",
    "已解决": "已解决",
    "已关闭": "已关闭",
    "反馈": "反馈",
}

PRIORITY_NAMES = {
    "立刻": "立刻",
    "紧急": "紧急",
    "高": "高",
    "普通": "普通",
    "低": "低",
}

# Email subjects
EMAIL_SUBJECTS = {
    "daily": "[Redmine] {project_name} - 项目日报 ({date})",
    "weekly": "[Redmine] {project_name} - 项目周报 ({date_range})",
    "monthly": "[Redmine] {project_name} - 项目月报 ({month})",
}

# Email content
EMAIL_CONTENT = {
    "header": "📊 {project_name} - 项目{report_type}",
    "report_date": "报告日期：{date}",
    "report_month": "报告月份：{month}",
    "report_week": "报告周期：{start} 至 {end}",
    "overview": "📈 概览",
    "status_distribution": "📋 状态分布",
    "priority_distribution": "⚡ 优先级分布",
    "high_priority_issues": "🔥 高优先级 Issue",
    "assignees_workload": "👥 人员任务量 TOP",
    "trend_analysis": "📊 趋势分析",
    "metrics": {
        "total_issues": "Issue 总数",
        "today_new": "今日新增",
        "today_closed": "今日关闭",
        "week_new": "本周新增",
        "week_closed": "本周关闭",
        "month_new": "本月新增",
        "month_closed": "本月关闭",
        "open_issues": "未关闭",
        "closed_issues": "已关闭",
        "net_change": "净变化",
        "completion_rate": "完成率",
        "avg_resolution_days": "平均解决天数",
    },
    "trend": {
        "analysis_period": "分析周期",
        "trend_direction": "趋势方向",
        "total_new": "总新增",
        "total_closed": "总关闭",
        "avg_per_period": "平均每期",
        "change_rate": "变化率",
        "improving": "改善",
        "declining": "下降",
        "stable": "稳定",
    },
    "footer": {
        "auto_sent": "此邮件由 Redmine MCP Server 自动发送",
        "sent_time": "发送时间",
        "contact_admin": "如有问题，请联系系统管理员",
    },
}

# Subscription messages
SUBSCRIPTION_MESSAGES = {
    "subscribed": "已订阅项目 {project_id} 的{report_type}报告",
    "unsubscribed": "已取消 {count} 个订阅",
    "not_found": "未找到匹配的订阅",
}

# Day names
DAYS_OF_WEEK = {
    "Mon": "周一",
    "Tue": "周二",
    "Wed": "周三",
    "Thu": "周四",
    "Fri": "周五",
    "Sat": "周六",
    "Sun": "周日",
}

# Month names
MONTHS = {
    1: "一月",
    2: "二月",
    3: "三月",
    4: "四月",
    5: "五月",
    6: "六月",
    7: "七月",
    8: "八月",
    9: "九月",
    10: "十月",
    11: "十一月",
    12: "十二月",
}
