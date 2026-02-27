# Redmine MCP - 新架构说明

**重构日期**: 2026-02-27  
**目标**: 分离 MCP 服务和数据仓库，职责清晰

---

## 一、新目录结构

```
src/redmine_mcp_server/
├── main.py                          # 程序主入口
├── core/                            # 核心模块
│   ├── __init__.py
│   └── file_manager.py              # 文件管理
├── mcp/                             # MCP 服务层 ⭐对外
│   ├── __init__.py
│   ├── server.py                    # MCP 服务器初始化
│   └── tools/                       # MCP 工具
│       ├── __init__.py
│       ├── issue_tools.py           # Issue 管理
│       ├── project_tools.py         # 项目管理
│       ├── wiki_tools.py            # Wiki 管理
│       ├── attachment_tools.py      # 附件管理
│       ├── search_tools.py          # 搜索
│       ├── subscription_tools.py    # 订阅管理
│       ├── warehouse_tools.py       # 数仓同步
│       ├── analytics_tools.py       # 统计分析
│       ├── contributor_tools.py     # 贡献者分析
│       └── ads_tools.py             # ADS 报表
├── warehouse/                       # 数据仓库层 ⭐对内
│   ├── __init__.py
│   ├── database.py                  # 数据库访问
│   ├── repositories/                # 数据访问层（待创建）
│   │   └── __init__.py
│   └── services/                    # 业务逻辑层
│       ├── __init__.py
│       ├── analysis_service.py      # 分析服务
│       ├── report_service.py        # 报表服务
│       ├── sync_service.py          # 同步服务
│       ├── subscription_service.py  # 订阅服务
│       └── quality_service.py       # 质量监控
└── scheduler/                       # 调度器层 ⭐独立
    ├── __init__.py
    ├── tasks.py                     # 定时任务
    ├── daily_stats.py               # 每日统计
    └── ads_scheduler.py             # ADS 报表调度
```

---

## 二、层次关系

```
┌──────────────────────────────────────┐
│  MCP Service Layer (mcp/)            │ ← 对外服务
│  - server.py (MCP 初始化)             │
│  - tools/ (30+ 个 MCP 工具)            │
└──────────────┬───────────────────────┘
               │ 调用 Service
┌──────────────▼───────────────────────┐
│  Warehouse Service Layer (warehouse/)│ ← 业务逻辑
│  - services/ (业务逻辑)               │
│  - database.py (数据库访问)           │
└──────────────┬───────────────────────┘
               │ 调用 Database
┌──────────────▼───────────────────────┐
│  Database Layer (PostgreSQL)         │ ← 数据存储
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  Scheduler Layer (scheduler/)        │ ← 独立调度
│  - tasks.py (定时同步)                │
│  - daily_stats.py (每日统计)          │
│  直接调用 Warehouse Service          │
└──────────────────────────────────────┘
```

---

## 三、职责划分

### 3.1 MCP 服务层 (mcp/)

**职责**: 提供 MCP 协议接口

**包含**:
- `server.py`: MCP 服务器初始化、工具注册
- `tools/`: 30+ 个 MCP 工具函数

**特点**:
- ✅ 对外暴露接口
- ✅ 参数验证
- ✅ 响应格式化
- ❌ 不包含业务逻辑

### 3.2 数据仓库层 (warehouse/)

**职责**: 数据管理和业务逻辑

**包含**:
- `database.py`: 数据库连接、SQL 查询
- `services/`: 业务逻辑实现
- `repositories/`: 数据访问（待创建）

**特点**:
- ✅ 业务规则实现
- ✅ 数据处理
- ✅ 数据库操作
- ❌ 不依赖 MCP

### 3.3 调度器层 (scheduler/)

**职责**: 定时任务调度

**包含**:
- `tasks.py`: 增量/全量同步
- `daily_stats.py`: 每日统计
- `ads_scheduler.py`: ADS 报表调度

**特点**:
- ✅ 独立运行
- ✅ 定时触发
- ✅ 直接调用 Service
- ❌ 不依赖 MCP 服务

---

## 四、调用流程

### 4.1 MCP 工具调用

```
用户请求
  ↓
MCP Tool (mcp/tools/issue_tools.py)
  ↓
Warehouse Service (warehouse/services/)
  ↓
Database (warehouse/database.py)
  ↓
PostgreSQL
```

### 4.2 定时任务调用

```
Cron 触发
  ↓
Scheduler Task (scheduler/tasks.py)
  ↓
Warehouse Service (warehouse/services/)
  ↓
Database (warehouse/database.py)
  ↓
PostgreSQL
```

---

## 五、重构成果

### 5.1 代码组织

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 目录数 | 2 | 6 |
| 主文件大小 | 91K | 1.5K (-98%) |
| 职责清晰度 | 低 | 高 |
| 模块独立性 | 低 | 高 |

### 5.2 可维护性

- ✅ **职责清晰**: 每层只做一件事
- ✅ **易于测试**: 各层独立测试
- ✅ **易于扩展**: 新增功能不影响其他层
- ✅ **可独立部署**: 调度器可单独运行

---

## 六、下一步计划

### 6.1 创建 Repository 层

```python
# warehouse/repositories/issue_repo.py
class IssueRepository:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_daily_stats(self, project_id, date):
        # SQL 查询
        ...
```

### 6.2 更新 Service 层

```python
# warehouse/services/stats_service.py
class StatsService:
    def __init__(self, issue_repo):
        self.repo = issue_repo
    
    def get_project_stats(self, project_id, date):
        # 业务逻辑
        stats = self.repo.get_daily_stats(project_id, date)
        return self._format_stats(stats)
```

### 6.3 更新 MCP 工具

```python
# mcp/tools/stats_tools.py
@mcp.tool()
async def get_project_daily_stats(project_id, date):
    service = get_stats_service()
    return service.get_project_stats(project_id, date)
```

---

**维护者**: OpenJaw  
**日期**: 2026-02-27
