# 邮件订阅功能

**版本**: 1.0  
**日期**: 2026-02-27  
**说明**: 支持通过邮件接收 Redmine 项目状态报告

---

## 一、功能概述

Redmine MCP Server 现在支持三种推送渠道：

| 渠道 | 说明 | 配置复杂度 |
|------|------|------------|
| **Email** 📧 | 通过 SMTP 发送邮件报告 | 简单 |
| **DingTalk** 💬 | 通过钉钉机器人推送 | 中等 |
| **Telegram** ✈️ | 通过 Telegram Bot 推送 | 中等 |

邮件订阅功能支持：
- 简要报告 (brief) - 包含关键指标概览
- 详细报告 (detailed) - 包含状态分布、优先级、高优先级 Issue、人员负载等

---

## 二、配置邮件服务

### 步骤 1: 配置 SMTP 服务器

在 `.env` 文件中添加以下配置：

```bash
# =====================================================
# Email Subscription Configuration
# =====================================================

# SMTP 服务器配置
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# 发件人配置
EMAIL_SENDER_EMAIL=your-email@gmail.com
EMAIL_SENDER_NAME=Redmine MCP Server

# 使用 TLS (推荐) 或 SSL
EMAIL_USE_TLS=true

# 默认订阅邮箱 (可选)
DEFAULT_EMAIL=user@example.com
```

### 步骤 2: 获取 SMTP 凭证

#### Gmail

1. 启用两步验证
2. 创建应用专用密码：https://myaccount.google.com/apppasswords
3. 使用应用专用密码作为 `EMAIL_SMTP_PASSWORD`

#### Outlook/Hotmail

1. 启用两步验证
2. 创建应用密码：https://account.microsoft.com/security
3. 使用应用密码

#### 企业邮箱

联系 IT 部门获取 SMTP 配置：
- SMTP 服务器地址
- SMTP 端口 (通常 587 for TLS, 465 for SSL)
- 认证凭据

### 步骤 3: 测试邮件服务

使用 MCP 工具测试邮件配置：

```python
# 测试 SMTP 连接
test_email_service()

# 测试发送邮件
test_email_service(to_email="your-email@example.com")
```

返回示例：
```json
{
  "connection": {
    "success": true,
    "message": "SMTP connection successful",
    "server": "smtp.gmail.com",
    "port": 587
  },
  "test_email": {
    "success": true,
    "message": "Email sent to your-email@example.com",
    "to": "your-email@example.com",
    "subject": "[Redmine MCP] 邮件服务测试"
  }
}
```

---

## 三、订阅项目报告

### 方法 1: 订阅到邮箱

```python
# 订阅项目到邮箱
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="your-email@example.com",
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

### 方法 2: 订阅到钉钉

```python
subscribe_project(
    project_id=341,
    channel="dingtalk",
    channel_id="dingtalk-user-id",
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

### 方法 3: 订阅到 Telegram

```python
subscribe_project(
    project_id=341,
    channel="telegram",
    channel_id="123456789",
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_id` | int | 是 | - | 项目 ID |
| `channel` | str | 否 | "dingtalk" | 推送渠道 (email/dingtalk/telegram) |
| `channel_id` | str | 否 | 自动检测 | 渠道 ID (邮箱/钉钉用户 ID/Telegram chat ID) |
| `frequency` | str | 否 | "daily" | 推送频率 (realtime/daily/weekly/monthly) |
| `level` | str | 否 | "brief" | 报告级别 (brief/detailed) |
| `push_time` | str | 否 | - | 推送时间 (daily 用 "09:00", weekly 用 "Mon 09:00") |

---

## 四、邮件报告示例

### 简要报告 (Brief)

```
主题：[Redmine] 江苏新顺 CIM - 项目状态简报

📊 江苏新顺 CIM - 项目状态简报
报告日期：2026-02-27

指标          数量
─────────────────
Issue 总数     156
今日新增       +5
今日关闭       3
未关闭         42
```

### 详细报告 (Detailed)

```
主题：[Redmine] 江苏新顺 CIM - 项目详细状态报告

📊 江苏新顺 CIM - 项目详细状态报告
报告日期：2026-02-27

📈 概览
─────────────────
Issue 总数     156
今日新增       +5
今日关闭       3
未关闭         42

📊 状态分布
─────────────────
状态          数量
新建          15
进行中        20
已解决        8
已关闭        113

⚡ 优先级分布
─────────────────
优先级        数量
立刻          2
紧急          5
高            12
普通          120
低            17

🔥 高优先级 Issue
─────────────────
主题                    优先级    负责人
系统登录失败            立刻      张三
数据同步异常            紧急      李四
...

👥 人员任务量 TOP
─────────────────
姓名      总数    进行中
张三      25      8
李四      20      6
...
```

---

## 五、管理订阅

### 查看我的订阅

```python
list_my_subscriptions()
```

返回：
```json
[
  {
    "subscription_id": "default_user:341:email",
    "user_id": "default_user",
    "project_id": 341,
    "channel": "email",
    "channel_id": "user@example.com",
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00",
    "enabled": true
  },
  {
    "subscription_id": "default_user:356:dingtalk",
    "user_id": "default_user",
    "project_id": 356,
    "channel": "dingtalk",
    "channel_id": "user123",
    "frequency": "daily",
    "level": "detailed",
    "push_time": "09:00",
    "enabled": true
  }
]
```

### 获取订阅统计

```python
get_subscription_stats()
```

返回：
```json
{
  "total_subscriptions": 15,
  "by_frequency": {
    "daily": 13,
    "weekly": 2
  },
  "by_channel": {
    "email": 8,
    "dingtalk": 5,
    "telegram": 2
  },
  "by_project": {
    "341": 3,
    "356": 2,
    "357": 2
  },
  "active_subscriptions": 15
}
```

### 取消订阅

```python
# 取消特定项目的订阅
unsubscribe_project(project_id=341)

# 取消所有订阅 (不传参数)
unsubscribe_project()
```

---

## 六、高级配置

### 多邮箱订阅

同一个项目可以订阅到多个邮箱：

```python
# 订阅到工作邮箱
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="work@example.com",
    frequency="daily",
    level="brief"
)

# 同时订阅到个人邮箱
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="personal@example.com",
    frequency="weekly",
    level="detailed",
    push_time="Mon 09:00"
)
```

### 混合渠道订阅

```python
# 工作日用钉钉接收简要报告
subscribe_project(
    project_id=341,
    channel="dingtalk",
    channel_id="user123",
    frequency="daily",
    level="brief",
    push_time="09:00"
)

# 周末用邮件接收详细报告
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    frequency="weekly",
    level="detailed",
    push_time="Sat 10:00"
)
```

---

## 七、故障排查

### 问题 1: 邮件发送失败

**错误信息**:
```
SMTP authentication failed: (535, b'5.7.8 Username and Password not accepted')
```

**解决方案**:
1. 检查用户名密码是否正确
2. Gmail 用户需要启用两步验证并创建应用专用密码
3. 检查是否启用了"允许不够安全的应用"

### 问题 2: 连接超时

**错误信息**:
```
SMTP error: [Errno 110] Connection timed out
```

**解决方案**:
1. 检查网络连接
2. 确认 SMTP 服务器地址和端口正确
3. 检查防火墙设置

### 问题 3: 证书验证失败

**错误信息**:
```
SMTP error: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**解决方案**:
1. 尝试使用 SSL 端口 (465) 代替 TLS 端口 (587)
2. 设置 `EMAIL_USE_TLS=false`

---

## 八、最佳实践

### 1. 选择合适的报告级别

- **Brief**: 适合每日快速浏览，包含关键指标
- **Detailed**: 适合周报复盘，包含详细分析

### 2. 选择合适的推送时间

- **Daily**: 建议设置在早上 9:00 (开始工作前)
- **Weekly**: 建议设置在周一早上或周五下午
- **Monthly**: 建议设置在月初第一天

### 3. 避免邮件过载

- 不要为同一项目订阅多个相同频率的报告
- 优先使用 Brief 级别进行日常监控
- 使用 Detailed 级别进行周期性复盘

---

## 九、相关文件

| 文件 | 说明 |
|------|------|
| `src/redmine_mcp_server/dws/services/email_service.py` | 邮件服务实现 |
| `src/redmine_mcp_server/mcp/tools/subscription_tools.py` | 订阅 MCP 工具 |
| `.env.example` | 环境变量配置模板 |

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
