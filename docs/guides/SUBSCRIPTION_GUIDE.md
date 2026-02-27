# Redmine MCP 项目订阅功能指南

## 📋 功能概述

项目订阅功能允许用户订阅 Redmine 项目的定期报告，自动接收项目状态更新。

**支持特性：**
- ✅ 多种推送频率（实时/每日/每周/每月）
- ✅ 两种报告级别（简要/详细）
- ✅ 多项目订阅
- ✅ 钉钉/Telegram 推送
- ✅ 灵活的推送时间设置

---

## 🛠️ 可用工具

### 1. `subscribe_project` - 订阅项目

**功能**: 订阅一个项目的定期报告

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_id` | int | ✅ | - | 项目 ID |
| `frequency` | str | ❌ | "daily" | 推送频率：`realtime`, `daily`, `weekly`, `monthly` |
| `level` | str | ❌ | "brief" | 报告级别：`brief` (简要), `detailed` (详细) |
| `push_time` | str | ❌ | - | 推送时间：daily 用 `"09:00"`, weekly 用 `"Mon 09:00"` |

**示例**:
```json
{
  "name": "subscribe_project",
  "arguments": {
    "project_id": 341,
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00"
  }
}
```

**返回**:
```json
{
  "success": true,
  "subscription_id": "user123:341:dingtalk",
  "message": "已订阅项目 341",
  "subscription": {
    "user_id": "user123",
    "project_id": 341,
    "channel": "dingtalk",
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00",
    "enabled": true
  }
}
```

---

### 2. `unsubscribe_project` - 取消订阅

**功能**: 取消项目订阅

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | int | ❌ | 项目 ID (不传则取消所有订阅) |

**示例**:
```json
{
  "name": "unsubscribe_project",
  "arguments": {
    "project_id": 341
  }
}
```

---

### 3. `list_my_subscriptions` - 查看我的订阅

**功能**: 查看当前用户的所有订阅

**参数**: 无

**返回**:
```json
[
  {
    "subscription_id": "user123:341:dingtalk",
    "project_id": 341,
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00",
    "enabled": true
  }
]
```

---

### 4. `get_subscription_stats` - 订阅统计

**功能**: 获取所有订阅的统计信息

**参数**: 无

**返回**:
```json
{
  "total_subscriptions": 10,
  "by_frequency": {
    "daily": 8,
    "weekly": 2
  },
  "by_channel": {
    "dingtalk": 6,
    "telegram": 4
  },
  "by_project": {
    "341": 5,
    "372": 5
  },
  "active_subscriptions": 10
}
```

---

### 5. `generate_subscription_report` - 生成报告

**功能**: 手动生成项目订阅报告

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `project_id` | int | ✅ | - | 项目 ID |
| `level` | str | ❌ | "brief" | 报告级别：`brief`, `detailed` |

**示例**:
```json
{
  "name": "generate_subscription_report",
  "arguments": {
    "project_id": 341,
    "level": "detailed"
  }
}
```

---

## 📊 报告内容

### 简要报告 (brief)

包含：
- Issue 总数
- 今日新建/关闭/更新数量
- 高优先级 Issue 数量（立刻/紧急/高）
- TOP 5 高优先级 Issue 列表

### 详细报告 (detailed)

包含简要报告所有内容，外加：
- 完整的优先级分布
- 完整的状态分布
- 人员任务量 TOP 10
- 高优先级 Issue 详情（最多 20 个）
- 逾期风险 Issue 识别（>30 天未关闭）
- 项目洞察与建议

---

## 🕐 推送频率说明

| 频率 | push_time 格式 | 示例 | 说明 |
|------|---------------|------|------|
| `realtime` | - | - | 即时推送（Issue 变更时） |
| `daily` | `"HH:MM"` | `"09:00"` | 每天 09:00 推送 |
| `weekly` | `"Ddd HH:MM"` | `"Mon 09:00"` | 每周一 09:00 推送 |
| `monthly` | `"DD HH:MM"` | `"01 09:00"` | 每月 1 号 09:00 推送 |

---

## 🔧 配置选项

### 环境变量

在 `.env.docker` 中配置：

```bash
# 订阅功能配置
SUBSCRIPTIONS_FILE=./data/subscriptions.json

# 推送渠道配置
DINGTALK_ENABLED=true
TELEGRAM_ENABLED=true

# 默认推送设置
DEFAULT_SUBSCRIPTION_FREQUENCY=daily
DEFAULT_SUBSCRIPTION_LEVEL=brief
DEFAULT_PUSH_TIME=09:00
```

---

## 📝 使用场景示例

### 场景 1: 每日简要报告

```bash
# 订阅新顺 CIM 项目的每日简要报告，每天 9 点推送
subscribe_project(
  project_id=341,
  frequency="daily",
  level="brief",
  push_time="09:00"
)
```

### 场景 2: 每周详细报告

```bash
# 订阅工研院 MES 项目的每周详细报告，每周一 9 点推送
subscribe_project(
  project_id=372,
  frequency="weekly",
  level="detailed",
  push_time="Mon 09:00"
)
```

### 场景 3: 多项目订阅

```bash
# 同时订阅多个项目
subscribe_project(project_id=341, frequency="daily", push_time="09:00")
subscribe_project(project_id=372, frequency="daily", push_time="09:30")
subscribe_project(project_id=356, frequency="weekly", push_time="Mon 10:00")
```

### 场景 4: 查看和管理订阅

```bash
# 查看我的所有订阅
list_my_subscriptions()

# 查看订阅统计
get_subscription_stats()

# 取消某个项目的订阅
unsubscribe_project(project_id=341)

# 取消所有订阅
unsubscribe_project()
```

---

## 📦 数据存储

订阅配置存储在 `./data/subscriptions.json`：

```json
{
  "user123:341:dingtalk": {
    "user_id": "user123",
    "project_id": 341,
    "channel": "dingtalk",
    "channel_id": "default",
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00",
    "created_at": "2026-02-26T06:05:12.384523",
    "updated_at": "2026-02-26T06:05:12.384523",
    "enabled": true
  }
}
```

---

## 🚀 下一步开发计划

- [ ] 支持用户身份识别（从钉钉/Telegram 会话自动获取用户 ID）
- [ ] 支持实时推送（Issue 变更时立即通知）
- [ ] 支持邮件推送渠道
- [ ] 支持自定义报告模板
- [ ] 支持订阅分组管理
- [ ] 支持推送历史记录

---

## 📞 故障排查

### 问题 1: 订阅保存失败

**错误**: `Failed to save subscriptions: [Errno 13] Permission denied`

**解决**:
```bash
sudo chmod 777 /docker/redmine-mcp-server/data
docker restart redmine-mcp-server
```

### 问题 2: 工具未找到

**错误**: `Tool "subscribe_project" not found`

**解决**:
```bash
# 检查 MCP 服务器日志
docker logs redmine-mcp-server | grep subscription

# 重启服务
docker restart redmine-mcp-server

# 验证工具列表
curl -s http://localhost:8000/health
```

### 问题 3: 报告生成失败

**错误**: `Failed to generate report`

**解决**:
1. 检查 Redmine API 连接
2. 检查数仓同步状态
3. 查看完整错误日志

---

**最后更新**: 2026-02-26  
**版本**: 1.0
