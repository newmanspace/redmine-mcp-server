# 订阅功能扩展 - 邮件推送支持

**版本**: 1.0  
**日期**: 2026-02-27  
**说明**: 为订阅系统添加邮件推送渠道支持

---

## 一、变更概述

### 变更前
- 仅支持 DingTalk 和 Telegram 两种推送渠道
- 需要配置机器人和 Webhook

### 变更后
- 新增 **Email** 推送渠道 📧
- 支持 SMTP 邮件发送
- 提供简要 (brief) 和详细 (detailed) 两种报告模板
- 支持 HTML 格式邮件

---

## 二、新增文件

### 1. 邮件服务实现
**文件**: `src/redmine_mcp_server/dws/services/email_service.py`

核心功能：
- `EmailPushService` 类 - 邮件推送服务
- `send_email()` - 发送邮件
- `send_subscription_email()` - 发送订阅报告
- `test_connection()` - 测试 SMTP 连接

### 2. MCP 工具更新
**文件**: `src/redmine_mcp_server/mcp/tools/subscription_tools.py`

新增工具：
- `test_email_service()` - 测试邮件服务配置

更新工具：
- `subscribe_project()` - 新增 `channel` 和 `channel_id` 参数

### 3. 配置文件更新
**文件**: `.env.example`

新增配置项：
```bash
# Email Subscription Configuration
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_SENDER_EMAIL=your-email@gmail.com
EMAIL_SENDER_NAME=Redmine MCP Server
EMAIL_USE_TLS=true
DEFAULT_EMAIL=user@example.com
```

---

## 三、支持的推送渠道

现在订阅系统支持三种推送渠道：

| 渠道 | channel 值 | channel_id 格式 | 配置复杂度 |
|------|-----------|----------------|------------|
| **Email** 📧 | `email` | 邮箱地址 | ⭐ 简单 |
| **DingTalk** 💬 | `dingtalk` | 钉钉用户 ID | ⭐⭐ 中等 |
| **Telegram** ✈️ | `telegram` | Telegram chat ID | ⭐⭐ 中等 |

---

## 四、使用示例

### 示例 1: 订阅到邮箱

```python
# 订阅项目到邮箱，每日早上 9 点接收简要报告
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="user@example.com",
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

### 示例 2: 订阅到钉钉

```python
# 订阅项目到钉钉，每日早上 9 点接收简要报告
subscribe_project(
    project_id=341,
    channel="dingtalk",
    channel_id="dingtalk-user-id",
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

### 示例 3: 订阅到 Telegram

```python
# 订阅项目到 Telegram，每周一早上 10 点接收详细报告
subscribe_project(
    project_id=341,
    channel="telegram",
    channel_id="123456789",
    frequency="weekly",
    level="detailed",
    push_time="Mon 10:00"
)
```

### 示例 4: 测试邮件服务

```python
# 测试 SMTP 连接
test_email_service()

# 发送测试邮件
test_email_service(to_email="user@example.com")
```

### 示例 5: 混合渠道订阅

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

## 五、邮件报告模板

### 简要报告 (Brief)

包含关键指标：
- Issue 总数
- 今日新增
- 今日关闭
- 未关闭数量

### 详细报告 (Detailed)

包含完整分析：
- 概览指标
- 状态分布
- 优先级分布
- 高优先级 Issue TOP 5
- 人员任务量 TOP 5

---

## 六、数据库表结构

订阅信息存储在 `warehouse.ads_user_subscriptions` 表中：

```sql
CREATE TABLE warehouse.ads_user_subscriptions (
    subscription_id   VARCHAR(255) PRIMARY KEY,
    user_id           VARCHAR(100) NOT NULL,
    project_id        INTEGER NOT NULL,
    channel           VARCHAR(50) NOT NULL,       -- email/dingtalk/telegram
    channel_id        VARCHAR(255) NOT NULL,      -- 邮箱/钉钉 ID/Telegram ID
    frequency         VARCHAR(20) NOT NULL,
    level             VARCHAR(20) NOT NULL,
    push_time         VARCHAR(50),
    enabled           BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL
);
```

---

## 七、配置步骤

### 步骤 1: 配置 SMTP 服务器

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，添加邮件配置
nano .env
```

### 步骤 2: 获取 SMTP 凭证

#### Gmail 用户
1. 启用两步验证
2. 创建应用专用密码
3. 使用应用专用密码作为 `EMAIL_SMTP_PASSWORD`

#### 企业邮箱用户
联系 IT 部门获取：
- SMTP 服务器地址
- SMTP 端口
- 认证凭据

### 步骤 3: 测试邮件服务

```python
# 测试 SMTP 连接
test_email_service()

# 测试发送邮件
test_email_service(to_email="your-email@example.com")
```

### 步骤 4: 订阅项目

```python
subscribe_project(
    project_id=341,
    channel="email",
    channel_id="your-email@example.com",
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

---

## 八、技术架构

### 数据流

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│  Subscription   │────▶│  EmailPush      │
│  (VSCode, etc.) │◀────│     Manager     │◀────│     Service     │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   PostgreSQL    │     │    SMTP Server  │
                        │ ads_user_       │     │  (Gmail/ etc.)  │
                        │ subscriptions   │     │                 │
                        └─────────────────┘     └─────────────────┘
```

### 组件说明

| 组件 | 文件 | 说明 |
|------|------|------|
| SubscriptionManager | `dws/services/subscription_service.py` | 订阅管理 |
| EmailPushService | `dws/services/email_service.py` | 邮件推送 |
| MCP Tools | `mcp/tools/subscription_tools.py` | MCP 工具接口 |

---

## 九、安全建议

### 1. 使用应用专用密码

不要使用主密码，为 Redmine MCP 创建专用密码。

### 2. 启用 TLS/SSL

```bash
EMAIL_USE_TLS=true  # 推荐
# 或使用 SSL
EMAIL_SMTP_PORT=465
EMAIL_USE_TLS=false
```

### 3. 限制数据库权限

确保 `redmine_warehouse` 用户只有必要的权限：

```sql
GRANT SELECT, INSERT, UPDATE ON warehouse.ads_user_subscriptions TO redmine_warehouse;
```

---

## 十、故障排查

### 问题 1: SMTP 认证失败

**错误**: `SMTPAuthenticationError: (535, '5.7.8 Username and Password not accepted')`

**解决**:
1. 检查用户名密码
2. Gmail 用户启用两步验证并创建应用密码
3. 检查是否允许"不够安全的应用"

### 问题 2: 连接超时

**错误**: `smtplib.SMTPServerDisconnected`

**解决**:
1. 检查网络连接
2. 确认 SMTP 服务器和端口正确
3. 检查防火墙设置

### 问题 3: 证书验证失败

**错误**: `ssl.SSLCertVerificationError`

**解决**:
1. 使用 SSL 端口 (465) 代替 TLS 端口 (587)
2. 或设置 `EMAIL_USE_TLS=false`

---

## 十一、相关文件

| 文件 | 说明 |
|------|------|
| `src/redmine_mcp_server/dws/services/email_service.py` | 邮件服务实现 |
| `src/redmine_mcp_server/dws/services/subscription_service.py` | 订阅管理 |
| `src/redmine_mcp_server/mcp/tools/subscription_tools.py` | 订阅 MCP 工具 |
| `.env.example` | 配置模板 |
| `docs/feature/05-email-subscription.md` | 使用文档 |
| `init-scripts/07-ads-user-subscriptions.sql` | 数据库建表脚本 |

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
