# Redmine MCP - 架构重构方案

**目标**: 分离 MCP 服务和数据仓库，职责清晰

---

## 一、当前问题

### 1.1 逻辑混淆

- MCP 工具函数直接调用数仓
- 调度器依赖 MCP 初始化
- 职责边界不清

### 1.2 依赖混乱

```
redmine_handler.py (MCP)
    ↓
tools/*.py (工具)
    ↓
redmine_warehouse.py (数仓)
    ↑
redmine_scheduler.py (调度器)
```

---

## 二、新架构设计

### 2.1 目录结构

```
src/redmine_mcp_server/
├── main.py                      # 主入口
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── redmine_client.py        # Redmine API 客户端
│   └── config.py                # 配置管理
├── mcp/                         # MCP 服务层
│   ├── __init__.py
│   ├── server.py                # MCP 服务器初始化
│   └── tools/                   # MCP 工具
│       ├── __init__.py
│       ├── issue_tools.py
│       ├── project_tools.py
│       └── ...
├── warehouse/                   # 数据仓库层
│   ├── __init__.py
│   ├── database.py              # 数据库连接
│   ├── models.py                # 数据模型
│   ├── repositories/            # 数据访问层
│   │   ├── __init__.py
│   │   ├── issue_repo.py
│   │   ├── project_repo.py
│   │   └── stats_repo.py
│   └── services/                # 业务逻辑层
│       ├── __init__.py
│       ├── sync_service.py      # 同步服务
│       ├── analysis_service.py  # 分析服务
│       └── report_service.py    # 报表服务
└── scheduler/                   # 调度器层
    ├── __init__.py
    └── tasks.py                 # 定时任务
```

### 2.2 层次关系

```
┌─────────────────────────────────────┐
│         MCP Service Layer           │  ← 对外服务
│  (mcp/server.py + mcp/tools/)       │
└──────────────┬──────────────────────┘
               │ 调用
┌──────────────▼──────────────────────┐
│       Warehouse Service Layer       │  ← 业务逻辑
│  (warehouse/services/)              │
└──────────────┬──────────────────────┘
               │ 调用
┌──────────────▼──────────────────────┐
│     Warehouse Repository Layer      │  ← 数据访问
│  (warehouse/repositories/)          │
└──────────────┬──────────────────────┘
               │ 调用
┌──────────────▼──────────────────────┐
│      Warehouse Database Layer       │  ← 数据库连接
│  (warehouse/database.py)            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          Scheduler Layer            │  ← 独立调度
│  (scheduler/tasks.py)               │
│  直接调用 Warehouse Service Layer   │
└─────────────────────────────────────┘
```

---

## 三、职责划分

### 3.1 MCP 服务层

**职责**: 提供 MCP 协议接口，处理客户端请求

**包含**:
- MCP 服务器初始化
- 工具函数注册
- 请求参数验证
- 响应格式化

**不包含**:
- 业务逻辑
- 数据库操作

### 3.2 数据仓库层

**职责**: 数据管理、业务逻辑

**子层**:

#### Repository 层（数据访问）
- 直接数据库操作
- SQL 查询
- CRUD 操作

#### Service 层（业务逻辑）
- 业务规则
- 数据处理
- 调用 Repository

### 3.3 调度器层

**职责**: 定时任务调度

**特点**:
- 独立于 MCP 服务
- 直接调用 Service 层
- 可单独部署

---

## 四、重构步骤

### 4.1 第一阶段：创建新结构

1. 创建 core/、mcp/、warehouse/、scheduler/ 目录
2. 移动现有代码到新位置
3. 更新导入路径

### 4.2 第二阶段：分离数仓逻辑

1. 提取 redmine_warehouse.py → warehouse/database.py
2. 创建 warehouse/repositories/
3. 创建 warehouse/services/

### 4.3 第三阶段：重构 MCP 工具

1. 移动 tools/ → mcp/tools/
2. 工具调用 Service 层，不直接调用数据库
3. 参数验证和错误处理

### 4.4 第四阶段：独立调度器

1. 移动 redmine_scheduler.py → scheduler/tasks.py
2. 调度器调用 Service 层
3. 可配置独立运行

---

## 五、代码示例

### 5.1 Repository 层

```python
# warehouse/repositories/issue_repo.py
class IssueRepository:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_daily_stats(self, project_id: int, date: str) -> Dict:
        """获取项目每日统计"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.project_daily_summary
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, date))
                return dict(cur.fetchone())
```

### 5.2 Service 层

```python
# warehouse/services/stats_service.py
class StatsService:
    def __init__(self, issue_repo: IssueRepository):
        self.repo = issue_repo
    
    def get_project_daily_stats(self, project_id: int, date: str) -> Dict:
        """获取项目统计（业务逻辑）"""
        # 1. 参数验证
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 2. 调用 Repository
        stats = self.repo.get_daily_stats(project_id, date)
        
        # 3. 业务处理
        if not stats:
            return {"error": "No data found"}
        
        return {
            "project_id": project_id,
            "date": date,
            "total_issues": stats['total_issues'],
            "new_issues": stats['new_issues'],
            "closed_issues": stats['closed_issues'],
        }
```

### 5.3 MCP 工具层

```python
# mcp/tools/stats_tools.py
@mcp.tool()
async def get_project_daily_stats(
    project_id: int,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """MCP 工具：获取项目每日统计"""
    try:
        # 调用 Service 层
        service = get_stats_service()
        result = service.get_project_daily_stats(project_id, date)
        return result
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": str(e)}
```

### 5.4 调度器层

```python
# scheduler/tasks.py
class SyncTask:
    def __init__(self, sync_service: SyncService):
        self.service = sync_service
    
    def run_incremental_sync(self):
        """增量同步任务"""
        projects = self._get_subscribed_projects()
        for project_id in projects:
            self.service.incremental_sync(project_id)
    
    def _get_subscribed_projects(self) -> List[int]:
        """获取订阅的项目列表"""
        # 独立于 MCP 的实现
        ...
```

---

## 六、依赖关系

### 6.1 依赖方向

```
MCP Layer → Service Layer → Repository Layer → Database
Scheduler → Service Layer → Repository Layer → Database
```

### 6.2 禁止的依赖

- ❌ Repository → Service (反向依赖)
- ❌ Service → MCP (跨层依赖)
- ❌ Scheduler → MCP (独立运行)

---

## 七、预期效果

### 7.1 代码组织

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 目录数 | 2 | 6 |
| 最大文件 | 91K | <10K |
| 职责清晰度 | 低 | 高 |

### 7.2 可维护性

- ✅ 职责清晰：每层只做一件事
- ✅ 易于测试：各层独立测试
- ✅ 易于扩展：新增功能不影响其他层
- ✅ 可独立部署：调度器可单独运行

### 7.3 性能影响

- ⚠️ 调用链略长（+1-2 层）
- ✅ 性能影响可忽略（<1ms）
- ✅ 可缓存优化

---

**维护者**: OpenJaw  
**日期**: 2026-02-27
