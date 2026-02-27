# 国际化 (i18n) 支持

**版本**: 1.0  
**日期**: 2026-02-27  
**状态**: ✅ 已完成

---

## 一、功能概述

订阅系统现在支持：
- ✅ **中英文双语** - 报告内容根据订阅人语言偏好生成
- ✅ **订阅人信息** - 记录姓名和邮箱
- ✅ **语言偏好** - 每个订阅可独立设置语言
- ✅ **自动翻译** - 邮件内容、主题、指标名称自动翻译

---

## 二、文件结构

```
src/redmine_mcp_server/i18n/
├── __init__.py          # i18n 模块入口
├── config.py            # 配置文件
├── zh_CN.py             # 中文翻译
└── en_US.py             # 英文翻译
```

---

## 三、数据库变更

### 新增字段

`warehouse.ads_user_subscriptions` 表新增：

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_name` | VARCHAR(200) | 订阅人姓名 |
| `user_email` | VARCHAR(255) | 订阅人邮箱 |
| `language` | VARCHAR(10) | 语言偏好 (zh_CN/en_US) |

### 索引

- `idx_ads_user_subscriptions_user_email` - 按邮箱查询
- `idx_ads_user_subscriptions_language` - 按语言查询
- `idx_ads_user_subscriptions_report_type_language_enabled` - 复合索引（报告类型 + 语言）

---

## 四、使用示例

### 订阅中文日报

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    user_name="张三",
    user_email="user@example.com",
    report_type="daily",
    report_level="detailed",
    language="zh_CN",  # 中文
    send_time="09:00"
)
```

### 订阅英文周报

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="manager@example.com",
    user_name="John Doe",
    user_email="manager@example.com",
    report_type="weekly",
    report_level="comprehensive",
    language="en_US",  # English
    send_day_of_week="Mon",
    send_time="09:00"
)
```

### 订阅英文月报

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="ceo@example.com",
    user_name="CEO",
    user_email="ceo@example.com",
    report_type="monthly",
    report_level="comprehensive",
    language="en_US",
    send_day_of_month=1,
    send_time="10:00"
)
```

---

## 五、翻译内容

### 报告类型

| Key | zh_CN | en_US |
|-----|-------|-------|
| daily | 日报 | Daily Report |
| weekly | 周报 | Weekly Report |
| monthly | 月报 | Monthly Report |

### 报告级别

| Key | zh_CN | en_US |
|-----|-------|-------|
| brief | 简要 | Brief |
| detailed | 详细 | Detailed |
| comprehensive | 完整 | Comprehensive |

### 状态名称

| Key | zh_CN | en_US |
|-----|-------|-------|
| 新建 | 新建 | New |
| 进行中 | 进行中 | In Progress |
| 已解决 | 已解决 | Resolved |
| 已关闭 | 已关闭 | Closed |

### 优先级名称

| Key | zh_CN | en_US |
|-----|-------|-------|
| 立刻 | 立刻 | Immediate |
| 紧急 | 紧急 | Urgent |
| 高 | 高 | High |
| 普通 | 普通 | Normal |
| 低 | 低 | Low |

### 邮件主题

**中文**:
- 日报：`[Redmine] 江苏新顺 CIM - 项目日报 (2026-02-27)`
- 周报：`[Redmine] 江苏新顺 CIM - 项目周报 (2026-02-24 至 2026-03-02)`
- 月报：`[Redmine] 江苏新顺 CIM - 项目月报 (2026-02)`

**English**:
- Daily: `[Redmine] Jiangsu Xinshun CIM - Daily Report (2026-02-27)`
- Weekly: `[Redmine] Jiangsu Xinshun CIM - Weekly Report (2026-02-24 to 2026-03-02)`
- Monthly: `[Redmine] Jiangsu Xinshun CIM - Monthly Report (2026-02)`

### 邮件内容

**中文**:
- 📈 概览
- 📋 状态分布
- ⚡ 优先级分布
- 🔥 高优先级 Issue
- 👥 人员任务量 TOP
- 📊 趋势分析

**English**:
- 📈 Overview
- 📋 Status Distribution
- ⚡ Priority Distribution
- 🔥 High Priority Issues
- 👥 Top Assignees
- 📊 Trend Analysis

### 指标名称

| Key | zh_CN | en_US |
|-----|-------|-------|
| total_issues | Issue 总数 | Total Issues |
| today_new | 今日新增 | New Today |
| today_closed | 今日关闭 | Closed Today |
| open_issues | 未关闭 | Open |
| closed_issues | 已关闭 | Closed |
| completion_rate | 完成率 | Completion Rate |

### 趋势分析

| Key | zh_CN | en_US |
|-----|-------|-------|
| improving | 改善 | Improving |
| declining | 下降 | Declining |
| stable | 稳定 | Stable |
| analysis_period | 分析周期 | Analysis Period |
| trend_direction | 趋势方向 | Trend Direction |

---

## 六、API 使用

### 获取翻译

```python
from redmine_mcp_server.i18n import get_translations

# 获取中文翻译
zh_translations = get_translations('zh_CN')

# 获取英文翻译
en_translations = get_translations('en_US')

# 获取默认语言翻译
default_translations = get_translations()
```

### 使用辅助函数

```python
from redmine_mcp_server.i18n import (
    get_report_type_name,
    get_status_name,
    get_priority_name,
    format_email_subject,
    get_metric_name
)

# 获取报告类型名称
get_report_type_name('daily', 'zh_CN')  # '日报'
get_report_type_name('daily', 'en_US')  # 'Daily Report'

# 获取状态名称
get_status_name('新建', 'zh_CN')  # '新建'
get_status_name('新建', 'en_US')  # 'New'

# 格式化邮件主题
format_email_subject('daily', 'Project A', '2026-02-27', 'zh_CN')
# '[Redmine] Project A - 项目日报 (2026-02-27)'

format_email_subject('monthly', 'Project A', '2026-02', 'en_US')
# '[Redmine] Project A - Monthly Report (2026-02)'
```

---

## 七、邮件示例

### 中文日报

```
主题：[Redmine] 江苏新顺 CIM - 项目日报 (2026-02-27)

📊 江苏新顺 CIM - 项目日报
报告日期：2026-02-27

📈 概览
┌──────────────┬──────┐
│ 指标         │ 数量 │
├──────────────┼──────┤
│ Issue 总数   │ 540  │
│ 今日新增     │ +9   │
│ 今日关闭     │ 8    │
│ 未关闭       │ 162  │
└──────────────┴──────┘

📋 状态分布
新建：15
进行中：20
已解决：8
已关闭：378

📊 趋势分析
分析周期：7 天
趋势方向：改善
总新增：45
总关闭：38
```

### English Daily Report

```
Subject: [Redmine] Jiangsu Xinshun CIM - Daily Report (2026-02-27)

📊 Jiangsu Xinshun CIM - Daily Report
Report Date: 2026-02-27

📈 Overview
┌──────────────┬──────┐
│ Metric       │ Count│
├──────────────┼──────┤
│ Total Issues │ 540  │
│ New Today    │ +9   │
│ Closed Today │ 8    │
│ Open         │ 162  │
└──────────────┴──────┘

📋 Status Distribution
New: 15
In Progress: 20
Resolved: 8
Closed: 378

📊 Trend Analysis
Analysis Period: 7 days
Trend Direction: Improving
Total New: 45
Total Closed: 38
```

---

## 八、配置

### 环境变量

```bash
# 默认语言
DEFAULT_LANGUAGE=zh_CN

# 支持的语言
SUPPORTED_LANGUAGES=zh_CN,en_US
```

### 数据库配置

```sql
-- 查询所有中文订阅
SELECT * FROM warehouse.ads_user_subscriptions 
WHERE language = 'zh_CN' AND enabled = true;

-- 查询所有英文订阅
SELECT * FROM warehouse.ads_user_subscriptions 
WHERE language = 'en_US' AND enabled = true;
```

---

## 九、待办事项

### 已完成
- ✅ i18n 模块架构
- ✅ 中英文翻译文件
- ✅ 数据库字段扩展
- ✅ 订阅 API 支持语言参数
- ✅ 邮件主题翻译
- ✅ 指标名称翻译

### 待完成
- ⏳ 邮件正文翻译集成
- ⏳ 趋势分析翻译集成
- ⏳ MCP 工具参数更新
- ⏳ 数据库迁移脚本
- ⏳ 更多语言支持（日语/韩语等）

---

## 十、测试

### 测试中文订阅

```python
# 订阅中文日报
subscribe_project(
    project_id=341,
    user_name="张三",
    user_email="zhangsan@example.com",
    language="zh_CN",
    report_type="daily"
)

# 验证翻译
from redmine_mcp_server.i18n import get_report_type_name
assert get_report_type_name('daily', 'zh_CN') == '日报'
```

### 测试英文订阅

```python
# 订阅英文日报
subscribe_project(
    project_id=341,
    user_name="John Doe",
    user_email="john@example.com",
    language="en_US",
    report_type="daily"
)

# 验证翻译
from redmine_mcp_server.i18n import get_report_type_name
assert get_report_type_name('daily', 'en_US') == 'Daily Report'
```

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
