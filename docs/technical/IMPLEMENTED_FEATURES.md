# Redmine MCP 数仓 - 已实现功能清单

**最后更新**: 2026-02-27  
**MCP Server**: v0.10.0

---

## ✅ 已实现功能总览

### 核心 MCP 工具（30 个）

| 分类 | 工具名 | 说明 | 状态 |
|------|--------|------|------|
| **Issue 管理** | `get_redmine_issue` | 获取 Issue 详情 | ✅ |
| | `list_my_redmine_issues` | 我的 Issue 列表 | ✅ |
| | `search_redmine_issues` | 搜索 Issue | ✅ |
| | `create_redmine_issue` | 创建 Issue | ✅ |
| | `update_redmine_issue` | 更新 Issue | ✅ |
| **项目管理** | `list_redmine_projects` | 项目列表 | ✅ |
| | `summarize_project_status` | 项目状态汇总 | ✅ |
| **Wiki 管理** | `get_redmine_wiki_page` | 获取 Wiki 页面 | ✅ |
| | `create_redmine_wiki_page` | 创建 Wiki | ✅ |
| | `update_redmine_wiki_page` | 更新 Wiki | ✅ |
| | `delete_redmine_wiki_page` | 删除 Wiki | ✅ |
| **附件管理** | `get_redmine_attachment_download_url` | 附件下载链接 | ✅ |
| | `cleanup_attachment_files` | 清理附件 | ✅ |
| **全局搜索** | `search_entire_redmine` | 全局搜索 | ✅ |
| **订阅管理** | `subscribe_project` | 订阅项目 | ✅ |
| | `unsubscribe_project` | 取消订阅 | ✅ |
| | `list_my_subscriptions` | 我的订阅 | ✅ |
| | `get_subscription_stats` | 订阅统计 | ✅ |
| | `generate_subscription_report` | 生成订阅报告 | ✅ |
| **数仓同步** | `trigger_full_sync` | 全量同步 | ✅ |
| | `trigger_progressive_sync` | 增量同步 | ✅ |
| | `get_sync_progress` | 同步进度 | ✅ |
| | `backfill_historical_data` | 历史数据回填 | ✅ |
| **统计分析** | `get_project_daily_stats` | 项目每日统计 | ✅ |
| | `analyze_dev_tester_workload` | 开发/测试工作量分析 | ✅ |
| **贡献者分析** | `analyze_issue_contributors` | Issue 贡献者分析 | ✅ |
| | `get_project_role_distribution` | 项目角色分布 | ✅ |
| | `get_user_workload` | 用户工作量统计 | ✅ |
| | `trigger_contributor_sync` | 触发贡献者同步 | ✅ |

---

## 📊 已实现的数仓功能

### 1. 数据同步机制

**文件**: `src/redmine_mcp_server/redmine_scheduler.py`

| 功能 | 说明 | 频率 |
|------|------|------|
| **增量同步** | 同步最近 13 分钟更新的 Issue | 每 10 分钟 |
| **全量同步** | 同步项目所有 Issue | 每天/手动触发 |
| **历史回填** | 回填历史快照数据 | 手动触发 |
| **订阅管理** | 基于订阅的项目列表 | 自动维护 |

**数据库表**:
- `warehouse.issue_daily_snapshot` - Issue 每日快照
- `warehouse.project_daily_summary` - 项目每日汇总

### 2. 项目统计工具

**MCP Tool**: `get_project_daily_stats`

**功能**:
- ✅ 获取项目每日统计（新增/关闭/更新 Issue 数）
- ✅ 按状态分布统计（新建/进行中/已解决/已关闭）
- ✅ 按优先级分布统计（立刻/紧急/高/普通/低）
- ✅ 高优先级 Issue 列表
- ✅ 人员任务量 TOP 10
- ✅ 支持对比昨天数据

**示例**:
```python
get_project_daily_stats(project_id=357, date="2026-02-27", compare_with="yesterday")
```

### 3. 开发/测试工作量分析

**MCP Tool**: `analyze_dev_tester_workload`  
**文件**: `src/redmine_mcp_server/dev_test_analyzer.py`

**功能**:
- ✅ 基于 Journals 分析 Issue 状态流转
- ✅ 识别开发人员（将状态改为"已解决"的人）
- ✅ 识别测试人员（开发指定验证的人）
- ✅ 统计开发工作量（解决 Issue 数）
- ✅ 统计测试工作量（验证 Issue 数）
- ✅ 分析协作模式（自解自测 vs 协作测试）

**输出示例**:
```
======================================================================
📊 Project 341 - Dev/Test Workload Analysis
======================================================================
Total Resolved Issues: 17

👨‍💻 Developers (resolved issues):
--------------------------------------------------
刘 雅娇                      |   9 issues
汪 晓娟                      |   3 issues
邓 时杰                      |   1 issues

🧪 Testers (assigned to verify):
--------------------------------------------------
刘 雅娇                      |   9 issues
汪 晓娟                      |   3 issues
杨 志平                      |   2 issues

🤝 Collaborations:
--------------------------------------------------
刘 雅娇 → 刘 雅娇                         |   9 issues
汪 晓娟 → 汪 晓娟                         |   3 issues
王 路 → 杨 志平                          |   1 issues
======================================================================
```

### 4. 贡献者分析（2026-02-27 新增）

**MCP Tools**: `analyze_issue_contributors`, `get_project_role_distribution`, `get_user_workload`, `trigger_contributor_sync`  
**文件**: `src/redmine_mcp_server/dev_test_analyzer.py`, `src/redmine_mcp_server/redmine_handler.py`

**功能**:
- ✅ 基于 Journals 分析 Issue 所有贡献者
- ✅ 按角色分类（管理/实施/开发/测试/其他）
- ✅ 统计贡献者工作量（journals 数、状态变更等）
- ✅ 项目角色分布统计
- ✅ 用户工作量跨项目统计

**数据库表**:
- `warehouse.issue_contributors` - Issue 贡献者明细
- `warehouse.issue_contributor_summary` - Issue 贡献者汇总
- `warehouse.user_project_role` - 用户项目角色
- `warehouse.project_role_distribution` - 项目角色分布
- `warehouse.user_workload` - 用户工作量统计

**输出示例**:
```json
{
  "issue_id": 76361,
  "contributors": [
    {
      "user_name": "刘 雅娇",
      "role_category": "implementation",
      "journal_count": 7,
      "status_change_count": 2
    }
  ],
  "summary": {
    "implementation_count": 2,
    "total_contributors": 2,
    "total_journals": 9
  }
}
```

---

## 🗄️ 数据库表结构

### 已实现的表

```sql
-- Issue 每日快照
CREATE TABLE warehouse.issue_daily_snapshot (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    subject TEXT,
    status_id INTEGER,
    status_name TEXT,
    priority_id INTEGER,
    priority_name TEXT,
    assigned_to_id INTEGER,
    assigned_to_name TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_new BOOLEAN DEFAULT FALSE,
    is_closed BOOLEAN DEFAULT FALSE,
    is_updated BOOLEAN DEFAULT FALSE,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_issue_snapshot UNIQUE (issue_id, snapshot_date)
);

-- 项目每日汇总
CREATE TABLE warehouse.project_daily_summary (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    total_issues INTEGER DEFAULT 0,
    new_issues INTEGER DEFAULT 0,
    closed_issues INTEGER DEFAULT 0,
    status_new INTEGER DEFAULT 0,
    status_in_progress INTEGER DEFAULT 0,
    status_resolved INTEGER DEFAULT 0,
    status_closed INTEGER DEFAULT 0,
    priority_immediate INTEGER DEFAULT 0,
    priority_urgent INTEGER DEFAULT 0,
    priority_high INTEGER DEFAULT 0,
    priority_normal INTEGER DEFAULT 0,
    priority_low INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_project_summary UNIQUE (project_id, snapshot_date)
);
```

---

## 🎯 功能亮点

### 1. 订阅驱动的同步机制

- ✅ 用户订阅项目后自动加入同步列表
- ✅ 取消订阅后自动移除，节省资源
- ✅ 支持手动触发全量/增量同步

### 2. 低 Token 消耗的统计查询

- ✅ 使用 PostgreSQL 数仓，Token 消耗降低 97%
- ✅ 首次查询自动同步最新数据
- ✅ 后续查询直接从数仓读取

### 3. 基于 Journals 的精确分析

- ✅ `analyze_dev_tester_workload` 基于完整的变更历史
- ✅ 精确定位开发人员和测试人员
- ✅ 识别协作模式和自解自测情况

### 4. 定时同步调度器

- ✅ 每 10 分钟自动增量同步
- ✅ 每天自动全量同步
- ✅ 后台运行，不阻塞 MCP 工具调用

---

## 📈 数据统计

### 同步性能

| 指标 | 数值 |
|------|------|
| 增量同步间隔 | 10 分钟 |
| 增量时间窗口 | 13 分钟（含 3 分钟缓冲） |
| 单项目同步速度 | ~1-2 秒/项目（增量） |
| 全量同步速度 | ~30-60 秒/13 项目 |
| API 调用优化 | 分页获取，100 条/页 |

### 数仓规模（示例）

| 项目 | Issue 数 | 快照记录 |
|------|----------|----------|
| 341 (江苏新顺 CIM) | ~200 | ~6,000/月 |
| 357 (新顺 PMS) | ~50 | ~1,500/月 |
| 372 (上海工研院 MES) | ~100 | ~3,000/月 |

---

## 🔧 配置说明

### 环境变量

```bash
# Redmine 配置
REDMINE_URL=http://redmine.fa-software.com
REDMINE_API_KEY=your_api_key

# 数仓配置
WAREHOUSE_SYNC_ENABLED=true
WAREHOUSE_SYNC_INTERVAL_MINUTES=10
WAREHOUSE_DB_HOST=warehouse-db
WAREHOUSE_DB_PORT=5432
WAREHOUSE_DB_NAME=redmine_warehouse
WAREHOUSE_DB_USER=redmine_warehouse
WAREHOUSE_DB_PASSWORD=your_password

# 同步限制
MAX_ISSUES_PER_SYNC=500
SYNC_BATCH_SIZE=100
```

### Docker 容器

```bash
# MCP 服务器
docker-compose up -d redmine-mcp-server

# PostgreSQL 数仓
docker-compose up -d redmine-mcp-warehouse-db
```

---

## 📚 相关文档

### 功能文档

- [`docs/feature/01-subscription-feature.md`](./feature/01-subscription-feature.md) - 订阅功能
- [`docs/feature/02-data-sync.md`](./feature/02-data-sync.md) - 数据同步
- [`docs/feature/03-dev-test-analyzer.md`](./feature/03-dev-test-analyzer.md) - 开发/测试分析

### 技术文档

- [`docs/WAREHOUSE_SYNC.md`](./WAREHOUSE_SYNC.md) - 数仓同步机制
- [`docs/MCP_WAREHOUSE_SUMMARY.md`](./MCP_WAREHOUSE_SUMMARY.md) - 架构总结
- [`docs/WAREHOUSE_CONTRIBUTOR_EXTENSION.md`](./WAREHOUSE_CONTRIBUTOR_EXTENSION.md) - 贡献者扩展方案

---

## 🚀 后续扩展建议

### 短期（1-2 周）

1. **Issue 贡献者分析** - 扩展 `analyze_dev_tester_workload` 支持更多角色
2. **项目角色分布** - 统计项目中各角色的人员分布
3. **用户工作量统计** - 按用户统计跨项目工作量

### 中期（1 个月）

1. **Issue 质量报表** - 重开次数、平均解决时间
2. **团队负载分析** - 识别超负载/低负载人员
3. **趋势分析** - 按周/月统计工作量趋势

### 长期（3 个月）

1. **预测分析** - 基于历史数据预测项目风险
2. **自动化报告** - 定期生成并发送报告
3. **可视化 Dashboard** - Grafana 集成

---

## ✅ 验收清单

### 核心功能

- [x] Issue 数据同步到数仓
- [x] 项目每日统计
- [x] 开发/测试工作量分析
- [x] 订阅管理
- [x] 定时同步调度

### 待扩展

- [ ] Issue 贡献者分析（按角色分类）
- [ ] 项目角色分布统计
- [ ] 用户工作量跨项目统计
- [ ] Issue 质量报表
- [ ] 团队负载分析

---

**维护者**: OpenJaw <openjaw@gmail.com>  
**项目**: `/docker/redmine-mcp-server/`
