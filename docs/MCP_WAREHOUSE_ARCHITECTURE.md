# Redmine MCP 数据仓库架构设计

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Redmine MCP Server                            │
│  /docker/redmine-mcp-server/                                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    MCP Tools Layer                          │ │
│  │  - list_redmine_projects                                   │ │
│  │  - get_redmine_issue                                       │ │
│  │  - search_redmine_issues                                   │ │
│  │  - trigger_full_sync         ← 触发数仓同步                 │ │
│  │  - get_warehouse_stats       ← 查询数仓统计                 │ │
│  │  - analyze_issue_contributors ← 贡献者分析                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               Redmine Handler (redmine_handler.py)          │ │
│  │  - API 调用封装                                              │ │
│  │  - 数据转换                                                 │ │
│  │  - 缓存管理                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │          Warehouse Manager (redmine_warehouse.py)           │ │
│  │  - PostgreSQL 连接池                                         │ │
│  │  - 数据读写操作                                              │ │
│  │  - 快照管理                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL Warehouse Database                       │
│  /docker/redmine-warehouse/                                      │
│                                                                  │
│  Schema: warehouse                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ODS 层 (原始数据)                                        │  │
│  │  - issue_daily_snapshot        (Issue 每日快照)           │  │
│  │  - project_daily_summary       (项目每日汇总)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DWD 层 (明细数据)                                        │  │
│  │  - issue_contributors          (Issue 贡献者)             │  │
│  │  - user_project_role           (用户项目角色)             │  │
│  │  - journal_summary             (Journal 汇总)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DWS/ADS 层 (汇总/应用)                                   │  │
│  │  - project_stats               (项目统计)                 │  │
│  │  - user_workload               (用户工作量)               │  │
│  │  - quality_report              (质量报表)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心组件

### 2.1 MCP 服务器位置

```
/docker/redmine-mcp-server/
├── src/redmine_mcp_server/
│   ├── main.py                    # MCP 入口
│   ├── redmine_handler.py         # Redmine API 处理
│   ├── redmine_warehouse.py       # 数仓访问层 ✅
│   ├── redmine_scheduler.py       # 定时同步调度器
│   └── subscriptions.py           # 订阅管理
├── scripts/
│   ├── manual-sync.py             # 手动同步脚本
│   ├── analyze_all_history.py     # 历史数据分析
│   └── batch_analyze_history.py   # 批量分析
└── docs/
    ├── WAREHOUSE_SYNC.md          # 数仓同步文档
    └── tool-reference.md          # 工具参考
```

### 2.2 数仓位置

```
/docker/redmine-warehouse/
├── docker-compose.yml             # PostgreSQL 容器编排
├── .env                           # 数据库配置
├── init-scripts/                  # 初始化 SQL 脚本
│   └── 01-warehouse-schema.sql   # 表结构定义
├── data/                          # PostgreSQL 数据文件
└── docs/                          # 数仓文档
    └── redmine-warehouse-schema.md
```

---

## 三、MCP 工具集成

### 3.1 现有工具（已有的 MCP Tools）

| 工具名 | 说明 | 数仓关联 |
|--------|------|----------|
| `list_redmine_projects` | 列出所有项目 | 读取 ODS |
| `get_redmine_issue` | 获取 Issue 详情 | 读取 ODS |
| `search_redmine_issues` | 搜索 Issue | 读取 ODS |
| `trigger_full_sync` | 触发全量同步 | 写入 ODS |
| `list_my_redmine_issues` | 我的 Issue | 读取 ODS |
| `update_redmine_issue` | 更新 Issue | 写入 Redmine API |
| `create_redmine_issue` | 创建 Issue | 写入 Redmine API |
| `get_redmine_attachment_download_url` | 附件下载 | 文件管理 |
| `cleanup_attachment_files` | 清理附件 | 文件管理 |

### 3.2 新增工具（围绕数仓）

| 工具名 | 说明 | 数仓层 |
|--------|------|--------|
| `get_warehouse_stats` | 获取数仓统计 | DWS/ADS |
| `analyze_issue_contributors` | Issue 贡献者分析 | DWD |
| `get_project_role_distribution` | 项目角色分布 | DWS |
| `get_user_workload` | 用户工作量查询 | DWS |
| `get_issue_quality_report` | Issue 质量报表 | ADS |
| `get_team_load_analysis` | 团队负载分析 | ADS |

---

## 四、数据库表设计（PostgreSQL）

### 4.1 ODS 层 - 原始数据

```sql
-- Issue 每日快照（已存在）
CREATE TABLE warehouse.issue_daily_snapshot (
    issue_id        INTEGER NOT NULL,
    project_id      INTEGER NOT NULL,
    snapshot_date   DATE NOT NULL,
    subject         VARCHAR(500),
    status_id       INTEGER,
    status_name     VARCHAR(100),
    priority_id     INTEGER,
    priority_name   VARCHAR(100),
    assigned_to_id  INTEGER,
    assigned_to_name VARCHAR(200),
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP,
    is_new          BOOLEAN DEFAULT FALSE,
    is_closed       BOOLEAN DEFAULT FALSE,
    is_updated      BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (issue_id, snapshot_date)
);

-- 项目每日汇总（已存在）
CREATE TABLE warehouse.project_daily_summary (
    project_id      INTEGER NOT NULL,
    snapshot_date   DATE NOT NULL,
    total_issues    INTEGER,
    new_issues      INTEGER,
    closed_issues   INTEGER,
    updated_issues  INTEGER,
    status_new      INTEGER,
    status_in_progress INTEGER,
    status_resolved INTEGER,
    status_closed   INTEGER,
    status_feedback INTEGER,
    priority_immediate INTEGER,
    priority_urgent INTEGER,
    priority_high   INTEGER,
    priority_normal INTEGER,
    priority_low    INTEGER,
    PRIMARY KEY (project_id, snapshot_date)
);
```

### 4.2 DWD 层 - 明细数据（新增）

```sql
-- Issue 贡献者分析
CREATE TABLE warehouse.issue_contributors (
    issue_id            INTEGER NOT NULL,
    project_id          INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    user_name           VARCHAR(200),
    highest_role_id     INTEGER,
    highest_role_name   VARCHAR(100),
    role_category       VARCHAR(20),  -- manager/implementation/developer/tester
    journal_count       INTEGER,
    first_contribution  TIMESTAMP,
    last_contribution  TIMESTAMP,
    status_change_count INTEGER,
    note_count          INTEGER,
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (issue_id, user_id)
);

-- 用户项目角色
CREATE TABLE warehouse.user_project_role (
    project_id          INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    highest_role_id     INTEGER,
    highest_role_name   VARCHAR(100),
    role_category       VARCHAR(20),
    role_priority       INTEGER,
    all_role_ids        VARCHAR(200),
    is_direct_member    BOOLEAN DEFAULT TRUE,
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

-- Journal 汇总
CREATE TABLE warehouse.journal_summary (
    issue_id              INTEGER NOT NULL,
    user_id               INTEGER NOT NULL,
    journal_count         INTEGER,
    first_journal         TIMESTAMP,
    last_journal          TIMESTAMP,
    status_change_count   INTEGER,
    assigned_change_count INTEGER,
    note_count            INTEGER,
    etl_time              TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (issue_id, user_id)
);
```

### 4.3 DWS/ADS 层 - 汇总统计（新增）

```sql
-- 项目角色分布
CREATE TABLE warehouse.project_role_distribution (
    project_id           INTEGER NOT NULL,
    snapshot_date        DATE NOT NULL,
    manager_count        INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count      INTEGER DEFAULT 0,
    tester_count         INTEGER DEFAULT 0,
    other_count          INTEGER DEFAULT 0,
    total_members        INTEGER,
    etl_time             TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, snapshot_date)
);

-- Issue 贡献者汇总
CREATE TABLE warehouse.issue_contributor_summary (
    issue_id             INTEGER PRIMARY KEY,
    project_id           INTEGER,
    manager_count        INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count      INTEGER DEFAULT 0,
    tester_count         INTEGER DEFAULT 0,
    other_count          INTEGER DEFAULT 0,
    total_contributors   INTEGER,
    total_journals       INTEGER,
    etl_time             TIMESTAMP DEFAULT NOW()
);

-- 用户工作量统计
CREATE TABLE warehouse.user_workload (
    user_id           INTEGER NOT NULL,
    year_month        VARCHAR(7),  -- YYYY-MM
    project_id        INTEGER,
    total_issues      INTEGER,
    created_issues    INTEGER,
    closed_issues     INTEGER,
    total_journals    INTEGER,
    as_manager        INTEGER,
    as_developer      INTEGER,
    as_implementation INTEGER,
    etl_time          TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, year_month, project_id)
);
```

---

## 五、MCP 工具实现示例

### 5.1 贡献者分析工具

```python
# /docker/redmine-mcp-server/src/redmine_mcp_server/redmine_warehouse.py

class DataWarehouse:
    # ... 现有代码 ...
    
    def get_issue_contributors(self, issue_id: int) -> List[Dict]:
        """获取 Issue 的贡献者列表"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        user_id,
                        user_name,
                        role_category,
                        highest_role_name,
                        journal_count,
                        first_contribution,
                        last_contribution
                    FROM warehouse.issue_contributors
                    WHERE issue_id = %s
                    ORDER BY 
                        CASE role_category
                            WHEN 'manager' THEN 1
                            WHEN 'implementation' THEN 2
                            WHEN 'developer' THEN 3
                            WHEN 'tester' THEN 4
                            ELSE 5
                        END
                """, (issue_id,))
                return [dict(row) for row in cur.fetchall()]
    
    def get_project_role_distribution(self, project_id: int, 
                                       snapshot_date: date) -> Dict:
        """获取项目角色分布"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.project_role_distribution
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, snapshot_date.isoformat()))
                return dict(cur.fetchone())
```

### 5.2 MCP Tool 注册

```python
# /docker/redmine-mcp-server/src/redmine_mcp_server/main.py

from .redmine_warehouse import DataWarehouse

warehouse = DataWarehouse()

@mcp.tool()
async def analyze_issue_contributors(issue_id: int) -> dict:
    """分析 Issue 的贡献者（按角色分类）"""
    contributors = warehouse.get_issue_contributors(issue_id)
    
    return {
        "issue_id": issue_id,
        "contributors": contributors,
        "summary": {
            "manager": len([c for c in contributors if c['role_category'] == 'manager']),
            "implementation": len([c for c in contributors if c['role_category'] == 'implementation']),
            "developer": len([c for c in contributors if c['role_category'] == 'developer']),
            "tester": len([c for c in contributors if c['role_category'] == 'tester']),
        }
    }

@mcp.tool()
async def get_project_role_distribution(project_id: int, date: str = None) -> dict:
    """获取项目角色分布"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    return warehouse.get_project_role_distribution(
        project_id, 
        datetime.strptime(date, '%Y-%m-%d').date()
    )
```

---

## 六、数据同步流程

### 6.1 现有同步流程（Issue 快照）

```
Redmine Scheduler (redmine_scheduler.py)
    │
    ├─ 每 10 分钟触发增量同步
    │   └─ fetch_updated_issues(project_id, since=13min ago)
    │
    ├─ 每天触发全量同步
    │   └─ fetch_all_issues(project_id)
    │
    ▼
Redmine Handler (redmine_handler.py)
    │
    ├─ 调用 Redmine API
    ├─ 数据转换
    └─ 变更检测
    │
    ▼
Warehouse Manager (redmine_warehouse.py)
    │
    ├─ upsert_issues_batch()
    └─ refresh_daily_summary()
    │
    ▼
PostgreSQL Warehouse
    └─ warehouse.issue_daily_snapshot
```

### 6.2 新增同步流程（贡献者分析）

```
MCP Tool: analyze_issue_contributors(issue_id)
    │
    ├─ 检查 warehouse.issue_contributors 是否有缓存
    │   └─ 有则直接返回
    │
    ├─ 无缓存则触发分析流程：
    │   │
    │   ▼
    │   Redmine Handler
    │   │
    │   ├─ fetch_issue_with_journals(issue_id)
    │   ├─ extract_contributors_from_journals()
    │   └─ get_user_roles_from_project()
    │   │
    │   ▼
    │   Warehouse Manager
    │   │
    │   ├─ upsert_issue_contributors()
    │   └─ update_issue_contributor_summary()
    │   │
    │   ▼
    │   PostgreSQL Warehouse
    │   └─ warehouse.issue_contributors
    │
    └─ 返回分析结果
```

---

## 七、文件组织

### 7.1 MCP 服务器文件

```
/docker/redmine-mcp-server/
├── src/redmine_mcp_server/
│   ├── main.py                        # MCP 入口 + Tool 注册
│   ├── redmine_handler.py             # Redmine API 处理
│   ├── redmine_warehouse.py           # 数仓访问层 ⭐
│   ├── redmine_scheduler.py           # 定时同步调度器
│   ├── subscriptions.py               # 订阅管理
│   └── contributor_analyzer.py        # 【新增】贡献者分析
├── scripts/
│   ├── manual-sync.py                 # 手动同步
│   ├── analyze_all_history.py         # 历史分析
│   └── sync_contributors.py           # 【新增】贡献者同步
└── docs/
    ├── WAREHOUSE_SYNC.md              # 数仓同步文档
    ├── CONTRIBUTOR_ANALYSIS.md        # 【新增】贡献者分析文档
    └── tool-reference.md              # 工具参考
```

### 7.2 数仓文件

```
/docker/redmine-warehouse/
├── docker-compose.yml
├── .env
├── init-scripts/
│   ├── 01-warehouse-schema.sql       # 现有表
│   └── 02-contributor-tables.sql     # 【新增】贡献者相关表
└── docs/
    └── redmine-warehouse-schema.md
```

---

## 八、使用示例

### 8.1 MCP 工具调用

```python
# 通过 MCP 调用工具
from mcp import Client

async with Client() as client:
    # 分析 Issue 贡献者
    result = await client.call_tool(
        "analyze_issue_contributors",
        {"issue_id": 76361}
    )
    
    # 获取项目角色分布
    result = await client.call_tool(
        "get_project_role_distribution",
        {"project_id": 357, "date": "2026-02-27"}
    )
    
    # 获取用户工作量
    result = await client.call_tool(
        "get_user_workload",
        {"user_id": 1531, "year_month": "2026-02"}
    )
```

### 8.2 SQL 直接查询

```bash
# 查询 Issue 贡献者
docker exec redmine-mcp-warehouse-db psql -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT user_name, role_category, journal_count 
      FROM warehouse.issue_contributors 
      WHERE issue_id = 76361;"

# 查询项目角色分布
docker exec redmine-mcp-warehouse-db psql -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT * FROM warehouse.project_role_distribution 
      WHERE project_id = 357 
      ORDER BY snapshot_date DESC 
      LIMIT 1;"
```

---

## 九、部署步骤

### 9.1 数据库表初始化

```bash
cd /docker/redmine-warehouse

# 1. 创建新表
docker exec redmine-mcp-warehouse-db psql -U redmine_warehouse -d redmine_warehouse \
  -f /init-scripts/02-contributor-tables.sql
```

### 9.2 MCP 服务器更新

```bash
cd /docker/redmine-mcp-server

# 1. 添加新工具到 main.py
# 2. 更新 redmine_warehouse.py
# 3. 重启服务
docker-compose restart redmine-mcp-server
```

### 9.3 验证

```bash
# 检查 MCP 工具
mcp list-tools | grep -E "contributor|role|workload"

# 测试工具调用
mcp call analyze_issue_contributors '{"issue_id": 76361}'
```

---

## 十、优势

### 10.1 围绕 MCP 的设计优势

1. **统一管理**: 所有数据访问通过 MCP 工具
2. **权限控制**: MCP 层实现访问控制
3. **缓存优化**: MCP 层实现查询缓存
4. **易于扩展**: 新增工具只需注册到 MCP
5. **监控日志**: 统一的日志和监控

### 10.2 数据分层优势

1. **ODS 层**: 保持原始数据，支持回溯
2. **DWD 层**: 清洗转换，便于分析
3. **DWS/ADS 层**: 预聚合，快速查询

---

**文档版本**: 1.0  
**最后更新**: 2026-02-27  
**维护者**: OpenJaw <openjaw@gmail.com>
