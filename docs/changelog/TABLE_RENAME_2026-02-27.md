# 表命名优化 - Memberships 重命名

**变更日期**: 2026-02-27 11:49 AM  
**变更原因**: 提高表名可读性和准确性

---

## 一、变更内容

### 1.1 表名变更

| 原表名 | 新表名 | 说明 |
|--------|--------|------|
| `ods_memberships` | `ods_project_memberships` | 项目成员关系表 |
| `ods_member_roles` | `ods_project_member_roles` | 项目成员角色分配表 |

### 1.2 索引变更

| 原索引名 | 新索引名 | 说明 |
|----------|----------|------|
| `idx_ods_memberships_project` | `idx_ods_project_memberships_project` | 项目 ID 索引 |
| `idx_ods_memberships_user` | `idx_ods_project_memberships_user` | 用户 ID 索引 |

---

## 二、变更原因

### 2.1 原命名问题

- ❌ `ods_memberships` - 含义模糊，可能是：
  - 项目成员？
  - 组成员？
  - 其他成员关系？

### 2.2 新命名优势

- ✅ `ods_project_memberships` - 清晰明确：
  - **project** - 明确是项目级别
  - **memberships** - 成员关系
  - 符合 ODS 层命名规范：`ods_{业务主体}_{内容}`

### 2.3 一致性

与现有命名风格保持一致：

```
ods_projects           - 项目表
ods_project_memberships - 项目成员表 ✅
ods_users              - 用户表
```

---

## 三、影响范围

### 3.1 已更新的文件

| 文件类型 | 文件数 | 状态 |
|----------|--------|------|
| SQL 脚本 | 1 | ✅ `init-scripts/04-ods-layer-tables.sql` |
| Python 脚本 | 1 | ✅ `scripts/sync_ods_complete.py` |
| 文档 | 10+ | ✅ 所有 Markdown 文档 |

### 3.2 代码引用

需要同步更新 Python 代码中的表名引用：

```python
# 更新前
cur.execute("SELECT * FROM warehouse.ods_memberships WHERE project_id = %s", (pid,))

# 更新后
cur.execute("SELECT * FROM warehouse.ods_project_memberships WHERE project_id = %s", (pid,))
```

---

## 四、执行步骤

### 4.1 数据库变更

```sql
-- 重命名表
ALTER TABLE warehouse.ods_memberships RENAME TO ods_project_memberships;
ALTER TABLE warehouse.ods_member_roles RENAME TO ods_project_member_roles;

-- 重命名索引
ALTER INDEX warehouse.idx_ods_memberships_project RENAME TO idx_ods_project_memberships_project;
ALTER INDEX warehouse.idx_ods_memberships_user RENAME TO idx_ods_project_memberships_user;

-- 更新注释
COMMENT ON TABLE warehouse.ods_project_memberships IS 'ODS-项目成员关系表';
COMMENT ON TABLE warehouse.ods_project_member_roles IS 'ODS-项目成员角色分配表';
```

### 4.2 脚本更新

```bash
# 更新 SQL 脚本
sed -i 's/ods_memberships/ods_project_memberships/g' init-scripts/04-ods-layer-tables.sql
sed -i 's/ods_member_roles/ods_project_member_roles/g' init-scripts/04-ods-layer-tables.sql

# 更新 Python 脚本
sed -i 's/ods_memberships/ods_project_memberships/g' scripts/sync_ods_complete.py
sed -i 's/ods_member_roles/ods_project_member_roles/g' scripts/sync_ods_complete.py
```

### 4.3 文档更新

```bash
# 更新所有文档
find docs -name "*.md" -exec sed -i 's/ods_memberships/ods_project_memberships/g' {} \;
find docs -name "*.md" -exec sed -i 's/ods_member_roles/ods_project_member_roles/g' {} \;
```

---

## 五、验证

### 5.1 验证表名

```sql
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'warehouse' 
  AND tablename LIKE 'ods_project%'
ORDER BY tablename;

-- 结果:
-- ods_project_memberships
-- ods_project_member_roles
-- ods_projects
```

### 5.2 验证数据

```sql
SELECT COUNT(*) FROM warehouse.ods_project_memberships;
SELECT COUNT(*) FROM warehouse.ods_project_member_roles;

-- 应保持原有数据量不变
```

---

## 六、后续注意事项

### 6.1 开发注意

在新代码中使用新表名：

```python
# ✅ 正确
"SELECT * FROM warehouse.ods_project_memberships"

# ❌ 错误（旧表名）
"SELECT * FROM warehouse.ods_memberships"
```

### 6.2 文档注意

所有新文档应使用新表名，并在首次提及时说明：

```markdown
### 项目成员表 (`ods_project_memberships`)

记录项目与成员的关联关系...
```

---

## 七、总结

### 7.1 变更收益

- ✅ **可读性提升** - 表名更清晰明确
- ✅ **一致性增强** - 符合命名规范
- ✅ **可扩展性** - 为未来 `ods_group_memberships` 预留空间

### 7.2 变更成本

- ✅ **低风险** - 仅重命名，不影响数据结构
- ✅ **已验证** - 所有引用已更新
- ✅ **向后兼容** - 无外部依赖

### 7.3 相关表

完整的 ODS 层表清单：

```
ods_projects              ✅
ods_project_memberships   ✅ (重命名后)
ods_project_member_roles  ✅ (重命名后)
ods_users                 ✅
ods_groups                ✅
ods_group_users           ✅
ods_issues                ✅
ods_journals              ✅
ods_journal_details       ✅
ods_roles                 ✅
ods_trackers              ✅
ods_issue_statuses        ✅
```

---

**维护者**: OpenJaw  
**变更日期**: 2026-02-27 11:49 AM  
**项目**: `/docker/redmine-mcp-server/`  
**状态**: ✅ 已完成
