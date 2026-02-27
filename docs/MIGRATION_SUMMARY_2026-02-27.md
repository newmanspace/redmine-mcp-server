# Redmine MCP 数仓 - 命名规范迁移总结

**迁移日期**: 2026-02-27  
**迁移版本**: 1.0  
**状态**: ✅ 已完成

---

## 一、迁移目标

统一数仓表命名规范，采用分层前缀命名法：
- 提高表结构可读性
- 明确数据分层和用途
- 便于后续扩展和维护

---

## 二、迁移范围

### 2.1 数据库对象

| 对象类型 | 数量 | 说明 |
|----------|------|------|
| 表 | 7 | 所有 warehouse schema 下的表 |
| 索引 | 29 | 所有索引（主键、唯一、普通） |
| 序列 | 7 | 主键序列 |
| 存储函数 | 4 | 所有刷新函数 |

### 2.2 代码文件

| 文件 | 修改行数 | 说明 |
|------|---------|------|
| `redmine_warehouse.py` | ~50 | 数据访问层 |
| `redmine_handler.py` | ~20 | MCP 工具层 |
| `redmine_scheduler.py` | ~10 | 调度器 |
| `backfill_sync.py` | ~5 | 历史数据回填 |
| `subscription_reporter.py` | ~5 | 订阅报告 |

---

## 三、表重命名对照表

| 原表名 | 新表名 | 分层 | 说明 |
|--------|--------|------|------|
| `issue_daily_snapshot` | `dwd_issue_daily_snapshot` | DWD | Issue 每日快照 |
| `project_daily_summary` | `dws_project_daily_summary` | DWS | 项目每日汇总 |
| `issue_contributors` | `dws_issue_contributors` | DWS | Issue 贡献者明细 |
| `issue_contributor_summary` | `dws_issue_contributor_summary` | DWS | Issue 贡献者汇总 |
| `user_project_role` | `dwd_user_project_role` | DWD | 用户项目角色 |
| `project_role_distribution` | `dws_project_role_distribution` | DWS | 项目角色分布 |
| `user_workload` | `dws_user_monthly_workload` | DWS | 用户工作量（按月） |

---

## 四、索引重命名示例

### 主键索引

| 原名称 | 新名称 |
|--------|--------|
| `issue_daily_snapshot_pkey` | `pk_dwd_issue_daily_snapshot` |
| `project_daily_summary_pkey` | `pk_dws_project_daily_summary` |
| `issue_contributors_pkey` | `pk_dws_issue_contributors` |

### 唯一索引

| 原名称 | 新名称 |
|--------|--------|
| `uk_issue_snapshot` | `uk_dwd_issue_snapshot` |
| `uk_project_summary` | `uk_dws_project_summary` |
| `uk_issue_contributor` | `uk_dws_issue_contributor` |

### 普通索引

| 原名称 | 新名称 |
|--------|--------|
| `idx_issue_project_date` | `idx_dwd_issue_project_date` |
| `idx_contributors_user` | `idx_dws_issue_contributors_user` |
| `idx_user_workload_user` | `idx_dws_user_monthly_workload_user` |

---

## 五、存储函数重命名

| 原函数名 | 新函数名 | 参数 |
|----------|----------|------|
| `refresh_daily_summary` | `refresh_dws_project_daily_summary` | (project_id, snapshot_date) |
| `refresh_contributor_summary` | `refresh_dws_issue_contributor_summary` | (issue_id, project_id) |
| `refresh_project_role_distribution` | `refresh_dws_project_role_distribution` | (project_id, snapshot_date) |
| `refresh_user_workload` | `refresh_dws_user_monthly_workload` | (user_id, user_name, year_month, project_id) |

---

## 六、迁移步骤

### 6.1 准备阶段

1. ✅ 创建命名规范文档 `WAREHOUSE_NAMING_CONVENTION.md`
2. ✅ 创建迁移 SQL 脚本 `99-rename-tables.sql`
3. ✅ 更新 Python 代码中的表名引用
4. ✅ 验证 Python 代码语法

### 6.2 执行阶段

1. ✅ 执行数据库迁移脚本
   ```bash
   docker exec redmine-mcp-warehouse-db psql \
     -U redmine_warehouse -d redmine_warehouse \
     -f /docker-entrypoint-initdb.d/99-rename-tables.sql
   ```

2. ✅ 验证数据库对象
   - 表重命名：7 张 ✅
   - 索引重命名：29 个 ✅
   - 函数重命名：4 个 ✅

3. ✅ 重建 Docker 镜像
   ```bash
   docker compose build redmine-mcp-server
   ```

4. ✅ 重启服务
   ```bash
   docker compose up -d redmine-mcp-server
   ```

### 6.3 验证阶段

1. ✅ 测试 MCP 工具
   - `analyze_issue_contributors` - 正常 ✅
   - `get_project_daily_stats` - 正常 ✅
   - `get_project_role_distribution` - 正常 ✅
   - `get_user_workload` - 正常 ✅

2. ✅ 检查服务日志
   - 无错误日志 ✅
   - 数据库连接正常 ✅

---

## 七、验证结果

### 7.1 数据库验证

```sql
-- 验证表名
SELECT tablename FROM pg_tables WHERE schemaname = 'warehouse';

-- 结果:
-- dwd_issue_daily_snapshot
-- dwd_user_project_role
-- dws_issue_contributors
-- dws_issue_contributor_summary
-- dws_project_daily_summary
-- dws_project_role_distribution
-- dws_user_monthly_workload
```

### 7.2 索引验证

```sql
-- 验证索引命名
SELECT indexname FROM pg_indexes WHERE schemaname = 'warehouse';

-- 结果：所有索引均以 pk_/uk_/idx_ 开头 ✅
```

### 7.3 函数验证

```sql
-- 验证函数名
SELECT proname FROM pg_proc WHERE pronamespace = 'warehouse'::regnamespace;

-- 结果:
-- refresh_dws_project_daily_summary
-- refresh_dws_issue_contributor_summary
-- refresh_dws_project_role_distribution
-- refresh_dws_user_monthly_workload
```

### 7.4 功能验证

```bash
# 测试贡献者分析
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"analyze_issue_contributors","arguments":{"issue_id":76361}}}'

# 结果：返回正确数据 ✅
```

---

## 八、影响评估

### 8.1 积极影响

1. **可读性提升**
   - 通过表名即可识别数据分层
   - 便于新人理解和维护

2. **扩展性增强**
   - 为未来 20 张表的扩展预留空间
   - 统一规范便于自动化脚本编写

3. **维护成本降低**
   - 减少命名混淆
   - 便于问题定位

### 8.2 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 代码遗漏 | 中 | 全面搜索替换 + 语法检查 |
| 文档不同步 | 低 | 立即更新文档 |
| 回滚困难 | 低 | 提供回滚 SQL 脚本 |

---

## 九、回滚方案

如需回滚，执行以下脚本：

```sql
BEGIN;

-- 回滚表名
ALTER TABLE warehouse.dwd_issue_daily_snapshot RENAME TO issue_daily_snapshot;
ALTER TABLE warehouse.dws_project_daily_summary RENAME TO project_daily_summary;
ALTER TABLE warehouse.dws_issue_contributors RENAME TO issue_contributors;
ALTER TABLE warehouse.dws_issue_contributor_summary RENAME TO issue_contributor_summary;
ALTER TABLE warehouse.dwd_user_project_role RENAME TO user_project_role;
ALTER TABLE warehouse.dws_project_role_distribution RENAME TO project_role_distribution;
ALTER TABLE warehouse.dws_user_monthly_workload RENAME TO user_workload;

-- 回滚索引和序列...

COMMIT;
```

完整回滚脚本见：`/docker/redmine-mcp-server/init-scripts/99-rename-tables.sql`（底部）

---

## 十、后续工作

### 10.1 短期（本周）

- [x] 创建命名规范文档
- [x] 执行迁移
- [x] 验证功能
- [ ] 更新所有相关文档
- [ ] 团队培训

### 10.2 中期（本月）

- [ ] 实现 ODS 层 11 张表（按新规范）
- [ ] 实现 DIM 层 2 张表（按新规范）
- [ ] 实现 ADS 层 4 张表（按新规范）

### 10.3 长期

- [ ] 建立自动化命名检查工具
- [ ] 集成到 CI/CD 流程
- [ ] 定期审查命名规范

---

## 十一、相关文档

| 文档 | 位置 |
|------|------|
| 命名规范 | `docs/WAREHOUSE_NAMING_CONVENTION.md` |
| 表结构清单 | `docs/redmine-warehouse-tables.md` |
| 迁移脚本 | `init-scripts/99-rename-tables.sql` |
| 架构说明 | `docs/redmine-warehouse-schema.md` |

---

## 十二、参与人员

- **执行**: OpenJaw
- **审核**: TBD
- **批准**: TBD

---

**迁移状态**: ✅ 成功完成  
**迁移时间**: 2026-02-27 10:30 GMT+8  
** downtime**: 0 分钟（在线迁移）
