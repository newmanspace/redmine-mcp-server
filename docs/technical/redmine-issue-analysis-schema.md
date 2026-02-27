# Redmine Issue 分析表结构设计

## 一、Redmine 原始表结构

### 1. issues 表
```
id              - Issue ID
project_id      - 项目 ID
tracker_id      - 跟踪器 ID (需求/bug/任务等)
status_id       - 状态 ID
priority_id     - 优先级 ID
author_id       - 作者 ID
assigned_to_id  - 当前负责人 ID
subject         - 主题
description     - 描述
start_date      - 开始日期
due_date        - 截止日期
done_ratio      - 完成百分比
created_on      - 创建时间
updated_on      - 更新时间
```

### 2. journals 表 (Issue 变更日志)
```
id              - Journal ID
journalized_id  - 关联的 Issue ID
user_id         - 操作人 ID
notes           - 备注/说明
created_on      - 操作时间
```

### 3. journal_details 表 (变更明细)
```
id              - Detail ID
journal_id      - 关联的 Journal ID
property        - 属性类型 (attr/attachment/custom_field)
name            - 字段名 (status_id/assigned_to_id 等)
old_value       - 旧值
new_value       - 新值
```

### 4. memberships 表 (项目成员)
```
id              - Membership ID
project_id      - 项目 ID
user_id         - 用户 ID (或 group_id)
group_id        - 组 ID (可选)
```

### 5. member_roles 表 (成员角色)
```
id              - Role Assignment ID
membership_id   - 关联的 Membership ID
role_id         - 角色 ID
```

### 6. roles 表 (角色定义)
```
id    - 角色 ID
name  - 角色名称
```

### 7. users 表
```
id        - 用户 ID
login     - 登录名
firstname - 姓
lastname  - 名
mail      - 邮箱
status    - 状态
```

### 8. groups 表
```
id    - 组 ID
name  - 组名称
```

---

## 二、角色优先级定义

| 优先级 | 角色 ID | 角色名称 | 说明 |
|--------|---------|----------|------|
| 1 (最高) | 3 | 管理人员 | 项目经理、管理员 |
| 2 | 8 | 实施人员 | 实施顾问、部署人员 |
| 3 | 4 | 开发人员 | 开发工程师 |
| 4 | 7 | 测试人员 | 测试工程师 |
| 5 | 5 | 报告人员 | 报告查看者 |
| 6 (最低) | 6 | 查询人员 | 只读权限 |

---

## 三、分析结果表结构设计

### 表名：`issue_contributors`

存储每个 Issue 的贡献者分析结果。

```sql
CREATE TABLE issue_contributors (
    id                  SERIAL PRIMARY KEY,
    issue_id            INTEGER NOT NULL,        -- Issue ID
    project_id          INTEGER NOT NULL,        -- 项目 ID
    user_id             INTEGER NOT NULL,        -- 用户 ID
    user_name           VARCHAR(255),            -- 用户姓名
    highest_role_id     INTEGER,                 -- 在项目中的最高角色 ID
    highest_role_name   VARCHAR(100),            -- 最高角色名称
    role_category       VARCHAR(20),             -- 角色分类：manager/implementation/developer/tester/reporter/viewer
    journal_count       INTEGER DEFAULT 0,       -- 在 journals 中的操作次数
    first_contribution  TIMESTAMP,               -- 首次贡献时间
    last_contribution   TIMESTAMP,               -- 最后贡献时间
    contribution_types  JSONB,                   -- 贡献类型统计 {"status_change": 2, "note_added": 1, ...}
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(issue_id, user_id)
);

-- 索引
CREATE INDEX idx_issue_contributors_issue_id ON issue_contributors(issue_id);
CREATE INDEX idx_issue_contributors_project_id ON issue_contributors(project_id);
CREATE INDEX idx_issue_contributors_user_id ON issue_contributors(user_id);
CREATE INDEX idx_issue_contributors_role_category ON issue_contributors(role_category);
```

### 表名：`issue_contributor_summary`

每个 Issue 的汇总统计（按角色分类）。

```sql
CREATE TABLE issue_contributor_summary (
    id                  SERIAL PRIMARY KEY,
    issue_id            INTEGER NOT NULL,        -- Issue ID
    project_id          INTEGER NOT NULL,        -- 项目 ID
    manager_count       INTEGER DEFAULT 0,       -- 管理人员数量
    implementation_count INTEGER DEFAULT 0,      -- 实施人员数量
    developer_count     INTEGER DEFAULT 0,       -- 开发人员数量
    tester_count        INTEGER DEFAULT 0,       -- 测试人员数量
    other_count         INTEGER DEFAULT 0,       -- 其他人员数量
    total_contributors  INTEGER DEFAULT 0,       -- 总贡献者数
    last_analyzed       TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(issue_id)
);
```

### 表名：`project_role_cache`

缓存项目成员角色信息，避免重复查询。

```sql
CREATE TABLE project_role_cache (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    highest_role_id     INTEGER,                 -- 最高角色 ID
    highest_role_name   VARCHAR(100),            -- 最高角色名称
    role_category       VARCHAR(20),             -- 角色分类
    all_roles           JSONB,                   -- 所有角色列表
    cached_at           TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(project_id, user_id)
);

-- 索引
CREATE INDEX idx_project_role_cache_project_id ON project_role_cache(project_id);
CREATE INDEX idx_project_role_cache_user_id ON project_role_cache(user_id);
```

---

## 四、Function 设计

### `analyze_issue_contributors(issue_id, project_id)`

**输入:**
- `issue_id`: Issue ID
- `project_id`: 项目 ID

**输出:**
- 贡献者列表（按角色分类）
- 更新 `issue_contributors` 表
- 更新 `issue_contributor_summary` 表

**逻辑流程:**

```
1. 获取 Issue 的完整 journals 数据
   └─> GET /issues/{issue_id}.json?include=journals

2. 从 journals 中提取所有唯一的 user_id
   └─> 去重，得到贡献者列表

3. 获取项目 357 的 memberships 数据
   └─> GET /projects/{project_id}/memberships.json?limit=100

4. 对每个贡献者：
   a. 在 memberships 中查找该用户
   b. 获取该用户的所有 roles
   c. 按优先级确定最高角色
      - 管理人员 (3) > 实施人员 (8) > 开发人员 (4) > 测试人员 (7) > ...
   d. 映射到 role_category

5. 统计每个用户的 journal 操作：
   - 操作次数
   - 首次/最后贡献时间
   - 贡献类型 (status_change, note_added, assigned_to_change, etc.)

6. 写入/更新 issue_contributors 表
   └─> UPSERT (INSERT ... ON CONFLICT UPDATE)

7. 生成汇总统计，写入 issue_contributor_summary 表
```

### `get_user_highest_role(project_id, user_id)`

**输入:**
- `project_id`: 项目 ID
- `user_id`: 用户 ID

**输出:**
- `highest_role_id`: 最高角色 ID
- `highest_role_name`: 最高角色名称
- `role_category`: 角色分类

**逻辑:**
```
1. 检查 project_role_cache 是否有缓存
   └─> 有则返回缓存

2. 查询 memberships
   └─> GET /projects/{project_id}/memberships.json

3. 查找 user_id 匹配的 membership
   └─> 注意：用户可能通过 group 间接获得角色

4. 从 roles 列表中找出最高优先级角色

5. 缓存到 project_role_cache

6. 返回结果
```

### `refresh_project_role_cache(project_id)`

**输入:**
- `project_id`: 项目 ID

**功能:**
- 重新获取项目所有成员的角色信息
- 更新 project_role_cache 表

---

## 五、角色分类映射

```javascript
const ROLE_PRIORITY = {
    3: { category: 'manager',        priority: 1, name: '管理人员' },
    8: { category: 'implementation', priority: 2, name: '实施人员' },
    4: { category: 'developer',      priority: 3, name: '开发人员' },
    7: { category: 'tester',         priority: 4, name: '测试人员' },
    5: { category: 'reporter',       priority: 5, name: '报告人员' },
    6: { category: 'viewer',         priority: 6, name: '查询人员' }
};
```

---

## 六、API 调用示例

### 获取 Issue + Journals
```bash
GET /issues/76361.json?key={API_KEY}&include=journals,attachments,relations
```

### 获取项目 Memberships
```bash
GET /projects/357/memberships.json?key={API_KEY}&limit=100
```

### 获取用户详情（含 groups）
```bash
GET /users/1531.json?key={API_KEY}&include=groups,memberships
```

---

## 七、数据整合方案

### 方案 A: 本地数据库存储
- 在本地 PostgreSQL/SQLite 创建上述表
- 定期同步 Redmine 数据
- 优点：查询快，可自定义分析
- 缺点：需要维护数据同步

### 方案 B: 文件存储（JSON）
- 将分析结果存储为 JSON 文件
- 按项目/日期组织
- 优点：简单，无需数据库
- 缺点：查询效率低，不适合大数据量

### 方案 C: 内存缓存 + 按需查询
- 不持久化存储
- 每次分析时实时查询 Redmine API
- 使用内存缓存减少重复查询
- 优点：数据实时，无需维护
- 缺点：API 调用频繁，受网络影响

**推荐：方案 A + C 混合**
- 使用 `project_role_cache` 缓存角色信息（减少重复查询）
- `issue_contributors` 可选持久化或按需计算

---

## 八、后续扩展

1. **Issue 关系分析**: 通过 `relations` 分析父子任务、阻塞关系
2. **时间线分析**: 统计 Issue 在各状态的停留时间
3. **工作量统计**: 基于 `spent_hours` 和 journal 操作次数
4. **团队负载分析**: 按人员统计活跃 Issue 数量
