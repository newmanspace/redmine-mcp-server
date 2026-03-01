# ISSUE-004 - 订阅表字段名不匹配

**创建日期**: 2026-02-28  
**严重性**: 🔴 高  
**状态**: ⏳ 待修复  
**影响范围**: 订阅创建、订阅查询

---

## 问题描述

代码中使用的字段名与数据库表结构不一致，导致订阅无法保存。

**错误信息**:
```
Error executing tool subscribe_project: 'frequency'
```

**日志**:
```
2026-02-28 15:51:15 ERROR    Failed to save subscription to database: 'frequency'
```

---

## 根因分析

**问题文件**: `src/redmine_mcp_server/dws/services/subscription_service.py`

**代码使用的字段名**（旧版本）:
| 字段 | 代码中使用 |
|------|-----------|
| 报告类型 | `frequency` |
| 报告级别 | `level` |
| 推送时间 | `push_time` |

**数据库表结构**（新版本）:
| 字段 | 表结构中 |
|------|---------|
| 报告类型 | `report_type` |
| 报告级别 | `report_level` |
| 推送时间 | `send_time` |

**原因**:
- 数据库表结构更新后，代码未同步更新
- 缺少数据库迁移脚本或迁移不完整
- 代码审查时未发现字段名变更

---

## 解决方案

### 方案一：更新代码（推荐）

**修改文件**: `src/redmine_mcp_server/dws/services/subscription_service.py`

**需要修改的位置**:

1. **INSERT 语句** (约第 80 行)
```python
# 修改前
INSERT INTO warehouse.ads_user_subscriptions (
    subscription_id, user_id, project_id, channel,
    channel_id, frequency, level, push_time,
    enabled, created_at, updated_at
)

# 修改后
INSERT INTO warehouse.ads_user_subscriptions (
    subscription_id, user_id, project_id, channel,
    channel_id, report_type, report_level, send_time,
    enabled, created_at, updated_at
)
```

2. **SELECT 语句** (约第 95 行)
```python
# 修改前
"frequency": row["frequency"],
"level": row["level"],
"push_time": row["push_time"],

# 修改后
"report_type": row["report_type"],
"report_level": row["report_level"],
"send_time": row["send_time"],
```

3. **UPDATE 语句** (约第 130-148 行)
```python
# 修改前
frequency = EXCLUDED.frequency,
level = EXCLUDED.level,
push_time = EXCLUDED.push_time,

# 修改后
report_type = EXCLUDED.report_type,
report_level = EXCLUDED.report_level,
send_time = EXCLUDED.send_time,
```

4. **参数传递** (约第 148 行)
```python
# 修改前
subscription["frequency"],
subscription["level"],
subscription["push_time"],

# 修改后
subscription["report_type"],
subscription["report_level"],
subscription["send_time"],
```

### 方案二：回滚数据库表结构

如果代码是最新的，可以回滚数据库表结构到旧版本（不推荐）。

---

## 修复命令

```bash
cd /docker/redmine-mcp-server

# 使用 sed 批量替换
sed -i 's/"frequency"/"report_type"/g' src/redmine_mcp_server/dws/services/subscription_service.py
sed -i 's/"level"/"report_level"/g' src/redmine_mcp_server/dws/services/subscription_service.py
sed -i 's/"push_time"/"send_time"/g' src/redmine_mcp_server/dws/services/subscription_service.py

# 修改 SQL 语句中的字段名
sed -i 's/\bfrequency\b/report_type/g' src/redmine_mcp_server/dws/services/subscription_service.py
sed -i 's/\blevel\b/report_level/g' src/redmine_mcp_server/dws/services/subscription_service.py
sed -i 's/\bpush_time\b/send_time/g' src/redmine_mcp_server/dws/services/subscription_service.py

# 重新构建并重启
docker compose build redmine-mcp-server
docker compose restart redmine-mcp-server
```

---

## 验证步骤

```bash
# 1. 创建订阅
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"subscribe_project","arguments":{"project_id":341,"channel":"email","user_email":"andy.liang@fa-software.com","report_type":"daily","send_time":"08:30"}}}'

# 2. 查询数据库
docker exec redmine-mcp-server python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='warehouse-db',
    database='redmine_warehouse',
    user='redmine_warehouse',
    password='WarehouseP@ss2026'
)
cur = conn.cursor()
cur.execute('SELECT * FROM warehouse.ads_user_subscriptions LIMIT 5')
for row in cur.fetchall():
    print(row)
conn.close()
"

# 3. 推送报告
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"push_subscription_reports","arguments":{"report_type":"daily","project_id":341}}}'
```

---

## 如何避免

### 1. 数据库迁移管理

使用迁移工具管理表结构变更：
```bash
# 使用 Alembic (SQLAlchemy)
alembic revision -m "update subscription table fields"
alembic upgrade head

# 或使用 Flyway
flyway migrate
```

### 2. ORM 模型同步

```python
# 使用 SQLAlchemy 模型
class UserSubscription(Base):
    __tablename__ = 'ads_user_subscriptions'
    
    subscription_id = Column(String(255), primary_key=True)
    report_type = Column(String(20), nullable=False)  # 使用一致的字段名
    report_level = Column(String(20), nullable=False)
    send_time = Column(String(50))
```

### 3. 字段名规范文档

在 `docs/database-schema.md` 中记录：
```markdown
## ads_user_subscriptions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| report_type | VARCHAR(20) | 报告类型 (daily/weekly/monthly) |
| report_level | VARCHAR(20) | 报告级别 (brief/detailed/comprehensive) |
| send_time | VARCHAR(50) | 发送时间 (HH:MM) |
```

### 4. 代码审查清单

在 PR/MR 中添加检查项：
- [ ] 数据库字段名与表结构一致
- [ ] 有数据库迁移脚本（如有表结构变更）
- [ ] 更新了相关文档

### 5. 集成测试

```python
# tests/test_subscription.py
def test_subscription_crud():
    """测试订阅的 CRUD 操作"""
    # 创建
    result = subscribe_project(project_id=341, user_email="test@example.com")
    assert result["success"]
    
    # 查询
    subs = list_my_subscriptions()
    assert len(subs) > 0
    
    # 推送
    result = push_subscription_reports(project_id=341)
    assert result["success"] > 0
```

---

## 相关文件

- 问题文件：`src/redmine_mcp_server/dws/services/subscription_service.py`
- 表结构：`init-scripts/07-ads-user-subscriptions.sql`

---

**报告人**: Jaw  
**报告日期**: 2026-02-28  
**待修复**: 需要 qwen-code 修复代码
