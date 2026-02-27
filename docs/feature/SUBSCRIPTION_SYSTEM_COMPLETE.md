# 订阅系统完整功能 - 文档总结

**版本**: 2.0  
**日期**: 2026-02-27  
**状态**: ✅ 已完成

---

## 一、核心功能

### 1. 报告类型

| 类型 | 说明 | 发送频率 | 趋势分析 |
|------|------|----------|----------|
| **日报** (daily) | 每日项目状态 | 每天 | 7 天趋势 |
| **周报** (weekly) | 每周项目总结 | 每周指定星期 | 4 周趋势 |
| **月报** (monthly) | 每月项目汇总 | 每月指定日期 | 6 月趋势 |

### 2. 报告级别

| 级别 | 内容 |
|------|------|
| **brief** | 关键指标概览（总数/新增/关闭/未关闭） |
| **detailed** | brief + 状态分布 + 优先级分布 + 高优先级 Issue + 人员任务量 |
| **comprehensive** | detailed + 趋势分析 + 完成率 + 平均解决时间 |

### 3. 发送渠道

- ✅ **Email** - SMTP 邮件推送
- ⏳ **DingTalk** - 钉钉机器人（待实现）
- ⏳ **Telegram** - Telegram Bot（待实现）

---

## 二、数据库表结构

### `warehouse.ads_user_subscriptions`

```sql
CREATE TABLE warehouse.ads_user_subscriptions (
    subscription_id   VARCHAR(255) PRIMARY KEY,
    user_id           VARCHAR(100) NOT NULL,
    project_id        INTEGER NOT NULL,
    channel           VARCHAR(50) NOT NULL,
    channel_id        VARCHAR(255) NOT NULL,
    
    -- 报告类型配置
    report_type       VARCHAR(20) DEFAULT 'daily',
    report_level      VARCHAR(20) DEFAULT 'brief',
    
    -- 发送时间配置
    send_time         VARCHAR(50),
    send_day_of_week  VARCHAR(10),
    send_day_of_month INTEGER,
    
    -- 趋势分析配置
    include_trend     BOOLEAN DEFAULT TRUE,
    trend_period_days INTEGER DEFAULT 7,
    
    enabled           BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP,
    updated_at        TIMESTAMP
);
```

---

## 三、MCP 工具使用

### 订阅日报

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

### 订阅周报

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    report_type="weekly",
    report_level="comprehensive",
    send_day_of_week="Mon",
    send_time="09:00",
    include_trend=True,
    trend_period_days=30
)
```

### 订阅月报

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    report_type="monthly",
    report_level="comprehensive",
    send_day_of_month=1,
    send_time="10:00",
    include_trend=True,
    trend_period_days=180
)
```

### 手动触发推送

```python
# 推送所有每日订阅
push_subscription_reports(frequency="daily")

# 推送特定项目
push_subscription_reports(frequency="daily", project_id=341)
```

---

## 四、报告内容示例

### 日报内容

**📈 概览**
- Issue 总数：540
- 今日新增：+9
- 今日关闭：8
- 未关闭：162

**📊 状态分布**
- 新建：15
- 进行中：20
- 已解决：8
- 已关闭：378

**⚡ 优先级分布**
- 立刻：2
- 紧急：5
- 高：12
- 普通：120

**🔥 高优先级 Issue**
| 主题 | 优先级 | 状态 | 负责人 |
|------|--------|------|--------|
| 系统登录失败 | 立刻 | 进行中 | 张三 |

**👥 人员任务量 TOP**
| 姓名 | Issue 数 |
|------|----------|
| 张三 | 25 |

**📊 趋势分析（7 天）**
- 总新增：45
- 总关闭：38
- 平均每日新增：6.4
- 平均每日关闭：5.4
- 趋势：improving

### 周报内容

**📈 概览**
- Issue 总数：540
- 本周新增：35
- 本周关闭：28
- 净变化：+7

**📊 趋势分析（4 周）**
- 第 1 周：新增 30, 关闭 25
- 第 2 周：新增 32, 关闭 28
- 第 3 周：新增 28, 关闭 30
- 第 4 周：新增 35, 关闭 28

### 月报内容

**📈 概览**
- Issue 总数：540
- 本月新增：120
- 本月关闭：95
- 净变化：+25
- 完成率：70.0%
- 平均解决天数：5.2

**📊 趋势分析（6 月）**
- 月度新增/关闭趋势图
- 累计 Issue 增长趋势
- 解决速度趋势

---

## 五、服务组件

### 1. `subscription_service.py`
- 订阅配置 CRUD
- 数据库持久化

### 2. `subscription_push_service.py`
- 推送执行逻辑
- 报告生成调用

### 3. `report_generation_service.py`
- 日报/周报/月报生成
- 统计数据计算

### 4. `trend_analysis_service.py`
- 每日/每周/每月趋势分析
- 趋势方向判断

### 5. `email_service.py`
- SMTP 邮件发送
- HTML 邮件模板生成

---

## 六、文件清单

| 文件 | 说明 |
|------|------|
| `init-scripts/07-ads-user-subscriptions.sql` | 数据库建表脚本 |
| `src/redmine_mcp_server/dws/services/subscription_service.py` | 订阅管理 |
| `src/redmine_mcp_server/dws/services/subscription_push_service.py` | 订阅推送 |
| `src/redmine_mcp_server/dws/services/report_generation_service.py` | 报告生成 |
| `src/redmine_mcp_server/dws/services/trend_analysis_service.py` | 趋势分析 |
| `src/redmine_mcp_server/dws/services/email_service.py` | 邮件服务 |
| `src/redmine_mcp_server/mcp/tools/subscription_tools.py` | 订阅 MCP 工具 |
| `src/redmine_mcp_server/mcp/tools/subscription_push_tools.py` | 推送 MCP 工具 |

---

## 七、配置示例

### .env.docker

```bash
# Redmine 配置
REDMINE_URL=http://redmine.fa-software.com
REDMINE_API_KEY=adabb6a1089a5ac90e5649f505029d28e1cc9bc7

# SMTP 配置
EMAIL_SMTP_SERVER=smtp.qiye.aliyun.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=jenkins@fa-software.com
EMAIL_SMTP_PASSWORD=***
EMAIL_SENDER_EMAIL=jenkins@fa-software.com
EMAIL_SENDER_NAME=Redmine MCP Server
EMAIL_USE_TLS=true

# 默认配置
DEFAULT_EMAIL=user@example.com
```

---

## 八、待完善功能

1. **定时调度器** - 自动在指定时间发送报告
2. **DingTalk 推送** - 钉钉机器人集成
3. **Telegram 推送** - Telegram Bot 集成
4. **PDF 导出** - 报告 PDF 格式导出
5. **自定义模板** - 用户自定义邮件模板

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
