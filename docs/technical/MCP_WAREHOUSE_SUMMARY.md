# Redmine MCP 数仓 - 完整架构

**核心理念**: 数仓完全整合在 MCP Server 中，使用 PostgreSQL 数据库

**项目位置**: `/docker/redmine-mcp-server/`  
**最后更新**: 2026-02-27

---

## 📦 项目结构

```
/docker/redmine-mcp-server/
├── src/redmine_mcp_server/
│   ├── main.py                    # MCP 入口
│   ├── redmine_handler.py         # MCP Tools (26 个)
│   ├── redmine_warehouse.py       # 数仓访问层 ⭐ (PostgreSQL)
│   ├── redmine_scheduler.py       # 定时同步调度器 ⭐
│   └── dev_test_analyzer.py       # 开发/测试分析器 ⭐
├── docs/                           # 📚 文档
│   ├── README.md                  # 文档索引
│   ├── MCP_WAREHOUSE_SUMMARY.md   # 本文档
│   ├── IMPLEMENTED_FEATURES.md    # 已实现功能
│   └── ...
├── init-scripts/                  # 🗄️ PostgreSQL 初始化脚本
│   └── 01-schema.sql
├── data/                          # 💾 MCP 服务器数据
└── docker-compose.yml             # 🐳 PostgreSQL + MCP Server
```

---

## 🏗️ 架构分层

```
┌─────────────────────────────────────────┐
│         MCP Tools (API 接口)             │
│  - get_project_daily_stats              │
│  - analyze_dev_tester_workload          │
│  - trigger_full_sync                    │
│  - subscribe_project                    │
│  ... (26 个工具)                         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Redmine Handler (API 处理)            │
│  - 调用 Redmine API                      │
│  - 数据转换                             │
│  - 缓存管理                             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   Warehouse Manager (数仓访问)           │
│  - PostgreSQL 连接池 (psycopg2)          │
│  - CRUD 操作                            │
│  - 事务管理                             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   PostgreSQL Database (数据存储)         │
│  Container: redmine-mcp-warehouse-db    │
│  Schema: warehouse                      │
│  - issue_daily_snapshot                 │
│  - project_daily_summary                │
│  - (扩展表中...)                         │
└─────────────────────────────────────────┘
```

---

## 🗄️ 数据库配置

### Docker Compose

```yaml
# docker-compose.yml
services:
  warehouse-db:
    image: postgres:15-alpine
    container_name: redmine-mcp-warehouse-db
    environment:
      POSTGRES_USER: redmine_warehouse
      POSTGRES_PASSWORD: WarehouseP@ss2026
      POSTGRES_DB: redmine_warehouse
    volumes:
      - warehouse_db_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
```

### 连接参数

| 参数 | 值 |
|------|------|
| Host | `warehouse-db` (Docker 网络) |
| Port | `5432` |
| Database | `redmine_warehouse` |
| User | `redmine_warehouse` |
| Password | `WarehouseP@ss2026` |
| Schema | `warehouse` |

### Python 连接代码

```python
# src/redmine_mcp_server/redmine_warehouse.py
import psycopg2
from psycopg2 import pool

class DataWarehouse:
    def __init__(self):
        self.connection_pool = pool.SimpleConnectionPool(
            1, 10,
            host=os.getenv("WAREHOUSE_DB_HOST", "warehouse-db"),
            port=os.getenv("WAREHOUSE_DB_PORT", "5432"),
            dbname=os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse"),
            user=os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse"),
            password=os.getenv("WAREHOUSE_DB_PASSWORD"),
            cursor_factory=RealDictCursor
        )
```

---

## 📊 数据库表

### 现有表

| 表名 | 说明 |
|------|------|
| `warehouse.issue_daily_snapshot` | Issue 每日快照 |
| `warehouse.project_daily_summary` | 项目每日汇总 |

### 扩展表（计划）

| 表名 | 说明 |
|------|------|
| `warehouse.issue_contributors` | Issue 贡献者明细 |
| `warehouse.issue_contributor_summary` | 贡献者汇总 |
| `warehouse.user_project_role` | 用户项目角色 |
| `warehouse.project_role_distribution` | 项目角色分布 |

---

## 🛠️ MCP 工具（26 个）

### 数仓相关工具

| 工具 | 说明 |
|------|------|
| `get_project_daily_stats` | 项目每日统计 |
| `analyze_dev_tester_workload` | 开发/测试工作量分析 |
| `trigger_full_sync` | 触发全量同步 |
| `trigger_progressive_sync` | 触发增量同步 |
| `get_sync_progress` | 同步进度查询 |
| `backfill_historical_data` | 历史数据回填 |

---

## 🔄 数据同步流程

### 增量同步（每 10 分钟）

```
Scheduler → fetch_updated_issues(13min 窗口)
    ↓
upsert_issues_batch()
    ↓
refresh_daily_summary()
    ↓
PostgreSQL: warehouse.issue_daily_snapshot
```

### 全量同步（每天/手动）

```
MCP Tool: trigger_full_sync
    ↓
fetch_all_issues(project_id)
    ↓
compare_with_yesterday()
    ↓
upsert_issues_batch()
    ↓
PostgreSQL
```

---

## 🚀 部署方式

```bash
cd /docker/redmine-mcp-server
docker-compose up -d
```

**启动的服务**:
1. `redmine-mcp-warehouse-db` - PostgreSQL 数据库
2. `redmine-mcp-server` - MCP 服务器

---

## 📈 性能数据

| 指标 | 数值 |
|------|------|
| 增量同步间隔 | 10 分钟 |
| 增量时间窗口 | 13 分钟 |
| 单项目同步速度 | ~1-2 秒 |
| 全量同步速度 | ~30-60 秒/13 项目 |
| Token 消耗降低 | 97% |

---

## 📚 文档导航

### 快速入门

1. [`README.md`](./README.md) - 文档索引
2. [`IMPLEMENTED_FEATURES.md`](./IMPLEMENTED_FEATURES.md) - 已实现功能
3. [`WAREHOUSE_SYNC.md`](./WAREHOUSE_SYNC.md) - 同步配置

### 开发扩展

1. [`WAREHOUSE_CONTRIBUTOR_EXTENSION.md`](./WAREHOUSE_CONTRIBUTOR_EXTENSION.md) - 贡献者扩展
2. [`redmine-warehouse-schema.md`](./redmine-warehouse-schema.md) - 表结构设计
3. [`feature/03-dev-test-analyzer.md`](./feature/03-dev-test-analyzer.md) - 分析器实现

### 运维管理

1. [`tool-reference.md`](./tool-reference.md) - 工具参考
2. [`troubleshooting.md`](./troubleshooting.md) - 故障排查
3. [`SUBSCRIPTION_GUIDE.md`](./SUBSCRIPTION_GUIDE.md) - 订阅指南

---

## ✅ 核心优势

1. **完全整合** - 数仓是 MCP Server 的内在部分
2. **PostgreSQL** - 生产级数据库，支持复杂查询
3. **统一管理** - 所有代码和配置在一个项目
4. **Docker 编排** - 自动管理数据库连接
5. **低维护成本** - 无额外配置

---

**维护者**: OpenJaw <openjaw@gmail.com>  
**项目**: `/docker/redmine-mcp-server/`
