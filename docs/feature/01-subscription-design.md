# 项目订阅功能 - 概要设计文档

**版本**: v1.0  
**发布日期**: 2026-02-26  
**状态**: ✅ 已实现

---

## 📐 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │  MCP Tools  │───▶│ Subscription │───▶│   Message   │   │
│  │  (5 tools)  │    │   Manager    │    │   Channel   │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
│                            │                                │
│                            ▼                                │
│                   ┌──────────────┐                         │
│                   │ Subscription │                         │
│                   │   Reporter   │                         │
│                   └──────────────┘                         │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Redmine   │ │  Warehouse  │ │  DingTalk/  │
    │     API     │ │  (Postgres) │ │  Telegram   │
    └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 🏗️ 组件设计

### 1. SubscriptionManager (订阅管理器)

**文件**: `src/redmine_mcp_server/subscriptions.py`

**职责**:
- 订阅配置的 CRUD 操作
- 订阅数据持久化（JSON 文件）
- 订阅查询与统计

**核心方法**:
```python
class SubscriptionManager:
    def subscribe(...) -> Dict           # 创建订阅
    def unsubscribe(...) -> Dict         # 取消订阅
    def get_user_subscriptions(...) -> List  # 查询用户订阅
    def get_project_subscribers(...) -> List  # 查询项目订阅者
    def get_due_subscriptions(...) -> List    # 获取待推送订阅
    def update_subscription(...) -> Dict      # 更新订阅
    def get_stats(...) -> Dict                # 获取统计
```

**数据结构**:
```json
{
  "subscription_id": "user_id:project_id:channel",
  "user_id": "string",
  "project_id": 341,
  "channel": "dingtalk",
  "channel_id": "string",
  "frequency": "daily",
  "level": "brief",
  "push_time": "09:00",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "enabled": true
}
```

---

### 2. SubscriptionReporter (报告生成器)

**文件**: `src/redmine_mcp_server/subscription_reporter.py`

**职责**:
- 生成简要报告
- 生成详细报告
- 报告格式化（适配不同渠道）
- 智能分析（逾期识别、负载预警）

**核心方法**:
```python
class SubscriptionReporter:
    def generate_brief_report(...) -> Dict      # 简要报告
    def generate_detailed_report(...) -> Dict   # 详细报告
    def format_report_for_message(...) -> str   # 格式化消息
    def _generate_insights(...) -> Dict         # 生成洞察
```

**报告生成流程**:
```
1. 检查数仓缓存
   ├─ 有缓存 → 从 PostgreSQL 读取
   └─ 无缓存 → 调用 Redmine API
   
2. 生成统计数据
   ├─ 优先级分布
   ├─ 状态分布
   └─ 人员负载
   
3. 识别风险
   ├─ 逾期 Issue (>30 天)
   └─ 负载预警 (>30 任务)
   
4. 生成建议
   └─ 基于数据分析
```

---

### 3. MCP Tools (工具接口)

**文件**: `src/redmine_mcp_server/redmine_handler.py`

**工具列表**:

| 工具 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `subscribe_project` | project_id, frequency, level, push_time | subscription | 订阅项目 |
| `unsubscribe_project` | project_id (optional) | removed_count | 取消订阅 |
| `list_my_subscriptions` | - | List[subscription] | 查看订阅 |
| `get_subscription_stats` | - | stats | 订阅统计 |
| `generate_subscription_report` | project_id, level | report | 生成报告 |

**工具调用流程**:
```
用户请求 (钉钉/Telegram)
    ↓
OpenClaw Gateway
    ↓
MCP Protocol
    ↓
redmine_handler.py (工具实现)
    ↓
SubscriptionManager / SubscriptionReporter
    ↓
返回结果 → 格式化 → 推送给用户
```

---

## 🔄 数据流

### 订阅创建流程

```
用户调用 subscribe_project
    ↓
验证参数 (project_id, frequency, level)
    ↓
生成 subscription_id (user_id:project_id:channel)
    ↓
创建订阅对象
    ↓
保存到 subscriptions.json
    ↓
返回订阅结果
```

### 自动推送流程

```
Scheduler 定时触发 (每分钟检查)
    ↓
获取当前时间匹配的订阅 (get_due_subscriptions)
    ↓
遍历每个订阅:
    ├─ 调用 generate_subscription_report
    ├─ 格式化报告 (format_report_for_message)
    └─ 通过渠道推送 (dingtalk/telegram)
    ↓
记录推送日志
```

---

## 📦 存储设计

### subscriptions.json

**路径**: `./data/subscriptions.json`

**结构**:
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
  },
  "user123:372:telegram": { ... }
}
```

**索引**:
- 主键：`subscription_id` (复合键：user_id + project_id + channel)
- 查询优化：按 `user_id`、`project_id`、`frequency` 过滤

---

## 🔌 集成点

### 1. Redmine API

**用途**: 获取 Issue 数据（当数仓无缓存时）

**接口**:
- `redmine.issue.filter()` - 查询 Issue
- `redmine.project.get()` - 获取项目信息

**优化**: 优先使用数仓缓存，减少 API 调用

---

### 2. PostgreSQL 数仓

**用途**: 快速获取项目统计数据

**表**:
- `warehouse.issue_daily_snapshot` - Issue 快照
- `warehouse.project_daily_summary` - 项目汇总

**查询**:
```sql
SELECT * FROM warehouse.project_daily_summary
WHERE project_id = 341 AND snapshot_date = '2026-02-26'
```

---

### 3. 消息渠道

**支持渠道**:
- 钉钉 (DingTalk)
- Telegram

**推送方式**:
- 钉钉：Stream 模式 WebSocket
- Telegram：Bot API

**消息格式**: Markdown 文本

---

## ⚡ 性能优化

### 1. 缓存策略

- **数仓缓存**: 优先从 PostgreSQL 读取统计数据
- **订阅缓存**: 内存缓存订阅配置，减少文件 IO
- **报告缓存**: 相同参数报告可缓存 5 分钟

### 2. Token 优化

| 报告类型 | Token 消耗 | 优化措施 |
|----------|-----------|----------|
| 简要报告 | ~500 | 仅返回关键指标 |
| 详细报告 | ~2000 | 限制 Issue 数量 (TOP 20) |

### 3. 推送优化

- **批量推送**: 同一用户多项目合并推送
- **时间窗口**: 推送时间允许 ±5 分钟浮动
- **失败重试**: 推送失败自动重试 3 次

---

## 🔒 安全设计

### 1. 权限控制

- **订阅隔离**: 用户只能查看/管理自己的订阅
- **项目权限**: 基于 Redmine 项目权限（TODO: 实现）
- **渠道验证**: 验证推送渠道 ID 归属（TODO: 实现）

### 2. 数据保护

- **文件权限**: subscriptions.json 仅 appuser 可写
- **敏感信息**: 不存储用户凭证
- **日志脱敏**: 日志中隐藏敏感数据

---

## 🧪 测试策略

### 单元测试

```python
# 测试订阅管理
def test_subscribe():
    manager = SubscriptionManager()
    result = manager.subscribe("user1", 341, "dingtalk", "default")
    assert result["success"] == True

# 测试报告生成
def test_generate_brief_report():
    reporter = SubscriptionReporter()
    report = reporter.generate_brief_report(341)
    assert "summary" in report
```

### 集成测试

```bash
# 测试脚本
./scripts/test-subscription.sh
```

**测试覆盖**:
- ✅ 订阅/取消订阅
- ✅ 简要/详细报告生成
- ✅ 订阅统计
- ✅ 数据持久化

---

## 📈 监控指标

### 业务指标

| 指标 | 目标值 | 告警阈值 |
|------|--------|----------|
| 订阅总数 | - | - |
| 活跃订阅率 | >90% | <80% |
| 推送成功率 | 100% | <99% |
| 报告生成时间 | <5s | >10s |

### 技术指标

| 指标 | 采集方式 |
|------|----------|
| subscriptions.json 文件大小 | 文件系统 |
| 订阅查询响应时间 | 日志分析 |
| 推送失败次数 | 错误日志 |

---

## 🚀 扩展计划

### v1.1 (短期)

- [ ] 用户身份自动识别（从会话获取 user_id）
- [ ] 订阅配置模板（快速订阅常用配置）
- [ ] 推送历史记录

### v1.2 (中期)

- [ ] 邮件推送渠道
- [ ] 自定义报告模板
- [ ] 订阅分组管理

### v2.0 (长期)

- [ ] 实时推送（Issue 变更立即通知）
- [ ] 智能推荐（根据用户行为推荐订阅项目）
- [ ] 多语言支持

---

## 📞 故障排查

### 问题 1: 订阅保存失败

**现象**: `Failed to save subscriptions: Permission denied`

**原因**: data 目录权限不足

**解决**:
```bash
sudo chmod 777 /docker/redmine-mcp-server/data
docker restart redmine-mcp-server
```

### 问题 2: 报告生成超时

**现象**: `Timeout generating report`

**原因**: 数仓无缓存，API 调用慢

**解决**:
1. 检查数仓同步状态
2. 手动触发同步：`python /app/scripts/manual-sync.py`
3. 增加超时时间

### 问题 3: 推送失败

**现象**: `Failed to push message`

**原因**: 渠道配置错误或网络问题

**解决**:
1. 检查渠道配置
2. 验证网络连接
3. 查看渠道日志

---

## 📚 相关文档

- [功能描述](./01-subscription-feature.md)
- [使用指南](../SUBSCRIPTION_GUIDE.md)
- [API 参考](../tool-reference.md)

---

**最后更新**: 2026-02-26  
**维护者**: OpenJaw <openjaw@gmail.com>  
**代码位置**: `src/redmine_mcp_server/subscriptions.py`, `subscription_reporter.py`
