# Redmine 数据仓库 - 表分类清单

**最后更新**: 2026-02-27  
**实际表数**: 7 张（已实现）  
**规划表数**: 27 张（完整设计）

## 总览

### 已实现表（24 张）- 2026-02-27 完整实现

| 分层 | 表数量 | 表名 | 说明 | 状态 |
|------|--------|------|------|------|
| **ODS** | 11 | `ods_projects`, `ods_issues`, `ods_journals`, `ods_journal_details` | 核心业务表 | ✅ |
| | | `ods_users`, `ods_groups`, `ods_group_users` | 用户与组织 | ✅ |
| | | `ods_project_memberships`, `ods_project_member_roles` | 项目成员 | ✅ |
| | | `ods_roles`, `ods_trackers`, `ods_issue_statuses` | 基础数据 | ✅ |
| **DWD** | 2 | `dwd_issue_daily_snapshot` | Issue 每日快照 | ✅ |
| | | `dwd_user_project_role` | 用户项目角色 | ✅ |
| **DWS** | 6 | `dws_project_daily_summary` | 项目每日汇总 | ✅ |
| | | `dws_issue_contributors`, `dws_issue_contributor_summary` | 贡献者分析 | ✅ |
| | | `dws_project_role_distribution` | 项目角色分布 | ✅ |
| | | `dws_user_monthly_workload` | 用户工作量 | ✅ |
| **DIM** | 5 | `dim_role_category` | 角色分类维度 | ✅ |
| | | `dim_date` | 日期维度 (2010-2030, 7670 天) | ✅ |
| | | `dim_project`, `dim_user`, `dim_issue` | SCD Type 2 维度 | ✅ |
| **合计** | **24** | | | ✅ |

### 规划表（27 张）- 待实现

| 分层 | 表数量 | 说明 |
|------|--------|------|
| **ODS** | 11 | 原始数据层 - 从 Redmine API 同步的原始数据 |
| **DWD** | 3 | 明细数据层 - 其他明细数据 |
| **DWS** | 5 | 汇总数据层 - 其他聚合统计 |
| **ADS** | 4 | 应用数据层 - 面向报表的数据 |
| **DIM** | 2 | 维度表 - 角色分类、日期维度 |

---

## 一、ODS 层 - 原始数据层 (11 张表)

从 Redmine API 直接同步的原始数据，保持与源系统一致。

### 1.1 核心业务表

| 表名 | 主键 | 说明 | 更新频率 |
|------|------|------|----------|
| `ods_projects` | project_id | 项目基本信息 | 每周 |
| `ods_issues` | issue_id | Issue 基本信息 | 每日 |
| `ods_journals` | journal_id | Issue 变更日志 | 每小时 |
| `ods_journal_details` | detail_id | Journal 变更明细 | 每小时 |

### 1.2 用户与组织表

| 表名 | 主键 | 说明 | 更新频率 |
|------|------|------|----------|
| `ods_users` | user_id | 用户基本信息 | 每周 |
| `ods_groups` | group_id | 组信息 | 每周 |
| `ods_group_users` | (group_id, user_id) | 组成员关系 | 每周 |

### 1.3 项目成员表

| 表名 | 主键 | 说明 | 更新频率 |
|------|------|------|----------|
| `ods_project_memberships` | membership_id | 项目成员关系 | 每周 |
| `ods_project_member_roles` | (membership_id, role_id) | 成员角色分配 | 每周 |

### 1.4 基础数据表

| 表名 | 主键 | 说明 | 更新频率 |
|------|------|------|----------|
| `ods_roles` | role_id | 角色定义 | 一次性 |
| `ods_trackers` | tracker_id | Tracker 类型（需求/Bug/任务） | 一次性 |
| `ods_issue_statuses` | status_id | Issue 状态定义 | 一次性 |

### ODS 层表结构详情

```sql
-- 项目表
CREATE TABLE ods_projects (
    project_id        INTEGER PRIMARY KEY,
    name              VARCHAR(255),
    identifier        VARCHAR(100),
    description       TEXT,
    status            INTEGER,           -- 1:激活, 5:关闭
    created_on        TIMESTAMP,
    updated_on        TIMESTAMP,
    parent_project_id INTEGER,
    sync_time         TIMESTAMP
);

-- Issue 表
CREATE TABLE ods_issues (
    issue_id        INTEGER PRIMARY KEY,
    project_id      INTEGER,
    tracker_id      INTEGER,
    status_id       INTEGER,
    priority_id     INTEGER,
    author_id       INTEGER,
    assigned_to_id  INTEGER,
    parent_issue_id INTEGER,
    subject         VARCHAR(500),
    description     TEXT,
    start_date      DATE,
    due_date        DATE,
    done_ratio      INTEGER,
    estimated_hours DECIMAL(10,2),
    spent_hours     DECIMAL(10,2),
    created_on      TIMESTAMP,
    updated_on      TIMESTAMP,
    closed_on       TIMESTAMP,
    sync_time       TIMESTAMP
);

-- Journal 表
CREATE TABLE ods_journals (
    journal_id   INTEGER PRIMARY KEY,
    issue_id     INTEGER,
    user_id      INTEGER,
    notes        TEXT,
    created_on   TIMESTAMP,
    sync_time    TIMESTAMP
);

-- Journal Detail 表
CREATE TABLE ods_journal_details (
    detail_id    INTEGER PRIMARY KEY,
    journal_id   INTEGER,
    property     VARCHAR(50),        -- attr/attachment/custom_field
    name         VARCHAR(100),       -- status_id/assigned_to_id 等
    old_value    TEXT,
    new_value    TEXT,
    sync_time    TIMESTAMP
);

-- 用户表
CREATE TABLE ods_users (
    user_id       INTEGER PRIMARY KEY,
    login         VARCHAR(100),
    firstname     VARCHAR(100),
    lastname      VARCHAR(100),
    mail          VARCHAR(255),
    status        INTEGER,            -- 1:激活, 0:锁定
    created_on    TIMESTAMP,
    last_login_on TIMESTAMP,
    sync_time     TIMESTAMP
);

-- 组表
CREATE TABLE ods_groups (
    group_id   INTEGER PRIMARY KEY,
    name       VARCHAR(255),
    sync_time  TIMESTAMP
);

-- 组成员关系
CREATE TABLE ods_group_users (
    group_id   INTEGER,
    user_id    INTEGER,
    sync_time  TIMESTAMP,
    PRIMARY KEY (group_id, user_id)
);

-- 项目成员表
CREATE TABLE ods_memberships (
    membership_id  INTEGER PRIMARY KEY,
    project_id     INTEGER,
    user_id        INTEGER,           -- 直接用户成员
    group_id       INTEGER,           -- 组成员（间接）
    sync_time      TIMESTAMP
);

-- 成员角色表
CREATE TABLE ods_member_roles (
    membership_id  INTEGER,
    role_id        INTEGER,
    sync_time      TIMESTAMP,
    PRIMARY KEY (membership_id, role_id)
);

-- 角色表
CREATE TABLE ods_roles (
    role_id   INTEGER PRIMARY KEY,
    name      VARCHAR(100),
    sync_time TIMESTAMP
);

-- Tracker 表
CREATE TABLE ods_trackers (
    tracker_id  INTEGER PRIMARY KEY,
    name        VARCHAR(100),
    sync_time   TIMESTAMP
);

-- Issue 状态表
CREATE TABLE ods_issue_statuses (
    status_id   INTEGER PRIMARY KEY,
    name        VARCHAR(100),
    is_closed   INTEGER DEFAULT 0,
    sync_time   TIMESTAMP
);
```

---

## 二、DWD 层 - 明细数据层 (4 张表)

清洗、转换、关联后的明细数据，便于分析查询。

### 2.1 业务明细表

| 表名 | 主键 | 说明 | 数据来源 |
|------|------|------|----------|
| `dwd_issues_full` | issue_id | Issue 完整明细（关联项目、状态、用户） | ODS 多表关联 |
| `dwd_user_project_role` | (project_id, user_id) | 用户在项目中的最高角色 | ODS memberships+roles |
| `dwd_issue_contributors` | (issue_id, user_id) | Issue 贡献者分析（按角色分类） | ODS journals+memberships |
| `dwd_journal_summary` | (issue_id, user_id) | Journal 汇总统计 | ODS journals+details |

### DWD 层表结构详情

```sql
-- Issue 完整明细
CREATE TABLE dwd_issues_full (
    issue_id          INTEGER PRIMARY KEY,
    project_id        INTEGER,
    project_name      VARCHAR(255),
    tracker_id        INTEGER,
    tracker_name      VARCHAR(100),
    status_id         INTEGER,
    status_name       VARCHAR(100),
    is_closed         INTEGER DEFAULT 0,
    priority_id       INTEGER,
    priority_name     VARCHAR(100),
    author_id         INTEGER,
    author_name       VARCHAR(200),
    assigned_to_id    INTEGER,
    assigned_to_name  VARCHAR(200),
    subject           VARCHAR(500),
    start_date        DATE,
    due_date          DATE,
    done_ratio        INTEGER,
    estimated_hours   DECIMAL(10,2),
    spent_hours       DECIMAL(10,2),
    created_date      DATE,
    created_on        TIMESTAMP,
    updated_on        TIMESTAMP,
    closed_on         TIMESTAMP,
    duration_days     INTEGER,
    etl_time          TIMESTAMP
);

-- 用户在项目中的角色
CREATE TABLE dwd_user_project_role (
    project_id        INTEGER,
    user_id           INTEGER,
    highest_role_id   INTEGER,
    highest_role_name VARCHAR(100),
    role_category     VARCHAR(20),     -- manager/implementation/developer/tester/other
    role_priority     INTEGER,         -- 1 最高
    all_role_ids      VARCHAR(200),    -- 所有角色 ID 列表
    is_direct_member  INTEGER DEFAULT 1,
    etl_time          TIMESTAMP,
    PRIMARY KEY (project_id, user_id)
);

-- Issue 贡献者分析
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
    etl_time            TIMESTAMP,
    PRIMARY KEY (issue_id, user_id)
);

-- Journal 汇总
CREATE TABLE dwd_journal_summary (
    issue_id              INTEGER,
    user_id               INTEGER,
    user_name             VARCHAR(200),
    journal_count         INTEGER,
    first_journal         TIMESTAMP,
    last_journal          TIMESTAMP,
    status_change_count   INTEGER,
    assigned_change_count INTEGER,
    note_count            INTEGER,
    attachment_count      INTEGER,
    etl_time              TIMESTAMP,
    PRIMARY KEY (issue_id, user_id)
);
```

---

## 三、DWS 层 - 汇总数据层 (6 张表)

按维度聚合的统计信息，支持快速查询。

### 3.1 项目统计

| 表名 | 主键 | 说明 | 粒度 |
|------|------|------|------|
| `dws_project_daily_stats` | (project_id, stat_date) | 项目每日统计 | 项目 + 日期 |
| `dws_project_role_distribution` | (project_id, stat_date) | 项目角色分布 | 项目 + 日期 |
| `dws_project_contributor_stats` | (project_id, stat_date, user_id) | 项目贡献者统计 | 项目 + 日期 + 用户 |
| `dws_tracker_distribution` | (project_id, stat_date, tracker_id) | Tracker 类型分布 | 项目 + 日期 + Tracker |

### 3.2 Issue 统计

| 表名 | 主键 | 说明 | 粒度 |
|------|------|------|------|
| `dws_issue_contributor_summary` | issue_id | Issue 贡献者汇总 | Issue |

### 3.3 用户统计

| 表名 | 主键 | 说明 | 粒度 |
|------|------|------|------|
| `dws_user_monthly_workload` | (user_id, year_month) | 用户月度工作量 | 用户 + 月份 |

### DWS 层表结构详情

```sql
-- 项目每日统计
CREATE TABLE dws_project_daily_stats (
    project_id          INTEGER,
    stat_date           DATE,
    total_issues        INTEGER,
    new_issues          INTEGER,
    closed_issues       INTEGER,
    open_issues         INTEGER,
    in_progress_issues  INTEGER,
    total_spent_hours   DECIMAL(10,2),
    total_estimated_hours DECIMAL(10,2),
    avg_done_ratio      DECIMAL(5,2),
    active_contributors INTEGER,
    etl_time            TIMESTAMP,
    PRIMARY KEY (project_id, stat_date)
);

-- 项目角色分布
CREATE TABLE dws_project_role_distribution (
    project_id           INTEGER,
    stat_date            DATE,
    manager_count        INTEGER,
    implementation_count INTEGER,
    developer_count      INTEGER,
    tester_count         INTEGER,
    other_count          INTEGER,
    total_members        INTEGER,
    etl_time             TIMESTAMP,
    PRIMARY KEY (project_id, stat_date)
);

-- 项目贡献者统计
CREATE TABLE dws_project_contributor_stats (
    project_id        INTEGER,
    stat_date         DATE,
    user_id           INTEGER,
    user_name         VARCHAR(200),
    role_category     VARCHAR(20),
    total_issues      INTEGER,
    created_issues    INTEGER,
    assigned_issues   INTEGER,
    closed_issues     INTEGER,
    journal_count     INTEGER,
    spent_hours       DECIMAL(10,2),
    first_activity    DATE,
    last_activity     DATE,
    etl_time          TIMESTAMP,
    PRIMARY KEY (project_id, stat_date, user_id)
);

-- Tracker 分布
CREATE TABLE dws_tracker_distribution (
    project_id        INTEGER,
    stat_date         DATE,
    tracker_id        INTEGER,
    tracker_name      VARCHAR(100),
    total_count       INTEGER,
    open_count        INTEGER,
    closed_count      INTEGER,
    avg_duration_days DECIMAL(10,2),
    etl_time          TIMESTAMP,
    PRIMARY KEY (project_id, stat_date, tracker_id)
);

-- Issue 贡献者汇总
CREATE TABLE dws_issue_contributor_summary (
    issue_id             INTEGER PRIMARY KEY,
    project_id           INTEGER,
    manager_count        INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count      INTEGER DEFAULT 0,
    tester_count         INTEGER DEFAULT 0,
    other_count          INTEGER DEFAULT 0,
    total_contributors   INTEGER DEFAULT 0,
    total_journals       INTEGER DEFAULT 0,
    etl_time             TIMESTAMP
);

-- 用户月度工作量
CREATE TABLE dws_user_monthly_workload (
    user_id           INTEGER,
    year_month        VARCHAR(7),       -- YYYY-MM
    total_issues      INTEGER,
    created_issues    INTEGER,
    closed_issues     INTEGER,
    total_journals    INTEGER,
    total_spent_hours DECIMAL(10,2),
    projects_involved INTEGER,
    as_manager        INTEGER,
    as_developer      INTEGER,
    as_implementation INTEGER,
    etl_time          TIMESTAMP,
    PRIMARY KEY (user_id, year_month)
);
```

---

## 四、ADS 层 - 应用数据层 (4 张表)

面向具体应用场景的报表数据。

### 4.1 应用报表

| 表名 | 主键 | 说明 | 用途 |
|------|------|------|------|
| `ads_project_status_report` | project_id | 项目状态报表 | 项目概览 |
| `ads_user_workload_ranking` | (stat_month, rank_type, user_id) | 用户工作量排名 | 绩效考核 |
| `ads_issue_quality_report` | (project_id, stat_month) | Issue 质量报表 | 质量分析 |
| `ads_team_load_analysis` | (project_id, stat_date, role_category) | 团队负载分析 | 资源调配 |

### ADS 层表结构详情

```sql
-- 项目状态报表
CREATE TABLE ads_project_status_report (
    project_id         INTEGER PRIMARY KEY,
    project_name       VARCHAR(255),
    status             VARCHAR(20),
    total_issues       INTEGER,
    open_issues        INTEGER,
    closed_issues      INTEGER,
    overdue_issues     INTEGER,
    completion_rate    DECIMAL(5,2),
    total_members      INTEGER,
    active_members_30d INTEGER,
    total_spent_hours  DECIMAL(10,2),
    last_updated       DATE,
    report_date        DATE,
    etl_time           TIMESTAMP
);

-- 用户工作量排名
CREATE TABLE ads_user_workload_ranking (
    stat_month    VARCHAR(7),
    rank_type     VARCHAR(20),         -- by_issues/by_hours/by_journals
    user_id       INTEGER,
    user_name     VARCHAR(200),
    role_category VARCHAR(20),
    metric_value  DECIMAL(10,2),
    rank_num      INTEGER,
    project_count INTEGER,
    etl_time      TIMESTAMP,
    PRIMARY KEY (stat_month, rank_type, user_id)
);

-- Issue 质量报表
CREATE TABLE ads_issue_quality_report (
    project_id          INTEGER,
    stat_month          VARCHAR(7),
    total_issues        INTEGER,
    reopen_count        INTEGER,
    avg_reopen_times    DECIMAL(5,2),
    avg_resolution_days DECIMAL(10,2),
    overdue_rate        DECIMAL(5,2),
    bug_ratio           DECIMAL(5,2),
    etl_time            TIMESTAMP,
    PRIMARY KEY (project_id, stat_month)
);

-- 团队负载分析
CREATE TABLE ads_team_load_analysis (
    project_id         INTEGER,
    stat_date          DATE,
    role_category      VARCHAR(20),
    member_count       INTEGER,
    total_issues       INTEGER,
    avg_issues_per_person DECIMAL(5,2),
    total_spent_hours  DECIMAL(10,2),
    avg_hours_per_person DECIMAL(10,2),
    overload_count     INTEGER,
    underload_count    INTEGER,
    etl_time           TIMESTAMP,
    PRIMARY KEY (project_id, stat_date, role_category)
);
```

---

## 五、DIM 层 - 维度表 (2 张表)

公共维度数据，用于关联分析。

### 5.1 维度表

| 表名 | 主键 | 说明 | 更新方式 |
|------|------|------|----------|
| `dim_role_category` | role_id | 角色分类维度 | 一次性 |
| `dim_date` | date_key | 日期维度 | 预生成 |

### 维度表结构详情

```sql
-- 角色分类维度
CREATE TABLE dim_role_category (
    role_id      INTEGER PRIMARY KEY,
    role_name    VARCHAR(100),
    category     VARCHAR(20),         -- manager/implementation/developer/tester/other
    priority     INTEGER,             -- 1 最高
    description  VARCHAR(255)
);

-- 预置数据
INSERT INTO dim_role_category VALUES
(3, '管理人员', 'manager', 1, '项目经理、管理员'),
(8, '实施人员', 'implementation', 2, '实施顾问、部署人员'),
(4, '开发人员', 'developer', 3, '开发工程师'),
(7, '测试人员', 'tester', 4, '测试工程师'),
(5, '报告人员', 'reporter', 5, '报告查看者'),
(6, '查询人员', 'viewer', 6, '只读权限');

-- 日期维度
CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,  -- YYYYMMDD
    full_date    DATE,
    year         INTEGER,
    month        INTEGER,
    day          INTEGER,
    quarter      INTEGER,
    week_of_year INTEGER,
    day_of_week  INTEGER,
    day_name     VARCHAR(20),
    month_name   VARCHAR(20),
    is_weekend   INTEGER DEFAULT 0,
    is_holiday   INTEGER DEFAULT 0
);
```

---

## 六、表关系图

```
┌─────────────────────────────────────────────────────────────┐
│                        ODS 层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ ods_projects│  │  ods_users  │  │   ods_issues        │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────────▼──────────┐  │
│  │ods_memberships│ │ods_groups  │  │   ods_journals      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│  ┌──────▼──────┐         │            ┌───────▼────────┐    │
│  │ods_member_roles       │            │ods_journal_details│ │
│  └─────────────┘         │            └────────────────┘    │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        DWD 层                                │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ dwd_issues_full │  │dwd_user_project_role│               │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
│  ┌────────▼────────────────────▼─────────┐                  │
│  │      dwd_issue_contributors           │                  │
│  └───────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        DWS 层                                │
│  ┌──────────────────────┐  ┌──────────────────────────┐     │
│  │dws_project_daily_stats│  │dws_issue_contributor_summary│  │
│  └──────────────────────┘  └──────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        ADS 层                                │
│  ┌─────────────────────┐  ┌──────────────────────────┐      │
│  │ads_project_status_report│ │ads_user_workload_ranking│      │
│  └─────────────────────┘  └──────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 七、快速索引

### 按功能查找表

**项目相关:**
- `ods_projects` → `dwd_issues_full` → `dws_project_daily_stats` → `ads_project_status_report`

**用户相关:**
- `ods_users` → `dwd_user_project_role` → `dws_user_monthly_workload` → `ads_user_workload_ranking`

**Issue 相关:**
- `ods_issues` → `dwd_issues_full` → `dws_issue_contributor_summary` → `ads_issue_quality_report`

**贡献者分析:**
- `ods_journals` → `dwd_issue_contributors` → `dws_issue_contributor_summary`

**角色分类:**
- `ods_roles` + `ods_project_member_roles` → `dwd_user_project_role` → `dws_project_role_distribution` → `dim_role_category`

### 按更新频率

**一次性:** `dim_role_category`, `dim_date`, `ods_roles`, `ods_trackers`, `ods_issue_statuses`

**每周:** `ods_projects`, `ods_users`, `ods_groups`, `ods_project_memberships`

**每日:** `ods_issues`, `dwd_*`, `dws_project_daily_stats`, `ads_*`

**每小时:** `ods_journals`, `ods_journal_details`

---

## 七、已实现表详细结构（2026-02-27 实际）

### 7.1 DWD 层 - 明细数据层（1 张）

#### `warehouse.issue_daily_snapshot`

Issue 每日快照表，记录每个 Issue 在每日的状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| issue_id | INTEGER | Issue ID |
| project_id | INTEGER | 项目 ID |
| snapshot_date | DATE | 快照日期 |
| subject | TEXT | Issue 标题 |
| status_id | INTEGER | 状态 ID |
| status_name | TEXT | 状态名称 |
| priority_id | INTEGER | 优先级 ID |
| priority_name | TEXT | 优先级名称 |
| assigned_to_id | INTEGER | 指派人 ID |
| assigned_to_name | TEXT | 指派人姓名 |
| created_at | TIMESTAMP | Issue 创建时间 |
| updated_at | TIMESTAMP | Issue 更新时间 |
| due_date | DATE | 截止日期 |
| is_new | BOOLEAN | 是否当日新建 |
| is_closed | BOOLEAN | 是否当日关闭 |
| is_updated | BOOLEAN | 是否当日更新 |
| created_at_snapshot | TIMESTAMP | 快照创建时间 |

**索引**: `uk_issue_snapshot(issue_id, snapshot_date)`, `idx_issue_project_date(project_id, snapshot_date)` 等

**数据量**: ~3,956 行

---

### 7.2 DWS 层 - 汇总数据层（1 张）

#### `warehouse.project_daily_summary`

项目每日汇总表，快速查询项目统计。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | BIGINT | | 主键 |
| project_id | INTEGER | | 项目 ID |
| snapshot_date | DATE | | 快照日期 |
| total_issues | INTEGER | 0 | Issue 总数 |
| new_issues | INTEGER | 0 | 新建数 |
| closed_issues | INTEGER | 0 | 关闭数 |
| updated_issues | INTEGER | 0 | 更新数 |
| status_new/in_progress/resolved/closed | INTEGER | 0 | 按状态统计 |
| status_feedback/testing/code_review | INTEGER | 0 | 扩展状态 |
| priority_immediate/urgent/high/normal/low | INTEGER | 0 | 按优先级统计 |
| created_at_snapshot | TIMESTAMP | CURRENT_TIMESTAMP | 创建时间 |

**索引**: `uk_project_summary(project_id, snapshot_date)`

**数据量**: ~539 行

---

### 7.3 DWS-Contributor 层 - 贡献者分析（5 张）⭐ 2026-02-27 新增

#### `warehouse.issue_contributors`

Issue 贡献者明细表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| issue_id | INTEGER | Issue ID |
| project_id | INTEGER | 项目 ID |
| user_id | INTEGER | 用户 ID |
| user_name | VARCHAR(200) | 用户姓名 |
| highest_role_id | INTEGER | 最高角色 ID |
| highest_role_name | VARCHAR(100) | 最高角色名称 |
| role_category | VARCHAR(20) | manager/implementation/developer/tester/other |
| journal_count | INTEGER | Journals 数量 |
| first_contribution | TIMESTAMP | 首次贡献时间 |
| last_contribution | TIMESTAMP | 最后贡献时间 |
| status_change_count | INTEGER | 状态变更次数 |
| note_count | INTEGER | 评论数 |
| assigned_change_count | INTEGER | 指派人变更次数 |
| created_at_snapshot | TIMESTAMP | 创建时间 |

**索引**: `uk_issue_contributor(issue_id, user_id)`, `idx_contributors_user(user_id)` 等

**数据量**: 27 行（11 个 Issue）

---

#### `warehouse.issue_contributor_summary`

Issue 贡献者汇总表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| issue_id | INTEGER | Issue ID（唯一） |
| project_id | INTEGER | 项目 ID |
| manager_count | INTEGER | 管理人员数 |
| implementation_count | INTEGER | 实施人员数 |
| developer_count | INTEGER | 开发人员数 |
| tester_count | INTEGER | 测试人员数 |
| other_count | INTEGER | 其他人员数 |
| total_contributors | INTEGER | 贡献者总数 |
| total_journals | INTEGER | Journals 总数 |
| created_at_snapshot | TIMESTAMP | 创建时间 |

**索引**: `issue_contributor_summary_issue_id_key(issue_id)` UNIQUE

**数据量**: 11 行

---

#### `warehouse.user_project_role`

用户项目角色表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| project_id | INTEGER | 项目 ID |
| user_id | INTEGER | 用户 ID |
| highest_role_id | INTEGER | 最高角色 ID |
| highest_role_name | VARCHAR(100) | 最高角色名称 |
| role_category | VARCHAR(20) | 角色类别 |
| role_priority | INTEGER | 角色优先级 (1-5) |
| all_role_ids | VARCHAR(200) | 所有角色 ID 列表 |
| is_direct_member | BOOLEAN | 是否直接成员 |
| created_at_snapshot | TIMESTAMP | 创建时间 |

**索引**: `uk_user_project_role(project_id, user_id)`, `idx_user_role_user(user_id)`

**数据量**: 0 行（待同步）

---

#### `warehouse.project_role_distribution`

项目角色分布表。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | BIGINT | | 主键 |
| project_id | INTEGER | | 项目 ID |
| snapshot_date | DATE | | 快照日期 |
| manager_count | INTEGER | 0 | 管理人员数 |
| implementation_count | INTEGER | 0 | 实施人员数 |
| developer_count | INTEGER | 0 | 开发人员数 |
| tester_count | INTEGER | 0 | 测试人员数 |
| other_count | INTEGER | 0 | 其他人员数 |
| total_members | INTEGER | 0 | 成员总数 |
| created_at_snapshot | TIMESTAMP | CURRENT_TIMESTAMP | 创建时间 |

**索引**: `uk_project_role_dist(project_id, snapshot_date)`

**数据量**: 1 行

---

#### `warehouse.user_workload`

用户工作量统计表。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | BIGINT | | 主键 |
| user_id | INTEGER | | 用户 ID |
| user_name | VARCHAR(200) | | 用户姓名 |
| year_month | VARCHAR(7) | | 年月 (YYYY-MM) |
| project_id | INTEGER | | 项目 ID |
| total_issues | INTEGER | 0 | 参与 Issue 数 |
| total_journals | INTEGER | 0 | 总操作数 |
| as_manager | INTEGER | 0 | 作为管理人员 |
| as_implementation | INTEGER | 0 | 作为实施人员 |
| as_developer | INTEGER | 0 | 作为开发人员 |
| as_tester | INTEGER | 0 | 作为测试人员 |
| resolved_issues | INTEGER | 0 | 解决 Issue 数 |
| verified_issues | INTEGER | 0 | 验证 Issue 数 |
| created_at_snapshot | TIMESTAMP | CURRENT_TIMESTAMP | 创建时间 |

**索引**: `uk_user_workload(user_id, year_month, project_id)`, `idx_user_workload_user(user_id)`

**数据量**: 0 行（待同步）

---

### 7.4 存储函数（4 个）

| 函数名 | 参数 | 说明 |
|--------|------|------|
| `refresh_daily_summary` | (project_id, snapshot_date) | 刷新项目每日汇总 |
| `refresh_contributor_summary` ⭐ | (issue_id, project_id) | 刷新 Issue 贡献者汇总 |
| `refresh_project_role_distribution` ⭐ | (project_id, snapshot_date) | 刷新项目角色分布 |
| `refresh_user_workload` ⭐ | (user_id, user_name, year_month, project_id) | 刷新用户工作量 |

---

## 八、扩展历史

### 2026-02-25 - 基础数仓上线
- ✅ `issue_daily_snapshot` - Issue 每日快照
- ✅ `project_daily_summary` - 项目每日汇总
- ✅ 定时同步调度器（每 10 分钟增量，每天全量）

### 2026-02-27 - 贡献者分析扩展
- ✅ `issue_contributors` - Issue 贡献者明细
- ✅ `issue_contributor_summary` - Issue 贡献者汇总
- ✅ `user_project_role` - 用户项目角色
- ✅ `project_role_distribution` - 项目角色分布
- ✅ `user_workload` - 用户工作量统计
- ✅ 新增 4 个 MCP 工具
- ✅ 新增 3 个存储函数
- ✅ 新增 12 个索引

---

**文档版本**: 2.0  
**最后更新**: 2026-02-27  
**实际表数**: 7 张  
**规划表数**: 27 张
