# Redmine MCP 数仓 - 表命名规范

**版本**: 1.0  
**制定日期**: 2026-02-27  
**适用范围**: warehouse schema 下所有表

---

## 一、命名原则

### 1.1 分层前缀

所有表名必须包含分层前缀，体现数据流向和用途：

| 分层 | 前缀 | 说明 | 示例 |
|------|------|------|------|
| **ODS** | `ods_` | 原始数据层 (Operational Data Store) | `ods_issues` |
| **DWD** | `dwd_` | 明细数据层 (Data Warehouse Detail) | `dwd_issue_daily_snapshot` |
| **DWS** | `dws_` | 汇总数据层 (Data Warehouse Summary) | `dws_project_daily_summary` |
| **ADS** | `ads_` | 应用数据层 (Application Data Store) | `ads_contributor_report` |
| **DIM** | `dim_` | 维度表 (Dimension) | `dim_role_category` |

### 1.2 命名格式

```
{分层前缀}_{业务主体}_{内容描述}_{粒度/频率}
```

**规则**:
1. 全部使用**小写字母**
2. 单词间使用**下划线**分隔
3. 使用**复数形式**表示明细数据（记录多条）
4. 使用**单数形式**表示汇总/维度表（单条记录）
5. 避免缩写（除非是行业通用缩写如 ID、URL）

### 1.3 业务主体命名

| 业务对象 | 命名 | 示例 |
|----------|------|------|
| Issue | `issue` | `dwd_issues` |
| Project | `project` | `dws_project_daily` |
| User | `user` | `dwd_users` |
| Journal | `journal` | `ods_journals` |
| Role | `role` | `dim_roles` |
| Contributor | `contributor` | `dws_issue_contributors` |

### 1.4 内容描述命名

| 内容类型 | 命名 | 示例 |
|----------|------|------|
| 快照 | `snapshot` | `dwd_issue_daily_snapshot` |
| 汇总 | `summary` | `dws_project_daily_summary` |
| 统计 | `stats` | `dws_project_daily_stats` |
| 角色 | `role` | `dwd_user_project_role` |
| 分布 | `distribution` | `dws_project_role_distribution` |
| 工作量 | `workload` | `dws_user_monthly_workload` |

### 1.5 粒度/频率后缀

| 粒度 | 后缀 | 示例 |
|------|------|------|
| 每日 | `daily` | `dws_project_daily_summary` |
| 每周 | `weekly` | `dws_user_weekly_workload` |
| 每月 | `monthly` | `dws_user_monthly_workload` |
| 实时 | `realtime` | `ads_issue_realtime` |
| 全量 | `full` | `dwd_issues_full` |
| 增量 | `incr` | `dwd_issues_incr` |

---

## 二、现有表重命名映射

### 2.1 已实现表（7 张）

| 原表名 | 新表名 | 分层 | 说明 |
|--------|--------|------|------|
| `issue_daily_snapshot` | `dwd_issue_daily_snapshot` | DWD | Issue 每日快照 |
| `project_daily_summary` | `dws_project_daily_summary` | DWS | 项目每日汇总 |
| `issue_contributors` | `dws_issue_contributors` | DWS | Issue 贡献者明细 |
| `issue_contributor_summary` | `dws_issue_contributor_summary` | DWS | Issue 贡献者汇总 |
| `user_project_role` | `dwd_user_project_role` | DWD | 用户项目角色 |
| `project_role_distribution` | `dws_project_role_distribution` | DWS | 项目角色分布 |
| `user_workload` | `dws_user_monthly_workload` | DWS | 用户工作量（按月） |

### 2.2 规划表（20 张）

| 规划表名 | 标准命名 | 分层 |
|----------|----------|------|
| `ods_projects` | `ods_projects` | ODS |
| `ods_issues` | `ods_issues` | ODS |
| `ods_journals` | `ods_journals` | ODS |
| `ods_users` | `ods_users` | ODS |
| `ods_project_memberships` | `ods_project_memberships` | ODS |
| `dwd_issues_full` | `dwd_issues_full` | DWD |
| `dwd_issue_contributors` | `dws_issue_contributors` | DWS |
| `ads_contributor_report` | `ads_contributor_report` | ADS |
| `dim_role_category` | `dim_role_category` | DIM |
| `dim_date` | `dim_date` | DIM |

---

## 三、索引命名规范

### 3.1 命名格式

```
{类型}_{表名}_{字段名}
```

| 类型 | 前缀 | 示例 |
|------|------|------|
| 主键 | `pk_` | `pk_dwd_issue_daily_snapshot` |
| 外键 | `fk_` | `fk_dwd_issues_project_id` |
| 唯一索引 | `uk_` | `uk_dwd_issue_snapshot` |
| 普通索引 | `idx_` | `idx_dwd_issue_project_date` |

### 3.2 现有索引重命名

| 原索引名 | 新索引名 | 说明 |
|----------|----------|------|
| `issue_daily_snapshot_pkey` | `pk_dwd_issue_daily_snapshot` | 主键 |
| `uk_issue_snapshot` | `uk_dwd_issue_snapshot` | 唯一约束 |
| `idx_issue_project_date` | `idx_dwd_issue_project_date` | 普通索引 |
| `project_daily_summary_pkey` | `pk_dws_project_daily_summary` | 主键 |
| `uk_project_summary` | `uk_dws_project_summary` | 唯一约束 |
| `issue_contributors_pkey` | `pk_dws_issue_contributors` | 主键 |
| `uk_issue_contributor` | `uk_dws_issue_contributor` | 唯一约束 |

---

## 四、存储函数命名规范

### 4.1 命名格式

```
{动作}_{业务主体}_{内容}
```

| 动作 | 说明 | 示例 |
|------|------|------|
| `refresh_` | 刷新/重新计算 | `refresh_dws_project_daily_summary` |
| `insert_` | 插入 | `insert_dwd_issue_snapshot` |
| `update_` | 更新 | `update_dwd_issue_snapshot` |
| `delete_` | 删除 | `delete_dwd_issue_snapshot` |
| `merge_` | 合并（upsert） | `merge_dwd_issue_snapshot` |

### 4.2 现有函数重命名

| 原函数名 | 新函数名 | 说明 |
|----------|----------|------|
| `refresh_daily_summary` | `refresh_dws_project_daily_summary` | 刷新项目汇总 |
| `refresh_contributor_summary` | `refresh_dws_issue_contributor_summary` | 刷新贡献者汇总 |
| `refresh_project_role_distribution` | `refresh_dws_project_role_distribution` | 刷新角色分布 |
| `refresh_user_workload` | `refresh_dws_user_monthly_workload` | 刷新用户工作量 |

---

## 五、序列命名规范

### 5.1 命名格式

```
seq_{表名}_{字段名}
```

| 原序列名 | 新序列名 | 说明 |
|----------|----------|------|
| `issue_daily_snapshot_id_seq` | `seq_dwd_issue_daily_snapshot_id` | 主键序列 |
| `project_daily_summary_id_seq` | `seq_dws_project_daily_summary_id` | 主键序列 |
| `issue_contributors_id_seq` | `seq_dws_issue_contributors_id` | 主键序列 |

---

## 六、视图命名规范

### 6.1 命名格式

```
{分层前缀}_v_{业务主体}_{内容}
```

| 示例 | 说明 |
|------|------|
| `dws_v_project_contributor_stats` | 项目贡献者统计视图 |
| `ads_v_user_workload_report` | 用户工作量报表视图 |

---

## 七、实施步骤

### 7.1 迁移策略

采用**渐进式迁移**，避免影响现有业务：

1. **创建新表** - 使用新命名创建表结构
2. **数据迁移** - 将旧表数据复制到新表
3. **更新代码** - 修改 MCP 工具引用新表名
4. **并行运行** - 新旧表同时运行 1-2 周
5. **删除旧表** - 确认无误后删除旧表

### 7.2 迁移 SQL 示例

```sql
-- 1. 创建新表
ALTER TABLE warehouse.issue_daily_snapshot 
  RENAME TO dwd_issue_daily_snapshot;

-- 2. 重命名索引
ALTER INDEX warehouse.uk_issue_snapshot 
  RENAME TO uk_dwd_issue_snapshot;

-- 3. 重命名序列
ALTER SEQUENCE warehouse.issue_daily_snapshot_id_seq 
  RENAME TO seq_dwd_issue_daily_snapshot_id;

-- 4. 重命名函数
ALTER FUNCTION warehouse.refresh_daily_summary(INTEGER, DATE)
  RENAME TO refresh_dws_project_daily_summary;
```

### 7.3 完整迁移脚本

创建文件：`/docker/redmine-mcp-server/init-scripts/99-rename-tables.sql`

---

## 八、代码影响范围

### 8.1 需要更新的文件

| 文件 | 修改内容 |
|------|----------|
| `src/redmine_mcp_server/redmine_warehouse.py` | 表名、SQL 语句 |
| `src/redmine_mcp_server/redmine_handler.py` | MCP 工具中的 SQL |
| `src/redmine_mcp_server/redmine_scheduler.py` | 同步逻辑中的表名 |
| `init-scripts/*.sql` | DDL 语句 |

### 8.2 影响评估

| 工具名 | 影响表 | 修改量 |
|--------|--------|--------|
| `get_project_daily_stats` | `dws_project_daily_summary` | 小 |
| `analyze_issue_contributors` | `dws_issue_contributors` | 中 |
| `get_project_role_distribution` | `dws_project_role_distribution` | 小 |
| `get_user_workload` | `dws_user_monthly_workload` | 小 |
| `trigger_contributor_sync` | 多张表 | 中 |

---

## 九、最佳实践

### 9.1 命名检查清单

创建新表时检查：
- [ ] 是否包含分层前缀（ods_/dwd_/dws_/ads_/dim_）
- [ ] 是否全部小写
- [ ] 是否使用下划线分隔
- [ ] 是否使用复数形式（明细表）
- [ ] 是否避免缩写
- [ ] 是否体现粒度/频率

### 9.2 文档更新

每次新增/修改表时更新：
- [ ] `docs/redmine-warehouse-tables.md`
- [ ] `docs/redmine-warehouse-schema.md`
- [ ] `docs/WAREHOUSE_NAMING_CONVENTION.md`（如有变更）

### 9.3 代码审查

PR 审查时检查：
- [ ] 表命名是否符合规范
- [ ] 索引命名是否符合规范
- [ ] 函数命名是否符合规范
- [ ] 文档是否同步更新

---

## 十、例外情况

以下情况可申请例外：
1. **临时表** - 使用 `tmp_{purpose}` 前缀
2. **中间表** - 使用 `mid_{purpose}` 前缀
3. **备份表** - 使用 `{table_name}_bak_{date}` 后缀
4. **测试表** - 使用 `test_{table_name}` 前缀

例外需经团队讨论并在文档中说明。

---

**维护者**: OpenJaw <openjaw@gmail.com>  
**项目**: `/docker/redmine-mcp-server/`
