# Redmine MCP - 贡献者分析功能

**版本**: 1.0  
**实现日期**: 2026-02-27  
**MCP Server**: v0.10.0

---

## 概述

贡献者分析功能扩展了 Redmine MCP 数仓，支持：
- 分析每个 Issue 的所有贡献者
- 按角色分类（管理/实施/开发/测试/其他）
- 统计贡献者工作量（journals 数量、状态变更等）
- 项目角色分布统计
- 用户工作量跨项目统计

---

## 新增 MCP 工具

### 1. `analyze_issue_contributors`

分析单个 Issue 的贡献者。

**参数**:
- `issue_id` (int): Issue ID

**返回**:
```json
{
  "issue_id": 76361,
  "contributors": [
    {
      "user_id": 1492,
      "user_name": "刘 雅娇",
      "role_category": "implementation",
      "journal_count": 7,
      "status_change_count": 2,
      "first_contribution": "2026-02-13T07:46:08",
      "last_contribution": "2026-01-05T01:14:16"
    }
  ],
  "summary": {
    "manager_count": 0,
    "implementation_count": 2,
    "developer_count": 0,
    "tester_count": 0,
    "total_contributors": 2,
    "total_journals": 9
  },
  "from_cache": true
}
```

### 2. `get_project_role_distribution`

获取项目角色分布统计。

**参数**:
- `project_id` (int): 项目 ID
- `date` (str, optional): 日期 (YYYY-MM-DD)，默认今天

**返回**:
```json
{
  "project_id": 357,
  "snapshot_date": "2026-02-27",
  "manager_count": 2,
  "implementation_count": 5,
  "developer_count": 3,
  "tester_count": 2,
  "other_count": 1,
  "total_members": 13
}
```

### 3. `get_user_workload`

获取用户工作量统计。

**参数**:
- `user_id` (int): 用户 ID
- `year_month` (str, optional): 年月 (YYYY-MM)，默认本月
- `project_id` (int, optional): 项目 ID

**返回**:
```json
{
  "user_id": 1492,
  "year_month": "2026-02",
  "projects": [
    {
      "project_id": 357,
      "total_issues": 15,
      "total_journals": 45,
      "as_manager": 0,
      "as_implementation": 12,
      "as_developer": 3,
      "as_tester": 0
    }
  ]
}
```

### 4. `trigger_contributor_sync`

触发贡献者分析同步。

**参数**:
- `project_id` (int, optional): 项目 ID（分析整个项目）
- `issue_ids` (List[int], optional): Issue ID 列表（分析特定 Issue）

**返回**:
```json
{
  "success": true,
  "message": "Contributor analysis completed",
  "results": {
    "project_id": 357,
    "total_analyzed": 50,
    "analyzed_issues": [76361, 77795, ...],
    "errors": []
  }
}
```

---

## 数据库扩展

### 新增表结构

执行 `/docker/redmine-mcp-server/init-scripts/03-contributor-analysis.sql` 创建以下表：

1. **`warehouse.issue_contributors`** - Issue 贡献者明细
2. **`warehouse.issue_contributor_summary`** - Issue 贡献者汇总
3. **`warehouse.user_project_role`** - 用户项目角色
4. **`warehouse.project_role_distribution`** - 项目角色分布
5. **`warehouse.user_workload`** - 用户工作量统计

### 应用扩展

```bash
# 执行扩展 SQL
docker exec redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/03-contributor-analysis.sql
```

---

## 使用示例

### 分析单个 Issue 的贡献者

```python
from mcp import Client

async with Client() as client:
    result = await client.call_tool(
        "analyze_issue_contributors",
        {"issue_id": 76361}
    )
    print(result)
```

### 触发项目贡献者同步

```python
result = await client.call_tool(
    "trigger_contributor_sync",
    {"project_id": 357}
)
```

### 查询项目角色分布

```python
result = await client.call_tool(
    "get_project_role_distribution",
    {"project_id": 357, "date": "2026-02-27"}
)
```

### 查询用户工作量

```python
result = await client.call_tool(
    "get_user_workload",
    {"user_id": 1492, "year_month": "2026-02"}
)
```

---

## 角色分类逻辑

角色分类基于 Redmine 项目成员的角色名称：

| 类别 | 角色名称匹配 |
|------|-------------|
| **manager** | project manager, manager, 负责人，项目经理 |
| **implementation** | implementation, 实施，实施人员 |
| **developer** | developer, 开发，开发人员，engineer |
| **tester** | tester, 测试，测试人员，qa |
| **other** | viewer, 报告者，reporter, 其他 |

**优先级**: manager > implementation > developer > tester > other

当用户在项目中拥有多个角色时，取优先级最高的角色。

---

## 实现细节

### 贡献者提取

从 Issue 的 Journals 中提取贡献者：

1. 遍历所有 Journals
2. 按 user_id 聚合
3. 统计每个用户的：
   - journal_count: 总操作数
   - status_change_count: 状态变更次数
   - note_count: 评论数
   - assigned_change_count: 指派人变更次数
   - first/last_contribution: 首次/最后贡献时间

### 角色映射

1. 获取项目在 Redmine 中的成员列表
2. 对每个成员，获取其所有角色
3. 根据角色名称映射到角色类别
4. 取优先级最高的角色作为该用户的主要角色

---

## 性能优化

### 缓存策略

- **Issue 贡献者**: 分析后缓存到数仓，仅在 trigger_contributor_sync 时更新
- **项目角色分布**: 每天计算一次
- **用户工作量**: 每月计算一次

### 增量更新

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

## 已知限制

1. **角色识别**: 依赖于 Redmine 项目成员配置，如果用户未添加到项目成员，角色识别可能不准确
2. **历史数据**: 需要手动触发 `trigger_contributor_sync` 来填充历史数据
3. **API 限制**: 大量 Issue 的项目可能需要较长时间完成同步

---

## 后续扩展

### 短期

- [ ] 优化角色识别逻辑（基于用户组）
- [ ] 添加贡献者趋势分析
- [ ] 支持按时间范围查询贡献者

### 中期

- [ ] Issue 质量报表（重开次数、平均解决时间）
- [ ] 团队负载分析（识别超负载/低负载人员）
- [ ] 用户工作量跨项目汇总

### 长期

- [ ] 预测分析（基于历史数据预测项目风险）
- [ ] 自动化报告（定期生成并发送报告）
- [ ] 可视化 Dashboard（Grafana 集成）

---

## 测试验证

### 验证步骤

```bash
# 1. 应用数据库扩展
docker exec redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/03-contributor-analysis.sql

# 2. 重启 MCP 服务器
cd /docker/redmine-mcp-server && docker compose restart redmine-mcp-server

# 3. 验证新工具
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  grep -o '"name":"[^"]*contributor[^"]*"'

# 4. 触发贡献者同步
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"trigger_contributor_sync","arguments":{"project_id":357}}}'

# 5. 查询贡献者分析
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"analyze_issue_contributors","arguments":{"issue_id":76361}}}'
```

### 预期结果

- ✅ 4 个新 MCP 工具可用
- ✅ 数据库表创建成功
- ✅ 贡献者分析返回正确数据
- ✅ 角色分类准确

---

## 相关文件

- **SQL 扩展**: `/docker/redmine-mcp-server/init-scripts/03-contributor-analysis.sql`
- **数仓访问层**: `/docker/redmine-mcp-server/src/redmine_mcp_server/redmine_warehouse.py`
- **MCP 工具**: `/docker/redmine-mcp-server/src/redmine_mcp_server/redmine_handler.py`
- **分析器**: `/docker/redmine-mcp-server/src/redmine_mcp_server/dev_test_analyzer.py`
- **架构文档**: `/docker/redmine-mcp-server/docs/WAREHOUSE_CONTRIBUTOR_EXTENSION.md`

---

**维护者**: OpenJaw <openjaw@gmail.com>  
**项目**: `/docker/redmine-mcp-server/`
