# Redmine MCP 数仓扩展 - 贡献者分析

**文档版本**: 1.0  
**最后更新**: 2026-02-27  
**MCP Server**: v0.10.0

---

## 一、现有架构

### 1.1 MCP 数仓整合架构

```
/docker/redmine-mcp-server/
├── src/redmine_mcp_server/
│   ├── main.py                    # MCP 入口
│   ├── redmine_handler.py         # MCP Tools 实现 ⭐
│   │   ├── get_project_daily_stats()  ← 现有数仓工具
│   │   ├── trigger_full_sync()        ← 同步触发
│   │   └── subscribe_project()        ← 订阅管理
│   ├── redmine_warehouse.py       # 数仓访问层 ⭐
│   │   ├── DataWarehouse 类
│   │   ├── upsert_issues_batch()
│   │   ├── get_issues_snapshot()
│   │   ├── get_project_daily_stats()
│   │   └── get_high_priority_issues()
│   └── redmine_scheduler.py       # 定时调度器
│       ├── 每 10 分钟增量同步
│       └── 每天全量同步
└── docs/
    └── WAREHOUSE_SYNC.md          # 数仓同步文档

/docker/redmine-warehouse/
├── docker-compose.yml             # PostgreSQL 容器
├── .env                           # 数据库配置
└── init-scripts/
    ├── 01-schema.sql              # Schema 创建
    └── 02-tables.sql              # 现有表结构
        ├── warehouse.issue_daily_snapshot
        └── warehouse.project_daily_summary
```

### 1.2 现有 MCP 工具（数仓相关）

| 工具名 | 功能 | 数仓表 |
|--------|------|--------|
| `get_project_daily_stats` | 项目每日统计 | `project_daily_summary` |
| `trigger_full_sync` | 触发全量同步 | `issue_daily_snapshot` |
| `subscribe_project` | 订阅项目 | subscriptions |

---

## 二、扩展需求

### 2.1 新增功能

围绕现有 MCP 数仓，扩展以下功能：

1. **Issue 贡献者分析** - 分析每个 Issue 的所有贡献者，按角色分类
2. **项目角色分布** - 统计项目中各角色的人员分布
3. **用户工作量统计** - 按用户统计工作量（Issue 数、操作数）

### 2.2 设计原则

1. **保持 MCP 中心** - 所有功能通过 MCP Tools 暴露
2. **复用现有架构** - 使用现有的 `DataWarehouse` 类和连接池
3. **增量扩展** - 在现有表基础上增加新表，不影响现有功能
4. **同步机制一致** - 使用现有的 scheduler 机制触发数据同步

---

## 三、数据库表扩展

### 3.1 新增表结构

创建文件：`/docker/redmine-warehouse/init-scripts/03-contributor-analysis.sql`

```sql
-- Issue 贡献者分析表
CREATE TABLE IF NOT EXISTS warehouse.issue_contributors (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(200),
    highest_role_id INTEGER,
    highest_role_name VARCHAR(100),
    role_category VARCHAR(20),  -- manager/implementation/developer/tester/other
    journal_count INTEGER DEFAULT 0,
    first_contribution TIMESTAMP,
    last_contribution TIMESTAMP,
    status_change_count INTEGER DEFAULT 0,
    note_count INTEGER DEFAULT 0,
    assigned_change_count INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_issue_contributor UNIQUE (issue_id, user_id)
);

-- Issue 贡献者汇总表
CREATE TABLE IF NOT EXISTS warehouse.issue_contributor_summary (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    manager_count INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    tester_count INTEGER DEFAULT 0,
    other_count INTEGER DEFAULT 0,
    total_contributors INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户项目角色表
CREATE TABLE IF NOT EXISTS warehouse.user_project_role (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    highest_role_id INTEGER,
    highest_role_name VARCHAR(100),
    role_category VARCHAR(20),
    role_priority INTEGER,
    all_role_ids VARCHAR(200),
    is_direct_member BOOLEAN DEFAULT TRUE,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_user_project_role UNIQUE (project_id, user_id)
);

-- 项目角色分布表
CREATE TABLE IF NOT EXISTS warehouse.project_role_distribution (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    manager_count INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    tester_count INTEGER DEFAULT 0,
    other_count INTEGER DEFAULT 0,
    total_members INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_project_role_dist UNIQUE (project_id, snapshot_date)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_contributors_issue ON warehouse.issue_contributors(issue_id);
CREATE INDEX IF NOT EXISTS idx_contributors_user ON warehouse.issue_contributors(user_id);
CREATE INDEX IF NOT EXISTS idx_contributors_category ON warehouse.issue_contributors(role_category);
CREATE INDEX IF NOT EXISTS idx_user_role_project ON warehouse.user_project_role(project_id);
CREATE INDEX IF NOT EXISTS idx_user_role_user ON warehouse.user_project_role(user_id);
CREATE INDEX IF NOT EXISTS idx_project_role_dist_date ON warehouse.project_role_distribution(project_id, snapshot_date);
```

### 3.2 应用扩展

```bash
# 执行扩展 SQL
docker exec redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -f /init-scripts/03-contributor-analysis.sql
```

---

## 四、MCP 代码扩展

### 4.1 扩展 DataWarehouse 类

文件：`/docker/redmine-mcp-server/src/redmine_mcp_server/redmine_warehouse.py`

```python
class DataWarehouse:
    # ... 现有代码 ...
    
    # ========== 新增：贡献者分析相关方法 ==========
    
    def upsert_issue_contributors(self, issue_id: int, project_id: int, 
                                   contributors: List[Dict]):
        """插入或更新 Issue 贡献者"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for contrib in contributors:
                    cur.execute("""
                        INSERT INTO warehouse.issue_contributors (
                            issue_id, project_id, user_id, user_name,
                            highest_role_id, highest_role_name, role_category,
                            journal_count, first_contribution, last_contribution,
                            status_change_count, note_count, assigned_change_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (issue_id, user_id) DO UPDATE SET
                            journal_count = EXCLUDED.journal_count,
                            last_contribution = EXCLUDED.last_contribution,
                            status_change_count = EXCLUDED.status_change_count,
                            note_count = EXCLUDED.note_count
                    """, (
                        issue_id, project_id, contrib['user_id'], contrib['user_name'],
                        contrib.get('highest_role_id'), contrib.get('highest_role_name'),
                        contrib.get('role_category'), contrib.get('journal_count', 0),
                        contrib.get('first_contribution'), contrib.get('last_contribution'),
                        contrib.get('status_change_count', 0), contrib.get('note_count', 0),
                        contrib.get('assigned_change_count', 0)
                    ))
                
                # Update summary
                self._refresh_contributor_summary(cur, issue_id, project_id)
    
    def _refresh_contributor_summary(self, cur, issue_id: int, project_id: int):
        """刷新贡献者汇总"""
        cur.execute("""
            INSERT INTO warehouse.issue_contributor_summary (
                issue_id, project_id, manager_count, implementation_count,
                developer_count, tester_count, other_count,
                total_contributors, total_journals
            )
            SELECT 
                %s, %s,
                SUM(CASE WHEN role_category='manager' THEN 1 ELSE 0 END),
                SUM(CASE WHEN role_category='implementation' THEN 1 ELSE 0 END),
                SUM(CASE WHEN role_category='developer' THEN 1 ELSE 0 END),
                SUM(CASE WHEN role_category='tester' THEN 1 ELSE 0 END),
                SUM(CASE WHEN role_category NOT IN ('manager','implementation','developer','tester') THEN 1 ELSE 0 END),
                COUNT(*),
                SUM(journal_count)
            FROM warehouse.issue_contributors
            WHERE issue_id = %s
            ON CONFLICT (issue_id) DO UPDATE SET
                manager_count = EXCLUDED.manager_count,
                implementation_count = EXCLUDED.implementation_count,
                developer_count = EXCLUDED.developer_count,
                tester_count = EXCLUDED.tester_count,
                other_count = EXCLUDED.other_count,
                total_contributors = EXCLUDED.total_contributors,
                total_journals = EXCLUDED.total_journals
        """, (issue_id, project_id, issue_id))
    
    def get_issue_contributors(self, issue_id: int) -> List[Dict]:
        """获取 Issue 贡献者列表"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        user_id, user_name, role_category, highest_role_name,
                        journal_count, first_contribution, last_contribution
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
    
    def get_issue_contributor_summary(self, issue_id: int) -> Optional[Dict]:
        """获取 Issue 贡献者汇总"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.issue_contributor_summary
                    WHERE issue_id = %s
                """, (issue_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    
    def upsert_user_project_roles(self, project_id: int, roles: List[Dict]):
        """批量插入用户项目角色"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for role in roles:
                    cur.execute("""
                        INSERT INTO warehouse.user_project_role (
                            project_id, user_id, highest_role_id, highest_role_name,
                            role_category, role_priority, all_role_ids, is_direct_member
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (project_id, user_id) DO UPDATE SET
                            highest_role_id = EXCLUDED.highest_role_id,
                            highest_role_name = EXCLUDED.highest_role_name,
                            role_category = EXCLUDED.role_category,
                            role_priority = EXCLUDED.role_priority
                    """, (
                        project_id, role['user_id'], role.get('highest_role_id'),
                        role.get('highest_role_name'), role.get('role_category'),
                        role.get('role_priority'), role.get('all_role_ids'),
                        role.get('is_direct_member', True)
                    ))
    
    def refresh_project_role_distribution(self, project_id: int, snapshot_date: date):
        """刷新项目角色分布"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO warehouse.project_role_distribution (
                        project_id, snapshot_date, manager_count,
                        implementation_count, developer_count, tester_count,
                        other_count, total_members
                    )
                    SELECT 
                        %s, %s,
                        SUM(CASE WHEN role_category='manager' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN role_category='implementation' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN role_category='developer' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN role_category='tester' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN role_category NOT IN ('manager','implementation','developer','tester') THEN 1 ELSE 0 END),
                        COUNT(*)
                    FROM warehouse.user_project_role
                    WHERE project_id = %s
                    ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
                        manager_count = EXCLUDED.manager_count,
                        implementation_count = EXCLUDED.implementation_count,
                        developer_count = EXCLUDED.developer_count,
                        tester_count = EXCLUDED.tester_count,
                        other_count = EXCLUDED.other_count,
                        total_members = EXCLUDED.total_members
                """, (project_id, snapshot_date.isoformat(), project_id))
```

### 4.2 新增 MCP Tools

文件：`/docker/redmine-mcp-server/src/redmine_mcp_server/redmine_handler.py`

```python
@mcp.tool()
async def analyze_issue_contributors(issue_id: int) -> Dict[str, Any]:
    """
    分析 Issue 的贡献者（按角色分类）
    
    从数仓中获取 Issue 的所有贡献者，按角色优先级排序：
    - 管理人员 > 实施人员 > 开发人员 > 测试人员
    
    Args:
        issue_id: Issue ID
    
    Returns:
        贡献者列表和汇总统计
    """
    from .redmine_warehouse import DataWarehouse
    
    try:
        warehouse = DataWarehouse()
        
        # 获取贡献者
        contributors = warehouse.get_issue_contributors(issue_id)
        
        # 获取汇总
        summary = warehouse.get_issue_contributor_summary(issue_id)
        
        if not contributors:
            # 如果数仓中没有，触发分析
            logger.info(f"No contributors in warehouse, analyzing issue {issue_id}...")
            # TODO: 调用分析逻辑
            return {"issue_id": issue_id, "message": "Contributors not yet analyzed"}
        
        return {
            "issue_id": issue_id,
            "contributors": contributors,
            "summary": summary,
            "from_cache": True
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze contributors: {e}")
        return {"error": f"Failed to analyze contributors: {str(e)}"}


@mcp.tool()
async def get_project_role_distribution(
    project_id: int,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取项目角色分布
    
    Args:
        project_id: 项目 ID
        date: 日期（YYYY-MM-DD），默认今天
    
    Returns:
        各角色的人员数量
    """
    from datetime import date as date_class
    from .redmine_warehouse import DataWarehouse
    
    try:
        warehouse = DataWarehouse()
        query_date = datetime.strptime(date, '%Y-%m-%d').date() if date else date_class.today()
        
        # 查询数仓
        with warehouse.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM warehouse.project_role_distribution
                    WHERE project_id = %s AND snapshot_date = %s
                """, (project_id, query_date.isoformat()))
                
                row = cur.fetchone()
                
                if row:
                    return dict(row)
                
                # 如果没有，触发计算
                logger.info(f"No role distribution for {project_id} on {query_date}, calculating...")
                # TODO: 调用计算逻辑
                
                return {"project_id": project_id, "date": query_date.isoformat(), "message": "Not yet calculated"}
        
    except Exception as e:
        logger.error(f"Failed to get role distribution: {e}")
        return {"error": f"Failed to get role distribution: {str(e)}"}


@mcp.tool()
async def get_user_workload(
    user_id: int,
    year_month: Optional[str] = None,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取用户工作量统计
    
    Args:
        user_id: 用户 ID
        year_month: 年月（YYYY-MM），默认本月
        project_id: 项目 ID（可选）
    
    Returns:
        工作量统计信息
    """
    from datetime import datetime
    from .redmine_warehouse import DataWarehouse
    
    if not year_month:
        year_month = datetime.now().strftime('%Y-%m')
    
    try:
        warehouse = DataWarehouse()
        
        # 查询数仓
        with warehouse.get_connection() as conn:
            with conn.cursor() as cur:
                if project_id:
                    cur.execute("""
                        SELECT * FROM warehouse.user_workload
                        WHERE user_id = %s AND year_month = %s AND project_id = %s
                    """, (user_id, year_month, project_id))
                else:
                    cur.execute("""
                        SELECT 
                            project_id, 
                            SUM(total_issues) as total_issues,
                            SUM(total_journals) as total_journals,
                            SUM(as_manager) as as_manager,
                            SUM(as_developer) as as_developer,
                            SUM(as_implementation) as as_implementation
                        FROM warehouse.user_workload
                        WHERE user_id = %s AND year_month = %s
                        GROUP BY project_id
                    """, (user_id, year_month))
                
                rows = cur.fetchall()
                
                if rows:
                    return {
                        "user_id": user_id,
                        "year_month": year_month,
                        "projects": [dict(row) for row in rows]
                    }
                
                return {"user_id": user_id, "year_month": year_month, "message": "No data yet"}
        
    except Exception as e:
        logger.error(f"Failed to get workload: {e}")
        return {"error": f"Failed to get workload: {str(e)}"}
```

---

## 五、数据同步扩展

### 5.1 贡献者分析同步

在 `redmine_scheduler.py` 中添加定时任务：

```python
class RedmineScheduler:
    # ... 现有代码 ...
    
    async def sync_contributor_analysis(self, project_id: int):
        """同步项目贡献者分析"""
        logger.info(f"Starting contributor analysis sync for project {project_id}...")
        
        try:
            # 1. 获取项目所有 Issue
            issues = await self.fetch_project_issues(project_id)
            
            # 2. 对每个 Issue 分析贡献者
            for issue in issues:
                await self.analyze_issue_contributors(issue)
            
            # 3. 计算项目角色分布
            await self.calculate_project_role_distribution(project_id)
            
            logger.info(f"Contributor analysis sync completed for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to sync contributor analysis: {e}")
    
    async def analyze_issue_contributors(self, issue: Dict):
        """分析单个 Issue 的贡献者"""
        issue_id = issue['id']
        project_id = issue['project']['id']
        
        # 1. 获取 Issue 的 journals
        journals = await self.fetch_issue_journals(issue_id)
        
        # 2. 提取贡献者
        contributors = self.extract_contributors_from_journals(journals)
        
        # 3. 获取用户在项目中的角色
        for contrib in contributors:
            role = await self.get_user_project_role(project_id, contrib['user_id'])
            contrib.update(role)
        
        # 4. 保存到数仓
        warehouse = DataWarehouse()
        warehouse.upsert_issue_contributors(issue_id, project_id, contributors)
```

### 5.2 同步触发器

扩展 `trigger_full_sync` 工具：

```python
@mcp.tool()
async def trigger_full_sync(
    project_id: Optional[int] = None,
    include_contributors: bool = False
) -> Dict[str, Any]:
    """
    Trigger full data sync for warehouse (manual)
    
    Args:
        project_id: 项目 ID（可选，默认所有订阅项目）
        include_contributors: 是否包含贡献者分析
    """
    # ... 现有同步逻辑 ...
    
    if include_contributors:
        logger.info("Triggering contributor analysis sync...")
        # 触发贡献者分析同步
        await scheduler.sync_contributor_analysis(project_id)
    
    return {"status": "success", "message": "Full sync triggered"}
```

---

## 六、使用示例

### 6.1 MCP 工具调用

```python
# 通过 MCP Client 调用
from mcp import Client

async with Client() as client:
    # 分析 Issue 贡献者
    result = await client.call_tool(
        "analyze_issue_contributors",
        {"issue_id": 76361}
    )
    print(result)
    # 输出:
    # {
    #   "issue_id": 76361,
    #   "contributors": [
    #     {"user_name": "刘雅娇", "role_category": "implementation", "journal_count": 7},
    #     {"user_name": "曾聚", "role_category": "developer", "journal_count": 2}
    #   ],
    #   "summary": {
    #     "manager_count": 0,
    #     "implementation_count": 1,
    #     "developer_count": 1,
    #     "total_contributors": 2
    #   }
    # }
    
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

### 6.2 SQL 直接查询

```bash
# 查询 Issue 贡献者
docker exec redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT user_name, role_category, journal_count 
      FROM warehouse.issue_contributors 
      WHERE issue_id = 76361;"

# 查询项目角色分布
docker exec redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT * FROM warehouse.project_role_distribution 
      WHERE project_id = 357 
      ORDER BY snapshot_date DESC 
      LIMIT 1;"
```

---

## 七、部署步骤

### 7.1 数据库扩展

```bash
# 1. 创建扩展 SQL 文件
cat > /docker/redmine-warehouse/init-scripts/03-contributor-analysis.sql << 'EOF'
-- (上面的 SQL 内容)
EOF

# 2. 执行扩展
docker exec redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -f /init-scripts/03-contributor-analysis.sql
```

### 7.2 MCP 服务器更新

```bash
cd /docker/redmine-mcp-server

# 1. 更新 redmine_warehouse.py
# 添加贡献者分析方法

# 2. 更新 redmine_handler.py  
# 添加新的 MCP Tools

# 3. 更新 redmine_scheduler.py
# 添加贡献者同步逻辑

# 4. 重启服务
docker-compose restart redmine-mcp-server
```

### 7.3 验证

```bash
# 检查 MCP 工具
mcp list-tools | grep -E "contributor|role|workload"

# 测试工具调用
mcp call analyze_issue_contributors '{"issue_id": 76361}'
```

---

## 八、性能优化

### 8.1 缓存策略

- **Issue 贡献者**: 分析后缓存，仅在 journals 变更时更新
- **项目角色分布**: 每天计算一次
- **用户工作量**: 每月计算一次

### 8.2 增量更新

```python
# 只分析有新 journals 的 Issue
async def incremental_contributor_sync(project_id: int):
    # 获取最近更新的 Issue
    updated_issues = await fetch_issues_updated_since(project_id, last_sync_time)
    
    for issue in updated_issues:
        # 检查是否有新 journals
        new_journals = await fetch_new_journals(issue['id'], last_sync_time)
        if new_journals:
            await analyze_issue_contributors(issue)
```

---

## 九、监控与日志

### 9.1 日志记录

```python
logger.info(f"Analyzed {len(contributors)} contributors for issue {issue_id}")
logger.info(f"Project {project_id} role distribution: {distribution}")
```

### 9.2 监控指标

- 贡献者分析耗时
- 数仓表数据量
- 缓存命中率

---

## 十、总结

### 10.1 架构优势

1. **MCP 中心**: 所有功能通过 MCP Tools 统一暴露
2. **现有整合**: 完全复用现有的 `DataWarehouse` 类和连接池
3. **增量扩展**: 不影响现有功能，逐步添加新表和新工具
4. **同步一致**: 使用现有的 scheduler 机制

### 10.2 扩展路径

```
现有: Issue 快照 + 项目统计
  ↓
扩展 1: 贡献者分析 (本期)
  ↓
扩展 2: 用户工作量统计
  ↓
扩展 3: 质量报表 + 团队负载分析
```

---

**维护者**: OpenJaw <openjaw@gmail.com>  
**项目**: `/docker/redmine-mcp-server/`
