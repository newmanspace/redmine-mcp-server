# Redmine 数据仓库表结构设计

## 一、数仓分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                         应用层 (ADS)                         │
│  - 项目状态报表  - 人员负载分析  - Issue 趋势分析  - 质量报表   │
├─────────────────────────────────────────────────────────────┤
│                         汇总层 (DWS)                         │
│  - 项目统计  - 人员统计  - Issue 统计  - 贡献者分析汇总        │
├─────────────────────────────────────────────────────────────┤
│                         明细层 (DWD)                         │
│  - Issue 明细  - Journal 明细  - 成员角色明细  - 贡献者分析    │
├─────────────────────────────────────────────────────────────┤
│                         原始层 (ODS)                         │
│  - projects  - users  - issues  - journals  - memberships   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、原始层 (ODS) - 原始数据同步

### `ods_projects` - 项目表
```sql
CREATE TABLE ods_projects (
    project_id          INTEGER PRIMARY KEY,
    name                VARCHAR(255),
    identifier          VARCHAR(100),
    description         TEXT,
    status              INTEGER,                    -- 1:激活, 5:关闭
    created_on          TIMESTAMP,
    updated_on          TIMESTAMP,
    parent_project_id   INTEGER,
    sync_time           TIMESTAMP DEFAULT NOW()
);
```

### `ods_users` - 用户表
```sql
CREATE TABLE ods_users (
    user_id             INTEGER PRIMARY KEY,
    login               VARCHAR(100),
    firstname           VARCHAR(100),
    lastname            VARCHAR(100),
    mail                VARCHAR(255),
    status              INTEGER,                    -- 1:激活, 0:锁定
    created_on          TIMESTAMP,
    last_login_on       TIMESTAMP,
    sync_time           TIMESTAMP DEFAULT NOW()
);
```

### `ods_groups` - 组表
```sql
CREATE TABLE ods_groups (
    group_id            INTEGER PRIMARY KEY,
    name                VARCHAR(255),
    sync_time           TIMESTAMP DEFAULT NOW()
);
```

### `ods_group_users` - 组成员关系
```sql
CREATE TABLE ods_group_users (
    group_id            INTEGER,
    user_id             INTEGER,
    sync_time           TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
);
```

### `ods_issues` - Issue 表
```sql
CREATE TABLE ods_issues (
    issue_id            INTEGER PRIMARY KEY,
    project_id          INTEGER,
    tracker_id          INTEGER,
    status_id           INTEGER,
    priority_id         INTEGER,
    author_id           INTEGER,
    assigned_to_id      INTEGER,
    parent_issue_id     INTEGER,
    subject             VARCHAR(500),
    description         TEXT,
    start_date          DATE,
    due_date            DATE,
    done_ratio          INTEGER,                  -- 完成百分比
    estimated_hours     DECIMAL(10,2),
    spent_hours         DECIMAL(10,2),
    created_on          TIMESTAMP,
    updated_on          TIMESTAMP,
    closed_on           TIMESTAMP,
    sync_time           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ods_issues_project ON ods_issues(project_id);
CREATE INDEX idx_ods_issues_status ON ods_issues(status_id);
CREATE INDEX idx_ods_issues_assigned ON ods_issues(assigned_to_id);
CREATE INDEX idx_ods_issues_created ON ods_issues(created_on);
```

### `ods_journals` - Issue 变更日志
```sql
CREATE TABLE ods_journals (
    journal_id          INTEGER PRIMARY KEY,
    issue_id            INTEGER,
    user_id             INTEGER,
    notes               TEXT,
    created_on          TIMESTAMP,
    sync_time           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ods_journals_issue ON ods_journals(issue_id);
CREATE INDEX idx_ods_journals_user ON ods_journals(user_id);
```

### `ods_journal_details` - Journal 变更明细
```sql
CREATE TABLE ods_journal_details (
    detail_id           INTEGER PRIMARY KEY,
    journal_id          INTEGER,
    property            VARCHAR(50),              -- attr/attachment/custom_field
    name                VARCHAR(100),             -- status_id/assigned_to_id 等
    old_value           TEXT,
    new_value           TEXT,
    sync_time           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ods_journal_details_journal ON ods_journal_details(journal_id);
```

### `ods_project_memberships` - 项目成员
```sql
CREATE TABLE ods_memberships (
    membership_id       INTEGER PRIMARY KEY,
    project_id          INTEGER,
    user_id             INTEGER,                  -- 直接用户成员
    group_id            INTEGER,                  -- 组成员（通过组获得角色）
    sync_time           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ods_memberships_project ON ods_memberships(project_id);
CREATE INDEX idx_ods_memberships_user ON ods_memberships(user_id);
```

### `ods_project_member_roles` - 成员角色
```sql
CREATE TABLE ods_member_roles (
    membership_id       INTEGER,
    role_id             INTEGER,
    sync_time           TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (membership_id, role_id)
);
```

### `ods_roles` - 角色定义
```sql
CREATE TABLE ods_roles (
    role_id             INTEGER PRIMARY KEY,
    name                VARCHAR(100),
    sync_time           TIMESTAMP DEFAULT NOW()
);

-- 预置角色数据
-- 3:管理人员, 8:实施人员, 4:开发人员, 7:测试人员, 5:报告人员, 6:查询人员
```

### `ods_trackers` - 跟踪器类型
```sql
CREATE TABLE ods_trackers (
    tracker_id          INTEGER PRIMARY KEY,
    name                VARCHAR(100),             -- 需求/bug/任务等
    sync_time           TIMESTAMP DEFAULT NOW()
);
```

### `ods_issue_statuses` - Issue 状态
```sql
CREATE TABLE ods_issue_statuses (
    status_id           INTEGER PRIMARY KEY,
    name                VARCHAR(100),             -- 新建/进行中/已解决等
    is_closed           BOOLEAN DEFAULT FALSE,
    sync_time           TIMESTAMP DEFAULT NOW()
);
```

---

## 三、明细层 (DWD) - 清洗后的明细数据

### `dwd_issues_full` - Issue 完整明细
```sql
CREATE TABLE dwd_issues_full (
    issue_id            INTEGER PRIMARY KEY,
    project_id          INTEGER,
    project_name        VARCHAR(255),
    tracker_id          INTEGER,
    tracker_name        VARCHAR(100),
    status_id           INTEGER,
    status_name         VARCHAR(100),
    is_closed           BOOLEAN,
    priority_id         INTEGER,
    priority_name       VARCHAR(100),
    author_id           INTEGER,
    author_name         VARCHAR(200),
    assigned_to_id      INTEGER,
    assigned_to_name    VARCHAR(200),
    subject             VARCHAR(500),
    start_date          DATE,
    due_date            DATE,
    done_ratio          INTEGER,
    estimated_hours     DECIMAL(10,2),
    spent_hours         DECIMAL(10,2),
    created_date        DATE,                     -- 按日期分区
    created_on          TIMESTAMP,
    updated_on          TIMESTAMP,
    closed_on           TIMESTAMP,
    duration_days       INTEGER,                  -- 从创建到关闭的天数
    etl_time            TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dwd_issues_project ON dwd_issues_full(project_id);
CREATE INDEX idx_dwd_issues_status ON dwd_issues_full(status_id);
CREATE INDEX idx_dwd_issues_created_date ON dwd_issues_full(created_date);
CREATE INDEX idx_dwd_issues_assigned ON dwd_issues_full(assigned_to_id);
```

### `dwd_journal_summary` - Journal 汇总明细
```sql
CREATE TABLE dwd_journal_summary (
    issue_id            INTEGER,
    user_id             INTEGER,
    user_name           VARCHAR(200),
    journal_count       INTEGER,                  -- 操作次数
    first_journal       TIMESTAMP,                -- 首次操作时间
    last_journal        TIMESTAMP,                -- 最后操作时间
    status_change_count INTEGER,                  -- 状态变更次数
    assigned_change_count INTEGER,                -- 分配变更次数
    note_count          INTEGER,                  -- 添加备注次数
    attachment_count    INTEGER,                  -- 附件上传次数
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (issue_id, user_id)
);
```

### `dwd_user_project_role` - 用户在项目中的角色
```sql
CREATE TABLE dwd_user_project_role (
    project_id          INTEGER,
    user_id             INTEGER,
    highest_role_id     INTEGER,                  -- 最高角色 ID
    highest_role_name   VARCHAR(100),             -- 最高角色名称
    role_category       VARCHAR(20),              -- manager/implementation/developer/tester/other
    role_priority       INTEGER,                  -- 优先级 (1 最高)
    all_role_ids        VARCHAR(200),             -- 所有角色 ID 列表，逗号分隔
    is_direct_member    BOOLEAN,                  -- 是否直接成员 (vs 通过组)
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

CREATE INDEX idx_dwd_user_project_role_user ON dwd_user_project_role(user_id);
CREATE INDEX idx_dwd_user_project_role_category ON dwd_user_project_role(role_category);
```

### `dwd_issue_contributors` - Issue 贡献者分析
```sql
CREATE TABLE dwd_issue_contributors (
    issue_id            INTEGER,
    project_id          INTEGER,
    user_id             INTEGER,
    user_name           VARCHAR(200),
    highest_role_id     INTEGER,
    highest_role_name   VARCHAR(100),
    role_category       VARCHAR(20),
    journal_count       INTEGER,
    first_contribution  TIMESTAMP,
    last_contribution   TIMESTAMP,
    status_change_count INTEGER,
    note_count          INTEGER,
    assigned_change_count INTEGER,
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (issue_id, user_id)
);

CREATE INDEX idx_dwd_issue_contributors_issue ON dwd_issue_contributors(issue_id);
CREATE INDEX idx_dwd_issue_contributors_user ON dwd_issue_contributors(user_id);
CREATE INDEX idx_dwd_issue_contributors_category ON dwd_issue_contributors(role_category);
```

---

## 四、汇总层 (DWS) - 聚合统计信息

### `dws_project_daily_stats` - 项目每日统计
```sql
CREATE TABLE dws_project_daily_stats (
    project_id          INTEGER,
    stat_date           DATE,
    total_issues        INTEGER,                  -- 累计 Issue 总数
    new_issues          INTEGER,                  -- 当日新增
    closed_issues       INTEGER,                  -- 当日关闭
    open_issues         INTEGER,                  -- 当前未关闭
    in_progress_issues  INTEGER,                  -- 进行中
    total_spent_hours   DECIMAL(10,2),            -- 累计花费工时
    total_estimated_hours DECIMAL(10,2),          -- 累计预估工时
    avg_done_ratio      DECIMAL(5,2),             -- 平均完成度
    active_contributors INTEGER,                  -- 活跃贡献者数
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, stat_date)
);
```

### `dws_project_contributor_stats` - 项目贡献者统计
```sql
CREATE TABLE dws_project_contributor_stats (
    project_id          INTEGER,
    stat_date           DATE,
    user_id             INTEGER,
    user_name           VARCHAR(200),
    role_category       VARCHAR(20),
    total_issues        INTEGER,                  -- 参与 Issue 总数
    created_issues      INTEGER,                  -- 创建的 Issue
    assigned_issues     INTEGER,                  -- 被分配的 Issue
    closed_issues       INTEGER,                  -- 关闭的 Issue
    journal_count       INTEGER,                  -- 总操作次数
    spent_hours         DECIMAL(10,2),            -- 花费工时
    first_activity      DATE,                     -- 首次活动日期
    last_activity       DATE,                     -- 最后活动日期
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, stat_date, user_id)
);
```

### `dws_project_role_distribution` - 项目角色分布
```sql
CREATE TABLE dws_project_role_distribution (
    project_id          INTEGER,
    stat_date           DATE,
    manager_count       INTEGER,
    implementation_count INTEGER,
    developer_count     INTEGER,
    tester_count        INTEGER,
    other_count         INTEGER,
    total_members       INTEGER,
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, stat_date)
);
```

### `dws_issue_contributor_summary` - Issue 贡献者汇总
```sql
CREATE TABLE dws_issue_contributor_summary (
    issue_id            INTEGER PRIMARY KEY,
    project_id          INTEGER,
    manager_count       INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count     INTEGER DEFAULT 0,
    tester_count        INTEGER DEFAULT 0,
    other_count         INTEGER DEFAULT 0,
    total_contributors  INTEGER DEFAULT 0,
    total_journals      INTEGER DEFAULT 0,
    etl_time            TIMESTAMP DEFAULT NOW()
);
```

### `dws_user_monthly_workload` - 用户月度工作量
```sql
CREATE TABLE dws_user_monthly_workload (
    user_id             INTEGER,
    year_month          VARCHAR(7),               -- YYYY-MM
    total_issues        INTEGER,                  -- 参与 Issue 数
    created_issues      INTEGER,
    closed_issues       INTEGER,
    total_journals      INTEGER,                  -- 操作次数
    total_spent_hours   DECIMAL(10,2),
    projects_involved   INTEGER,                  -- 参与项目数
    as_manager          INTEGER,                  -- 作为管理人员的 Issue
    as_developer        INTEGER,                  -- 作为开发人员的 Issue
    as_implementation   INTEGER,                  -- 作为实施人员的 Issue
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, year_month)
);
```

### `dws_tracker_distribution` - Tracker 类型分布
```sql
CREATE TABLE dws_tracker_distribution (
    project_id          INTEGER,
    stat_date           DATE,
    tracker_id          INTEGER,
    tracker_name        VARCHAR(100),
    total_count         INTEGER,
    open_count          INTEGER,
    closed_count        INTEGER,
    avg_duration_days   DECIMAL(10,2),
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, stat_date, tracker_id)
);
```

---

## 五、应用层 (ADS) - 面向应用的报表

### `ads_project_status_report` - 项目状态报表
```sql
CREATE TABLE ads_project_status_report (
    project_id          INTEGER PRIMARY KEY,
    project_name        VARCHAR(255),
    status              VARCHAR(20),              -- 激活/关闭
    total_issues        INTEGER,
    open_issues         INTEGER,
    closed_issues       INTEGER,
    overdue_issues      INTEGER,                  -- 超期未关闭
    completion_rate     DECIMAL(5,2),             -- 完成率%
    total_members       INTEGER,
    active_members_30d  INTEGER,                  -- 近 30 天活跃成员
    total_spent_hours   DECIMAL(10,2),
    last_updated        DATE,
    report_date         DATE,
    etl_time            TIMESTAMP DEFAULT NOW()
);
```

### `ads_user_workload_ranking` - 用户工作量排名
```sql
CREATE TABLE ads_user_workload_ranking (
    stat_month        VARCHAR(7),                 -- YYYY-MM
    rank_type         VARCHAR(20),                -- by_issues/by_hours/by_journals
    user_id           INTEGER,
    user_name         VARCHAR(200),
    role_category     VARCHAR(20),
    metric_value      DECIMAL(10,2),
    rank_num          INTEGER,
    project_count     INTEGER,
    etl_time          TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (stat_month, rank_type, user_id)
);
```

### `ads_issue_quality_report` - Issue 质量报表
```sql
CREATE TABLE ads_issue_quality_report (
    project_id          INTEGER,
    stat_month        VARCHAR(7),
    total_issues        INTEGER,
    reopen_count        INTEGER,                  -- 重新打开次数
    avg_reopen_times    DECIMAL(5,2),             -- 平均重开次数
    avg_resolution_days DECIMAL(10,2),            -- 平均解决天数
    overdue_rate        DECIMAL(5,2),             -- 超期率%
    bug_ratio           DECIMAL(5,2),             -- Bug 占比%
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, stat_month)
);
```

### `ads_team_load_analysis` - 团队负载分析
```sql
CREATE TABLE ads_team_load_analysis (
    project_id          INTEGER,
    stat_date           DATE,
    role_category       VARCHAR(20),
    member_count        INTEGER,
    total_issues        INTEGER,
    avg_issues_per_person DECIMAL(5,2),
    total_spent_hours   DECIMAL(10,2),
    avg_hours_per_person DECIMAL(10,2),
    overload_count      INTEGER,                  -- 超负载人数
    underload_count     INTEGER,                  -- 低负载人数
    etl_time            TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, stat_date, role_category)
);
```

---

## 六、维度表

### `dim_date` - 日期维度
```sql
CREATE TABLE dim_date (
    date_key            INTEGER PRIMARY KEY,      -- YYYYMMDD
    full_date           DATE,
    year                INTEGER,
    month               INTEGER,
    day                 INTEGER,
    quarter             INTEGER,
    week_of_year        INTEGER,
    day_of_week         INTEGER,
    day_name            VARCHAR(20),
    month_name          VARCHAR(20),
    is_weekend          BOOLEAN,
    is_holiday          BOOLEAN
);
```

### `dim_role_category` - 角色分类维度
```sql
CREATE TABLE dim_role_category (
    role_id             INTEGER PRIMARY KEY,
    role_name           VARCHAR(100),
    category            VARCHAR(20),              -- manager/implementation/developer/tester/other
    priority            INTEGER,                  -- 1 最高
    description         VARCHAR(255)
);

-- 预置数据
INSERT INTO dim_role_category VALUES
(3, '管理人员', 'manager', 1, '项目经理、管理员'),
(8, '实施人员', 'implementation', 2, '实施顾问、部署人员'),
(4, '开发人员', 'developer', 3, '开发工程师'),
(7, '测试人员', 'tester', 4, '测试工程师'),
(5, '报告人员', 'reporter', 5, '报告查看者'),
(6, '查询人员', 'viewer', 6, '只读权限');
```

---

## 七、物化视图 (可选)

### `mv_project_realtime_stats` - 项目实时统计
```sql
CREATE MATERIALIZED VIEW mv_project_realtime_stats AS
SELECT 
    p.project_id,
    p.project_name,
    COUNT(DISTINCT i.issue_id) as total_issues,
    COUNT(DISTINCT CASE WHEN i.is_closed = FALSE THEN i.issue_id END) as open_issues,
    COUNT(DISTINCT CASE WHEN i.is_closed = TRUE THEN i.issue_id END) as closed_issues,
    SUM(i.spent_hours) as total_spent_hours,
    COUNT(DISTINCT ic.user_id) as total_contributors,
    MAX(i.updated_on) as last_activity
FROM ods_projects p
LEFT JOIN dwd_issues_full i ON p.project_id = i.project_id
LEFT JOIN dwd_issue_contributors ic ON i.issue_id = ic.issue_id
WHERE p.status = 1
GROUP BY p.project_id, p.project_name;

-- 刷新
REFRESH MATERIALIZED VIEW mv_project_realtime_stats;
```

---

## 八、数据同步流程

```
┌─────────────────────────────────────────────────────────────┐
│                     Redmine API                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ODS 层 - 原始数据同步                            │
│  sync_projects() → ods_projects                             │
│  sync_users() → ods_users                                   │
│  sync_issues() → ods_issues                                 │
│  sync_journals() → ods_journals                             │
│  sync_memberships() → ods_memberships                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              DWD 层 - 数据清洗转换                            │
│  build_issues_full() → dwd_issues_full                      │
│  build_user_project_role() → dwd_user_project_role          │
│  build_issue_contributors() → dwd_issue_contributors        │
│  build_journal_summary() → dwd_journal_summary              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              DWS 层 - 聚合统计                                │
│  agg_project_daily_stats() → dws_project_daily_stats        │
│  agg_project_contributor_stats() → dws_project_contributor_stats
│  agg_user_monthly_workload() → dws_user_monthly_workload    │
│  agg_issue_contributor_summary() → dws_issue_contributor_summary
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ADS 层 - 应用报表                                │
│  build_project_status_report() → ads_project_status_report  │
│  build_user_workload_ranking() → ads_user_workload_ranking  │
│  build_issue_quality_report() → ads_issue_quality_report    │
└─────────────────────────────────────────────────────────────┘
```

---

## 九、SQL 示例

### 查询 Issue 的贡献者分布
```sql
SELECT 
    i.issue_id,
    i.subject,
    SUM(CASE WHEN c.role_category = 'manager' THEN 1 ELSE 0 END) as managers,
    SUM(CASE WHEN c.role_category = 'implementation' THEN 1 ELSE 0 END) as implementations,
    SUM(CASE WHEN c.role_category = 'developer' THEN 1 ELSE 0 END) as developers,
    SUM(CASE WHEN c.role_category = 'tester' THEN 1 ELSE 0 END) as testers
FROM dwd_issues_full i
LEFT JOIN dwd_issue_contributors c ON i.issue_id = c.issue_id
WHERE i.project_id = 357
GROUP BY i.issue_id, i.subject;
```

### 查询开发人员的工作量排名
```sql
SELECT 
    u.user_name,
    COUNT(DISTINCT c.issue_id) as issues_involved,
    SUM(c.journal_count) as total_operations,
    SUM(i.spent_hours) as total_hours
FROM dwd_issue_contributors c
JOIN dwd_issues_full i ON c.issue_id = i.issue_id
JOIN ods_users u ON c.user_id = u.user_id
WHERE c.role_category = 'developer'
  AND i.project_id = 357
  AND i.created_date >= '2026-01-01'
GROUP BY u.user_id, u.user_name
ORDER BY issues_involved DESC
LIMIT 10;
```

### 查询项目角色分布
```sql
SELECT 
    role_category,
    COUNT(DISTINCT user_id) as member_count
FROM dwd_user_project_role
WHERE project_id = 357
GROUP BY role_category
ORDER BY 
    CASE role_category 
        WHEN 'manager' THEN 1 
        WHEN 'implementation' THEN 2 
        WHEN 'developer' THEN 3 
        WHEN 'tester' THEN 4 
        ELSE 5 
    END;
```
