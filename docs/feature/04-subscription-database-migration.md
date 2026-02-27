# 订阅数据库持久化 - 迁移指南

**版本**: 1.0  
**日期**: 2026-02-27  
**说明**: 将订阅数据从 JSON 文件迁移到 PostgreSQL 数据库

---

## 一、变更概述

### 变更前
- 订阅信息存储在 `data/subscriptions.json` 文件中
- 文件读写方式，不支持并发访问
- 无事务保证，数据一致性依赖文件系统

### 变更后
- 订阅信息存储在 PostgreSQL `warehouse.ads_user_subscriptions` 表中
- 数据库事务保证数据一致性
- 支持并发访问和复杂查询
- 符合数仓 ADS 层命名规范

---

## 二、数据库表结构

### 表名：`warehouse.ads_user_subscriptions`

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `subscription_id` | VARCHAR(255) | 主键，格式：`user_id:project_id:channel` |
| `user_id` | VARCHAR(100) | 用户 ID |
| `project_id` | INTEGER | 项目 ID |
| `channel` | VARCHAR(50) | 推送渠道 (dingtalk/telegram/email) |
| `channel_id` | VARCHAR(255) | 渠道 ID |
| `frequency` | VARCHAR(20) | 推送频率 (realtime/daily/weekly/monthly) |
| `level` | VARCHAR(20) | 报告级别 (brief/detailed) |
| `push_time` | VARCHAR(50) | 推送时间 |
| `enabled` | BOOLEAN | 是否启用 |
| `created_at` | TIMESTAMP | 创建时间 |
| `updated_at` | TIMESTAMP | 更新时间 |
| `sync_time` | TIMESTAMP | 数据仓库同步时间 |

### 索引

- `idx_ads_user_subscriptions_user` - 按用户查询
- `idx_ads_user_subscriptions_project` - 按项目查询
- `idx_ads_user_subscriptions_project_enabled` - 查询启用的订阅项目

---

## 三、迁移步骤

### 步骤 1: 创建数据库表

执行 SQL 脚本创建订阅表：

```bash
# 连接到 PostgreSQL 数据库
psql -h <warehouse-db-host> -U redmine_warehouse -d redmine_warehouse

# 执行建表脚本
psql -h <warehouse-db-host> -U redmine_warehouse -d redmine_warehouse \
  -f /docker/redmine-mcp-server/init-scripts/07-ads-user-subscriptions.sql
```

或者在 psql 交互界面：

```sql
\i /docker/redmine-mcp-server/init-scripts/07-ads-user-subscriptions.sql
```

### 步骤 2: 运行迁移脚本

```bash
# 确保环境变量配置正确
export WAREHOUSE_DB_HOST=<your-db-host>
export WAREHOUSE_DB_PORT=5432
export WAREHOUSE_DB_NAME=redmine_warehouse
export WAREHOUSE_DB_USER=redmine_warehouse
export WAREHOUSE_DB_PASSWORD=<your-password>

# 运行迁移脚本
cd /docker/redmine-mcp-server
python scripts/migrate_subscriptions_to_db.py
```

### 步骤 3: 验证迁移结果

```sql
-- 连接到数据库
psql -h <warehouse-db-host> -U redmine_warehouse -d redmine_warehouse

-- 查看订阅总数
SELECT COUNT(*) FROM warehouse.ads_user_subscriptions;

-- 查看订阅详情
SELECT 
    subscription_id,
    user_id,
    project_id,
    channel,
    frequency,
    enabled,
    created_at
FROM warehouse.ads_user_subscriptions
ORDER BY created_at DESC;

-- 验证与 JSON 文件数据一致
-- (迁移脚本会自动验证并输出结果)
```

### 步骤 4: 重启 MCP 服务

```bash
# 停止服务
docker-compose down

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 四、MCP 工具使用

迁移完成后，订阅相关的 MCP 工具将自动使用数据库存储：

### 订阅项目

```python
# MCP 工具调用
subscribe_project(
    project_id=341,
    frequency="daily",
    level="brief",
    push_time="09:00"
)
```

### 查看我的订阅

```python
list_my_subscriptions()
# 返回：
# [
#   {
#     "subscription_id": "default_user:341:dingtalk",
#     "user_id": "default_user",
#     "project_id": 341,
#     "channel": "dingtalk",
#     "frequency": "daily",
#     "level": "brief",
#     "push_time": "09:00",
#     "enabled": true,
#     ...
#   }
# ]
```

### 获取订阅统计

```python
get_subscription_stats()
# 返回：
# {
#   "total_subscriptions": 13,
#   "by_frequency": {"daily": 13},
#   "by_channel": {"dingtalk": 13},
#   "by_project": {"341": 1, "356": 1, ...},
#   "active_subscriptions": 13
# }
```

### 取消订阅

```python
unsubscribe_project(project_id=341)
```

---

## 五、回滚方案

如需回滚到 JSON 文件存储：

### 方法 1: 修改代码

修改 `src/redmine_mcp_server/dws/services/subscription_service.py`：

```python
class SubscriptionManager:
    def __init__(self):
        # 注释掉数据库初始化
        # self._init_warehouse()
        # self.warehouse = None
        
        # 恢复 JSON 文件存储
        self.subscriptions_file = Path(SUBSCRIPTIONS_FILE)
        self.subscriptions: Dict[str, Any] = {}
        self._load_subscriptions()  # 从 JSON 加载
```

### 方法 2: 禁用数据库连接

设置环境变量禁用数据库：

```bash
export WAREHOUSE_SYNC_ENABLED=false
```

---

## 六、故障排查

### 问题 1: 数据库表不存在

**错误信息**:
```
relation "warehouse.ads_user_subscriptions" does not exist
```

**解决方案**:
```bash
# 执行建表脚本
psql -h <db-host> -U redmine_warehouse -d redmine_warehouse \
  -f /docker/redmine-mcp-server/init-scripts/07-ads-user-subscriptions.sql
```

### 问题 2: 数据库连接失败

**错误信息**:
```
Failed to initialize warehouse connection: could not connect to server
```

**解决方案**:
1. 检查数据库是否运行：`docker-compose ps`
2. 检查网络连接：`ping <db-host>`
3. 检查环境变量配置是否正确

### 问题 3: 迁移后数据不一致

**解决方案**:
```bash
# 重新运行迁移脚本
python scripts/migrate_subscriptions_to_db.py

# 查看迁移日志
cat logs/migration.log
```

---

## 七、常见问题

### Q1: 迁移是否会影响现有订阅？

**A**: 不会。迁移脚本使用 `ON CONFLICT DO UPDATE`，如果订阅已存在会更新，不会重复插入。

### Q2: JSON 文件还会使用吗？

**A**: 不会。迁移完成后，订阅数据只存储在数据库中。JSON 文件作为备份保留。

### Q3: 数据库和 JSON 文件会同时使用吗？

**A**: 不会。代码逻辑优先使用数据库，如果数据库不可用会降级到 JSON 文件（降级模式可选）。

### Q4: 迁移需要停机吗？

**A**: 不需要。可以在服务运行时执行迁移，迁移完成后重启服务即可。

---

## 八、相关文件

| 文件 | 说明 |
|------|------|
| `init-scripts/07-ads-user-subscriptions.sql` | 数据库建表脚本 |
| `scripts/migrate_subscriptions_to_db.py` | 数据迁移脚本 |
| `src/redmine_mcp_server/dws/services/subscription_service.py` | 订阅服务实现 |
| `src/redmine_mcp_server/mcp/tools/subscription_tools.py` | 订阅 MCP 工具 |
| `src/redmine_mcp_server/mcp/tools/warehouse_tools.py` | 仓库管理工具 |

---

## 九、架构说明

### 数据流向

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│  Subscription   │────▶│   PostgreSQL    │
│  (VSCode, etc.) │◀────│     Manager     │◀────│  ads_user_      │
└─────────────────┘     └─────────────────┘     │  subscriptions  │
                                                └─────────────────┘
```

### 数仓分层

```
ODS 层 → DWD 层 → DWS 层 → ADS 层
                    ↓
              ads_user_subscriptions (订阅表)
```

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
