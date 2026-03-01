# Init-Scripts 规范文档

**版本**: 2.0  
**日期**: 2026-02-28  
**维护者**: OpenJaw

---

## 📁 文件结构

```
init-scripts/
├── v0.10.0__init_schema.sql       # 初始表结构
├── v0.10.0__init_data.sql         # 初始数据/函数/视图
├── v0.11.0__add_feature.sql       # 增量变更
├── README.md                      # 本说明文档
└── templates/                     # 模板文件（参考用）
    ├── schema.template.sql
    └── data.template.sql
```

---

## 📝 命名规范

### 格式

```
v{主版本}.{次版本}.{修订版本}__{简短描述}.sql

示例:
v0.10.0__init_schema.sql           # 初始表结构
v0.10.0__init_data.sql             # 初始数据
v0.11.0__add_user_preferences.sql  # 新增用户偏好表
v0.12.0__alter_issue_add_fields.sql # 修改 Issue 表
```

### 规则

1. **版本号**: `v{主版本}.{次版本}.{修订版本}`
   - 主版本：重大变更（不兼容）
   - 次版本：功能新增（兼容）
   - 修订版本：修复问题

2. **分隔符**: `__` (双下划线)

3. **描述**: 小写，下划线分隔，简短描述

### 执行顺序

PostgreSQL 按**字母顺序**执行：

```
v0.10.0__init_schema.sql      → 第 1 个执行（表结构）
v0.10.0__init_data.sql        → 第 2 个执行（数据/函数/视图）
v0.11.0__add_feature.sql      → 第 3 个执行（增量变更）
```

---

## 📄 文件模板

### v{version}__init_schema.sql

```sql
-- =====================================================
-- Version: v{version}
-- Type: SCHEMA
-- Date: {date}
-- Description: {description}
-- =====================================================

-- 1. 扩展和模式
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS warehouse;
SET search_path TO warehouse, public;

-- 2. 表定义（按层级）
-- DWD Layer
CREATE TABLE IF NOT EXISTS warehouse.table_name (...);

-- DWS Layer
CREATE TABLE IF NOT EXISTS warehouse.table_name (...);

-- ODS Layer
CREATE TABLE IF NOT EXISTS warehouse.table_name (...);

-- DIM Layer
CREATE TABLE IF NOT EXISTS warehouse.table_name (...);

-- ADS Layer
CREATE TABLE IF NOT EXISTS warehouse.table_name (...);

-- 3. 索引
CREATE INDEX IF NOT EXISTS idx_table_column ON warehouse.table_name(column);

-- 4. 授权
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;

-- 5. 注释
COMMENT ON SCHEMA warehouse IS 'Redmine MCP 数据仓库模式';
COMMENT ON TABLE warehouse.table_name IS '表说明';
```

### v{version}__init_data.sql

```sql
-- =====================================================
-- Version: v{version}
-- Type: DATA
-- Date: {date}
-- Description: {description}
-- =====================================================

SET timezone = 'Asia/Shanghai';
SET search_path TO warehouse, public;

-- 1. 基础数据
INSERT INTO warehouse.dim_role_category (...) VALUES ...;

-- 2. 存储函数
CREATE OR REPLACE FUNCTION warehouse.function_name(...)
RETURNS ... AS $$
BEGIN
    -- 逻辑
END;
$$ LANGUAGE plpgsql;

-- 3. 视图
CREATE OR REPLACE VIEW warehouse.view_name AS
SELECT ... FROM warehouse.table_name;

-- 4. 最终授权
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA warehouse TO redmine_warehouse;
```

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
# 执行单个脚本
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -f /docker-entrypoint-initdb.d/v0.10.0__init_schema.sql
```

### 验证安装

```bash
# 检查表数量
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'warehouse';"

# 检查函数数量
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'warehouse';"

# 检查视图数量
docker compose exec warehouse-db psql \
  -U redmine_warehouse \
  -d redmine_warehouse \
  -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'warehouse';"
```

---

## 🔧 开发流程

### 新增功能

1. **创建新版本脚本**:
   ```bash
   # 确定版本号
   # 功能新增：次版本 +1 (v0.10.0 → v0.11.0)
   # 修复问题：修订版本 +1 (v0.10.0 → v0.10.1)
   
   cd init-scripts
   cp templates/schema.template.sql v0.11.0__add_user_preferences.sql
   ```

2. **编辑脚本**:
   - 更新版本号
   - 更新描述
   - 添加表/函数/视图定义

3. **测试**:
   ```bash
   # 在测试数据库执行
   docker compose exec warehouse-db psql \
     -U redmine_warehouse \
     -d redmine_warehouse_test \
     -f /docker-entrypoint-initdb.d/v0.11.0__add_user_preferences.sql
   ```

4. **提交 Git**:
   ```bash
   git add init-scripts/v0.11.0__add_user_preferences.sql
   git commit -m "feat(db): add user preferences table (v0.11.0)"
   git push
   ```

---

## 📊 版本管理示例

### v0.10.0 - 初始版本

```
v0.10.0__init_schema.sql    # 所有表结构
v0.10.0__init_data.sql      # 所有函数/视图/数据
```

### v0.11.0 - 新增用户偏好

```
v0.11.0__add_user_preferences.sql
```

内容:
```sql
-- =====================================================
-- Version: v0.11.0
-- Type: SCHEMA
-- Date: 2026-02-28
-- Description: Add user preferences table
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.user_preferences (
    user_id INTEGER PRIMARY KEY,
    preference_key VARCHAR(100),
    preference_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user 
    ON warehouse.user_preferences(user_id);

COMMENT ON TABLE warehouse.user_preferences IS '用户偏好设置表';

GRANT ALL PRIVILEGES ON TABLE warehouse.user_preferences TO redmine_warehouse;
```

### v0.12.0 - 修改 Issue 表

```
v0.12.0__alter_issue_add_custom_fields.sql
```

---

## 📋 检查清单

### 新脚本检查

- [ ] 文件名符合规范 (`v{version}__{description}.sql`)
- [ ] 文件头完整（版本/类型/日期/描述）
- [ ] SQL 语法正确
- [ ] 包含授权语句
- [ ] 包含注释
- [ ] 无语法错误

### 测试验证

- [ ] 在测试环境执行成功
- [ ] 表/函数/视图创建成功
- [ ] 权限配置正确
- [ ] 不影响现有功能

### Git 提交

- [ ] 提交信息包含版本号
- [ ] 描述清晰
- [ ] 关联 Issue（如有）

---

## 🎯 最佳实践

### 版本号规则

| 变更类型 | 版本号变更 | 示例 |
|---------|-----------|------|
| 新功能 | 次版本 +1 | v0.10.0 → v0.11.0 |
| 修复 Bug | 修订版本 +1 | v0.10.0 → v0.10.1 |
| 重大变更 | 主版本 +1 | v0.x.x → v1.0.0 |

### 描述命名

**推荐**:
- `add_user_preferences` - 添加用户偏好
- `alter_issue_add_fields` - 修改 Issue 表添加字段
- `drop_old_table` - 删除旧表
- `migrate_user_data` - 迁移用户数据

**避免**:
- `update` - 太模糊
- `fix` - 不具体
- `new_feature` - 不清晰

### 文件组织

**大功能**: 单独文件
```
v0.11.0__add_subscription_system.sql  # 完整的订阅系统
```

**小改动**: 可以合并
```
v0.11.0__add_indexes_for_performance.sql  # 多个索引优化
```

---

## 📚 相关文档

- [Database Schema Design](./docs/architecture/DATABASE_SCHEMA.md)
- [Data Warehouse Guide](./docs/guides/redmine-warehouse-guide.md)
- [Deployment Guide](./docs/DOCKER_DEPLOYMENT.md)

---

**最后更新**: 2026-02-28
