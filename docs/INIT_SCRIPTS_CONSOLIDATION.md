# Init Scripts 整合说明

**日期**: 2026-02-28  
**目的**: 简化数据库初始化脚本管理

---

## 📋 变更总结

### 原有问题
- 8 个分散的 SQL 文件
- 执行顺序难以管理
- 重复的表定义
- 维护困难

### 新的结构
整合为 **2 个完整的脚本**：

1. **`00-complete-schema.sql`** - 完整的数据库表结构
2. **`99-init-data.sql`** - 初始化数据和函数

---

## 📁 文件结构

### Before (8 个文件)
```
init-scripts/
├── 01-schema.sql                    # 旧的基础表
├── 03-contributor-analysis.sql      # 贡献者分析表
├── 04-ods-layer-tables.sql          # ODS 层表
├── 05-dim-layer-tables.sql          # DIM 层表
├── 06-ads-layer-tables.sql          # ADS 层表
├── 07-ads-user-subscriptions.sql    # 订阅表
├── 08-migrate-subscriptions-i18n.sql # 订阅表迁移
├── 99-rename-tables.sql             # 表重命名
└── init-scripts/                    # 子目录（冗余）
    ├── 01-schema.sql
    └── 02-tables.sql
```

### After (2 个文件)
```
init-scripts/
├── 00-complete-schema.sql    # ✨ 完整的表结构（34 个表）
└── 99-init-data.sql          # ✨ 初始化数据 + 函数 + 视图
```

---

## 📊 00-complete-schema.sql 内容

### 1. DWD Layer (明细数据层) - 7 个表
- `issue_daily_snapshot` - Issue 每日快照
- `project_daily_summary` - 项目每日汇总
- `issue_contributors` - Issue 贡献者明细
- `issue_contributor_summary` - Issue 贡献者汇总
- `user_project_role` - 用户项目角色
- `project_role_distribution` - 项目角色分布
- `user_workload` - 用户工作量

### 2. ODS Layer (原始数据层) - 11 个表
- `ods_projects` - 项目表
- `ods_issues` - Issue 表
- `ods_journals` - Journal 表
- `ods_journal_details` - Journal 明细表
- `ods_users` - 用户表
- `ods_groups` - 组表
- `ods_group_users` - 组成员关系表
- `ods_project_memberships` - 项目成员表
- `ods_project_member_roles` - 成员角色表
- `ods_roles` - 角色表
- `ods_trackers` - Tracker 表
- `ods_issue_statuses` - Issue 状态表

### 3. DIM Layer (维度表) - 5 个表
- `dim_role_category` - 角色分类维度
- `dim_date` - 日期维度 (2010-2030)
- `dim_project` - 项目维度
- `dim_user` - 用户维度
- `dim_issue` - Issue 维度

### 4. DWS Layer (汇总数据层) - 6 个表
- `dws_project_daily_summary` - 项目每日汇总
- `dws_issue_contributors` - Issue 贡献者明细
- `dws_issue_contributor_summary` - Issue 贡献者汇总
- `dwd_user_project_role` - 用户项目角色
- `dws_project_role_distribution` - 项目角色分布
- `dws_user_monthly_workload` - 用户月度工作量

### 5. ADS Layer (应用数据层) - 5 个表
- `ads_contributor_report` - 贡献者分析报表
- `ads_project_health_report` - 项目健康度报表
- `ads_user_workload_report` - 用户工作量报表
- `ads_team_performance_report` - 团队绩效报表
- `ads_user_subscriptions` - 用户订阅表 ⭐

### 6. Indexes (索引) - 30+ 个索引
- DWD 层索引 (9 个)
- ODS 层索引 (8 个)
- DWS 层索引 (7 个)
- ADS 层索引 (9 个)
- 订阅表专用索引 (9 个) ⭐

### 7. Grants & Comments
- 所有表的授权
- 所有表的注释
- 所有字段的注释

---

## 📊 99-init-data.sql 内容

### 1. 基础数据初始化
```sql
-- 角色分类基础数据
INSERT INTO warehouse.dim_role_category ...
VALUES
    (3, '管理人员', 'manager', 1, '项目经理、管理员'),
    (8, '实施人员', 'implementation', 2, '实施顾问、部署人员'),
    (4, '开发人员', 'developer', 3, '开发工程师'),
    (7, '测试人员', 'tester', 4, '测试工程师'),
    ...
```

### 2. 存储函数 (3 个)

#### refresh_dws_project_daily_summary
- 从 DWD 层汇总到 DWS 层
- 按项目和日期聚合
- 支持 ON CONFLICT UPDATE

#### refresh_dws_issue_contributor_summary
- 汇总 Issue 贡献者数据
- 按角色分类统计
- 支持 ON CONFLICT UPDATE

#### refresh_dws_project_role_distribution
- 统计项目角色分布
- 按角色分类计数
- 支持 ON CONFLICT UPDATE

### 3. 视图定义 (4 个)

#### mv_project_realtime_stats
- 项目实时统计
- 包含 Issue 总数、未关闭数、贡献者数等

#### v_contributor_ranking
- 贡献者排行榜
- 按 Issue 数和 Journal 数排名

#### v_project_health_latest
- 最新项目健康度
- 每个项目取最新记录

#### v_user_workload_monthly
- 用户工作量月度汇总
- 按年月和排名排序

### 4. 表注释
- `ads_user_subscriptions` 表的所有字段注释
- 订阅功能相关的完整说明

### 5. 最终授权
- 所有函数的授权
- 所有视图的授权

---

## 🚀 使用方法

### 全新安装

```bash
# 1. 停止现有容器
docker compose down

# 2. 删除现有数据卷（⚠️ 会丢失数据）
docker volume rm redmine-mcp-server_warehouse_db_data

# 3. 重新启动（自动执行初始化脚本）
docker compose up -d

# 4. 等待初始化完成（约 30 秒）
docker compose logs -f warehouse-db
```

### 手动执行

```bash
# 执行完整 Schema
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/00-complete-schema.sql

# 执行初始化数据
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/99-init-data.sql
```

### 验证安装

```bash
# 检查表数量
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'warehouse';"

# 应该返回 34 个表
```

---

## 📝 迁移指南

### 从旧版本迁移

如果您已有旧版本的数据库：

```bash
# 1. 备份现有数据
docker compose exec warehouse-db pg_dump \
  -U redmine_warehouse \
  -d redmine_warehouse \
  > backup_$(date +%Y%m%d).sql

# 2. 执行新的 Schema（会创建所有新表）
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/00-complete-schema.sql

# 3. 执行初始化数据
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/99-init-data.sql

# 4. 验证表结构
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -c "\d warehouse.ads_user_subscriptions"
```

---

## 🎯 优势总结

### 维护性
- ✅ 单一 Schema 文件，易于版本控制
- ✅ 单一数据文件，易于测试
- ✅ 清晰的执行顺序（00- → 99-）

### 可读性
- ✅ 完整的注释
- ✅ 分层的结构
- ✅ 统一的格式

### 可靠性
- ✅ CREATE TABLE IF NOT EXISTS
- ✅ 所有表都有主键
- ✅ 所有表都有注释
- ✅ 完整的索引定义

### 扩展性
- ✅ 易于添加新表
- ✅ 易于修改现有表
- ✅ 支持增量迁移

---

## 📚 相关文档

- [Database Schema Design](./docs/architecture/DATABASE_SCHEMA.md)
- [Data Warehouse Guide](./docs/guides/redmine-warehouse-guide.md)
- [Subscription Feature](./docs/feature/04-subscription-database-migration.md)

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-28
