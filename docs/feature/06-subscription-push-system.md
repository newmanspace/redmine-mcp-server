# 订阅推送系统 - 完整实现

**版本**: 1.0  
**日期**: 2026-02-27  
**状态**: ✅ 已完成

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                               │
│                    (Claude, VSCode, etc.)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ MCP Tools
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Server                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ subscription_tools.py                                     │  │
│  │  - subscribe_project()     # 创建订阅                      │  │
│  │  - unsubscribe_project()   # 取消订阅                      │  │
│  │  - list_my_subscriptions() # 查看订阅                      │  │
│  │  - get_subscription_stats() # 统计信息                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ subscription_push_tools.py (NEW)                          │  │
│  │  - push_subscription_reports()  # 手动触发推送            │  │
│  │  - send_project_report_email()  # 一次性发送邮件          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ subscription_      │  │ subscription_      │                │
│  │ service.py         │  │ push_service.py    │                │
│  │ ────────────────── │  │ ────────────────── │                │
│  │ CRUD 订阅配置       │  │ 执行推送逻辑       │                │
│  │ 存储到数据库        │  │ 获取项目统计       │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ PostgreSQL         │  │ Redmine API        │                │
│  │ ads_user_          │  │ - Projects         │                │
│  │ subscriptions      │  │ - Issues           │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心组件

### 1. 订阅管理 (`subscription_service.py`)

**功能**: 订阅配置的 CRUD 操作

**数据库表**: `warehouse.ads_user_subscriptions`

**主要方法**:
- `subscribe()` - 创建订阅
- `unsubscribe()` - 取消订阅
- `get_user_subscriptions()` - 获取用户订阅
- `list_all_subscriptions()` - 列出所有订阅
- `get_due_subscriptions()` - 获取到期应推送的订阅

### 2. 订阅推送 (`subscription_push_service.py`) ✨ NEW

**功能**: 执行实际的推送操作

**主要方法**:
- `get_project_stats()` - 从 Redmine API 获取项目统计
- `push_subscription()` - 推送单个订阅
- `push_due_subscriptions()` - 推送所有到期的订阅
- `send_email_report()` - 发送邮件报告

**支持的渠道**:
- ✅ Email (已实现)
- ⏳ DingTalk (待实现)
- ⏳ Telegram (待实现)

### 3. MCP 工具

#### subscription_tools.py
- `subscribe_project()` - 订阅项目
- `unsubscribe_project()` - 取消订阅
- `list_my_subscriptions()` - 查看订阅
- `get_subscription_stats()` - 订阅统计

#### subscription_push_tools.py ✨ NEW
- `push_subscription_reports()` - 手动触发推送
- `send_project_report_email()` - 一次性发送邮件

---

## 三、使用示例

### 1. 订阅项目日报

```python
# 订阅到邮箱
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    frequency="daily",
    level="detailed",
    push_time="09:00"
)
```

### 2. 查看我的订阅

```python
list_my_subscriptions()
# 返回：
# [
#   {
#     "subscription_id": "default_user:341:email",
#     "user_id": "default_user",
#     "project_id": 341,
#     "channel": "email",
#     "channel_id": "user@example.com",
#     "frequency": "daily",
#     "level": "detailed",
#     "push_time": "09:00",
#     "enabled": true
#   }
# ]
```

### 3. 手动触发推送测试

```python
# 推送所有每日订阅
push_subscription_reports(frequency="daily")

# 推送特定项目的订阅
push_subscription_reports(frequency="daily", project_id=341)
```

### 4. 一次性发送项目报告（不创建订阅）

```python
send_project_report_email(
    project_id=341,
    to_email="user@example.com",
    level="detailed"
)
```

---

## 四、数据流程

### 订阅创建流程

```
MCP Client
    │
    ▼
subscribe_project(project_id=341, channel="email", ...)
    │
    ▼
SubscriptionManager.subscribe()
    │
    ▼
INSERT INTO warehouse.ads_user_subscriptions
    │
    ▼
返回订阅结果
```

### 订阅推送流程

```
定时触发器 / MCP 工具调用
    │
    ▼
push_subscription_reports(frequency="daily")
    │
    ▼
SubscriptionPushService.push_due_subscriptions()
    │
    ▼
获取到期订阅列表
    │
    ▼
For each subscription:
    ├──► get_project_stats(project_id)
    │        │
    │        ▼
    │    Redmine API → 获取 Issue 数据
    │        │
    │        ▼
    │    统计数据 → 计算报表
    │
    ├──► send_email_report(to_email, project_name, stats)
    │        │
    │        ▼
    │    SMTP Server → 发送邮件
    │
    └──► 记录推送结果
```

---

## 五、邮件报告内容

### 简要报告 (Brief)

- Issue 总数
- 今日新增/关闭
- 未关闭数量

### 详细报告 (Detailed)

**概览**
- Issue 总数
- 今日新增
- 今日关闭
- 未关闭

**状态分布**
- 新建/进行中/已解决/已关闭

**优先级分布**
- 立刻/紧急/高/普通/低

**高优先级 Issue TOP 5**
- 主题、优先级、状态、负责人

**人员任务量 TOP 5**
- 姓名、Issue 数量

---

## 六、配置文件

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
DEFAULT_EMAIL=jenkins@fa-software.com
DEFAULT_DINGTALK_USER=default
DEFAULT_TELEGRAM_CHAT_ID=default
```

---

## 七、文件清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/redmine_mcp_server/dws/services/subscription_service.py` | 订阅管理 | ✅ |
| `src/redmine_mcp_server/dws/services/subscription_push_service.py` | 订阅推送 | ✅ NEW |
| `src/redmine_mcp_server/dws/services/email_service.py` | 邮件服务 | ✅ |
| `src/redmine_mcp_server/mcp/tools/subscription_tools.py` | 订阅 MCP 工具 | ✅ |
| `src/redmine_mcp_server/mcp/tools/subscription_push_tools.py` | 推送 MCP 工具 | ✅ NEW |
| `src/redmine_mcp_server/mcp/server.py` | MCP 服务器 | ✅ Updated |
| `init-scripts/07-ads-user-subscriptions.sql` | 数据库建表 | ✅ |
| `.env.docker` | 配置模板 | ✅ Updated |

---

## 八、测试验证

### 测试结果

```bash
# 测试订阅推送服务
python3 test_subscription_push.py

# 输出:
# ======================================================================
# 测试订阅推送服务
# ======================================================================
#
# 初始化订阅推送服务...
#
# 获取项目 341 统计数据...
# ✅ 获取到统计数据:
#    Issue 总数：540
#    未关闭：162
#    已关闭：378
#    今日新增：9
#    今日关闭：8
#
# 发送邮件到 jenkins@fa-software.com...
#
# ======================================================================
# ✅ 邮件发送成功!
# ======================================================================
```

---

## 九、待完善功能

### 1. 定时推送调度器

目前需要手动调用 MCP 工具触发推送，需要添加：

```python
# 在 scheduler/tasks.py 中添加
@scheduled_job('cron', hour=9, minute=0)
def auto_push_daily_reports():
    """每天 9:00 自动推送每日报告"""
    from .subscription_push_service import push_daily_reports
    push_daily_reports()
```

### 2. 其他推送渠道

- DingTalk 推送
- Telegram 推送

### 3. Redmine API 认证修复

目前 `python-redmine` 库的认证方式有问题，需要修复：
- 修改 `redmine_handler.py` 使用 URL 参数传递 API Key
- 修改 `ods_sync_service.py` 同上

---

## 十、总结

✅ **已完成**:
- 订阅配置管理 (CRUD)
- 订阅数据持久化 (PostgreSQL)
- 订阅推送服务
- 邮件报告发送
- MCP 工具接口
- 测试验证

⏳ **待完成**:
- 定时推送调度器
- 其他推送渠道 (DingTalk, Telegram)
- Redmine API 认证修复

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
