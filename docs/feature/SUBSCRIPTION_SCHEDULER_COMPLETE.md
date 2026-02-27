# 订阅定时调度器 - 完整实现

**版本**: 3.0  
**日期**: 2026-02-27  
**状态**: ✅ 已完成

---

## 一、定时任务配置

### 自动调度任务

| 任务 | 触发时间 | 说明 |
|------|----------|------|
| **日报** | 每天早上 9:00 | 发送所有订阅的日报 |
| **周报** | 每周一早上 9:00 | 发送所有订阅的周报 |
| **月报** | 每月 1 号早上 10:00 | 发送所有订阅的月报 |
| **自定义检查** | 每分钟 | 检查是否有自定义时间的订阅需要发送 |

### 时区设置

- 默认时区：**Asia/Shanghai** (东八区)
- 可在代码中修改 `timezone` 参数

---

## 二、MCP 工具

### 1. 手动触发推送

```python
# 推送日报
push_subscription_reports(report_type="daily")

# 推送周报
push_subscription_reports(report_type="weekly")

# 推送特定项目的日报
push_subscription_reports(report_type="daily", project_id=341)
```

### 2. 发送一次性报告

```python
# 发送日报
send_project_report_email(
    project_id=341,
    to_email="user@example.com",
    report_type="daily",
    report_level="brief"
)

# 发送包含趋势分析的周报
send_project_report_email(
    project_id=341,
    to_email="manager@example.com",
    report_type="weekly",
    report_level="comprehensive",
    include_trend=True
)
```

### 3. 查看调度器状态

```python
get_subscription_scheduler_status()
# 返回:
# {
#   "status": "running",
#   "job_count": 4,
#   "jobs": [
#     {
#       "id": "daily_subscription_reports",
#       "name": "Send daily subscription reports",
#       "next_run": "2026-02-28T09:00:00+08:00",
#       "trigger": "cron[hour=9, minute=0]"
#     },
#     ...
#   ]
# }
```

---

## 三、订阅配置示例

### 订阅日报 - 每天 9 点接收

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    report_type="daily",
    report_level="detailed",
    send_time="09:00",
    include_trend=True,
    trend_period_days=7
)
```

### 订阅周报 - 每周一 9 点接收

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="manager@example.com",
    report_type="weekly",
    report_level="comprehensive",
    send_day_of_week="Mon",
    send_time="09:00",
    include_trend=True,
    trend_period_days=30
)
```

### 订阅月报 - 每月 1 号 10 点接收

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="ceo@example.com",
    report_type="monthly",
    report_level="comprehensive",
    send_day_of_month=1,
    send_time="10:00",
    include_trend=True,
    trend_period_days=180
)
```

### 自定义时间订阅

```python
# 每天下午 5 点接收日报
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    report_type="daily",
    send_time="17:00"  # 下午 5 点
)

# 每周五下午 4 点接收周报
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="team@example.com",
    report_type="weekly",
    send_day_of_week="Fri",
    send_time="16:00"
)
```

---

## 四、调度器工作流程

### 启动流程

```
服务器启动
    │
    ▼
main() 函数
    │
    ├──► 1. 初始化订阅管理器
    │      - 加载数据库连接
    │      - 读取订阅配置
    │
    ├──► 2. 初始化订阅调度器
    │      - 创建 BackgroundScheduler
    │      - 注册定时任务
    │      - 启动调度器
    │
    └──► 3. 初始化数据同步调度器
           - 每 10 分钟同步 Redmine 数据
```

### 日报发送流程 (每天 9:00)

```
09:00:00 - 定时任务触发
    │
    ▼
SubscriptionScheduler._send_daily_reports()
    │
    ▼
SubscriptionPushService.push_due_subscriptions("daily")
    │
    ├──► 获取所有 report_type='daily' 的订阅
    │
    ├──► For each subscription:
    │      ├──► 生成报告 (ReportGenerationService)
    │      │      - 获取项目统计
    │      │      - 获取趋势分析
    │      │
    │      ├──► 发送邮件 (EmailService)
    │      │      - 生成 HTML 邮件
    │      │      - SMTP 发送
    │      │
    │      └──► 记录结果
    │
    └──► 返回汇总结果
```

### 自定义时间检查流程 (每分钟)

```
每分钟
    │
    ▼
SubscriptionScheduler._check_custom_time_subscriptions()
    │
    ├──► 获取所有订阅
    │
    ├──► For each subscription:
    │      ├──► 检查时间是否匹配
    │      │      - send_time == 当前时间
    │      │      - report_type 匹配 (daily/weekly/monthly)
    │      │      - send_day_of_week/send_day_of_month 匹配
    │      │
    │      └──► 如果匹配，发送报告
    │
    └──► 完成检查
```

---

## 五、文件清单

| 文件 | 说明 |
|------|------|
| `src/redmine_mcp_server/scheduler/subscription_scheduler.py` | 订阅调度器 |
| `src/redmine_mcp_server/main.py` | 主入口（集成调度器） |
| `src/redmine_mcp_server/mcp/tools/subscription_push_tools.py` | MCP 工具 |
| `src/redmine_mcp_server/dws/services/subscription_service.py` | 订阅管理 |
| `src/redmine_mcp_server/dws/services/subscription_push_service.py` | 推送执行 |
| `src/redmine_mcp_server/dws/services/report_generation_service.py` | 报告生成 |
| `src/redmine_mcp_server/dws/services/trend_analysis_service.py` | 趋势分析 |
| `src/redmine_mcp_server/dws/services/email_service.py` | 邮件发送 |

---

## 六、测试验证

### 测试调度器状态

```python
# 查看调度器状态
get_subscription_scheduler_status()

# 预期输出:
{
  "status": "running",
  "job_count": 4,
  "jobs": [
    {
      "id": "daily_subscription_reports",
      "name": "Send daily subscription reports",
      "next_run": "2026-02-28T09:00:00+08:00",
      "trigger": "cron[hour=9, minute=0]"
    },
    {
      "id": "weekly_subscription_reports",
      "name": "Send weekly subscription reports",
      "next_run": "2026-03-02T09:00:00+08:00",
      "trigger": "cron[hour=9, minute=0, day_of_week=mon]"
    },
    {
      "id": "monthly_subscription_reports",
      "name": "Send monthly subscription reports",
      "next_run": "2026-03-01T10:00:00+08:00",
      "trigger": "cron[hour=10, minute=0, day=1]"
    },
    {
      "id": "check_custom_subscriptions",
      "name": "Check custom subscriptions",
      "next_run": "2026-02-27T23:20:00+08:00",
      "trigger": "interval[0:01:00]"
    }
  ]
}
```

### 手动触发测试

```python
# 测试日报推送
push_subscription_reports(report_type="daily")

# 测试周报推送
push_subscription_reports(report_type="weekly")

# 测试月报推送
push_subscription_reports(report_type="monthly")
```

---

## 七、配置说明

### 环境变量

```bash
# 时区配置（可选，默认 Asia/Shanghai）
TZ=Asia/Shanghai

# SMTP 配置（必需）
EMAIL_SMTP_SERVER=smtp.qiye.aliyun.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=jenkins@fa-software.com
EMAIL_SMTP_PASSWORD=***
EMAIL_SENDER_EMAIL=jenkins@fa-software.com
EMAIL_SENDER_NAME=Redmine MCP Server
EMAIL_USE_TLS=true
```

### 数据库表

```sql
-- 订阅配置表
warehouse.ads_user_subscriptions

-- 字段说明
report_type       -- daily/weekly/monthly
report_level      -- brief/detailed/comprehensive
send_time         -- HH:MM 格式
send_day_of_week  -- Mon/Tue/Wed/Thu/Fri/Sat/Sun
send_day_of_month -- 1-31
include_trend     -- true/false
trend_period_days -- 天数
```

---

## 八、日志示例

### 启动日志

```
2026-02-27 23:00:00 INFO     Redmine MCP Server v0.10.0
2026-02-27 23:00:00 INFO     Starting with transport: streamable-http
2026-02-27 23:00:00 INFO     Subscription manager initialized
2026-02-27 23:00:00 INFO     Subscription scheduler started (auto-send reports)
2026-02-27 23:00:00 INFO     Scheduled: Daily reports at 09:00
2026-02-27 23:00:00 INFO     Scheduled: Weekly reports on Monday 09:00
2026-02-27 23:00:00 INFO     Scheduled: Monthly reports on 1st day 10:00
2026-02-27 23:00:00 INFO     Scheduled: Check custom subscriptions every minute
2026-02-27 23:00:00 INFO     Warehouse sync scheduler started
```

### 日报发送日志

```
2026-02-28 09:00:00 INFO     Sending daily subscription reports...
2026-02-28 09:00:01 INFO     Sent subscription: default_user:341:email
2026-02-28 09:00:02 INFO     Sent subscription: default_user:356:email
2026-02-28 09:00:03 INFO     Daily reports sent: {'total': 2, 'success': 2, 'failed': 0}
```

---

## 九、故障排查

### 问题 1: 调度器未启动

**症状**: `get_subscription_scheduler_status()` 返回 `not_initialized`

**解决**:
1. 检查服务器日志是否有错误
2. 确认 APScheduler 库已安装：`pip list | grep APScheduler`
3. 重启服务器

### 问题 2: 报告未按时发送

**症状**: 到了指定时间没有收到邮件

**解决**:
1. 检查订阅配置是否正确 (`list_my_subscriptions()`)
2. 检查 `send_time` 格式是否为 `HH:MM`
3. 查看日志确认是否有错误
4. 手动触发测试：`push_subscription_reports(report_type="daily")`

### 问题 3: 自定义时间不生效

**症状**: 设置了自定义时间但没有发送

**解决**:
1. 确认 `send_time` 格式正确
2. 周报需要设置 `send_day_of_week`
3. 月报需要设置 `send_day_of_month`
4. 检查时区设置是否正确

---

## 十、最佳实践

### 1. 报告时间选择

- **日报**: 建议 09:00 (工作开始前) 或 17:00 (下班前总结)
- **周报**: 建议周一 09:00 (周计划) 或周五 16:00 (周总结)
- **月报**: 建议每月 1 号或最后一天

### 2. 报告级别选择

- **团队成员**: `detailed` - 了解项目详情
- **项目经理**: `comprehensive` - 完整分析 + 趋势
- **高层管理**: `brief` - 关键指标即可

### 3. 趋势分析周期

- **日报**: 7 天趋势 (看近期变化)
- **周报**: 30 天趋势 (看月度变化)
- **月报**: 180 天趋势 (看半年变化)

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
