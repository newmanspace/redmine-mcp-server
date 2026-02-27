-- Redmine MCP 数仓 - ODS 层原始数据表
-- 版本：1.0
-- 创建日期：2026-02-27
-- 说明：从 Redmine API 同步的原始数据，保持与源系统一致

-- =====================================================
-- 1. 核心业务表 (4 张)
-- =====================================================

-- 项目表
CREATE TABLE IF NOT EXISTS warehouse.ods_projects (
    project_id        INTEGER PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    identifier        VARCHAR(100) NOT NULL,
    description       TEXT,
    status            INTEGER,           -- 1:激活，5:关闭
    created_on        TIMESTAMP,
    updated_on        TIMESTAMP,
    parent_project_id INTEGER,
    sync_time         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issue 表
CREATE TABLE IF NOT EXISTS warehouse.ods_issues (
    issue_id        INTEGER PRIMARY KEY,
    project_id      INTEGER NOT NULL,
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
    sync_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal 表（Issue 变更日志）
CREATE TABLE IF NOT EXISTS warehouse.ods_journals (
    journal_id   INTEGER PRIMARY KEY,
    issue_id     INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    notes        TEXT,
    created_on   TIMESTAMP,
    sync_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal Detail 表（变更明细）
CREATE TABLE IF NOT EXISTS warehouse.ods_journal_details (
    detail_id    SERIAL PRIMARY KEY,
    journal_id   INTEGER NOT NULL,
    property     VARCHAR(50),        -- attr/attachment/custom_field
    name         VARCHAR(100),       -- status_id/assigned_to_id 等
    old_value    TEXT,
    new_value    TEXT,
    sync_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. 用户与组织表 (3 张)
-- =====================================================

-- 用户表
CREATE TABLE IF NOT EXISTS warehouse.ods_users (
    user_id       INTEGER PRIMARY KEY,
    login         VARCHAR(100) NOT NULL,
    firstname     VARCHAR(100),
    lastname      VARCHAR(100),
    mail          VARCHAR(255),
    status        INTEGER,            -- 1:激活，0:锁定
    created_on    TIMESTAMP,
    last_login_on TIMESTAMP,
    sync_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 组表
CREATE TABLE IF NOT EXISTS warehouse.ods_groups (
    group_id   INTEGER PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    is_builtin INTEGER DEFAULT 0,     -- 是否内置组
    sync_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 组成员关系
CREATE TABLE IF NOT EXISTS warehouse.ods_group_users (
    group_id   INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    sync_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id)
);

-- =====================================================
-- 3. 项目成员表 (2 张)
-- =====================================================

-- 项目成员表
CREATE TABLE IF NOT EXISTS warehouse.ods_project_memberships (
    membership_id  INTEGER PRIMARY KEY,
    project_id     INTEGER NOT NULL,
    user_id        INTEGER,           -- 直接用户成员
    group_id       INTEGER,           -- 组成员（间接）
    created_on     TIMESTAMP,
    sync_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 成员角色表
CREATE TABLE IF NOT EXISTS warehouse.ods_project_member_roles (
    membership_id  INTEGER NOT NULL,
    role_id        INTEGER NOT NULL,
    sync_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (membership_id, role_id)
);

-- =====================================================
-- 4. 基础数据表 (3 张)
-- =====================================================

-- 角色表
CREATE TABLE IF NOT EXISTS warehouse.ods_roles (
    role_id       INTEGER PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    is_builtin    INTEGER DEFAULT 0,
    permissions   TEXT,              -- JSON 格式存储权限列表
    sync_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracker 表（Issue 类型）
CREATE TABLE IF NOT EXISTS warehouse.ods_trackers (
    tracker_id    INTEGER PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    description   TEXT,
    is_in_chlog   INTEGER DEFAULT 0, -- 是否显示在变更日志
    is_in_roadmap INTEGER DEFAULT 0, -- 是否显示在路线图
    position      INTEGER,
    sync_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issue 状态表
CREATE TABLE IF NOT EXISTS warehouse.ods_issue_statuses (
    status_id     INTEGER PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    is_closed     INTEGER DEFAULT 0,
    is_default    INTEGER DEFAULT 0,
    position      INTEGER,
    sync_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 5. 索引
-- =====================================================

-- 项目表索引
CREATE INDEX IF NOT EXISTS idx_ods_projects_status ON warehouse.ods_projects(status);
CREATE INDEX IF NOT EXISTS idx_ods_projects_parent ON warehouse.ods_projects(parent_project_id);

-- Issue 表索引
CREATE INDEX IF NOT EXISTS idx_ods_issues_project ON warehouse.ods_issues(project_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_status ON warehouse.ods_issues(status_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_tracker ON warehouse.ods_issues(tracker_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_author ON warehouse.ods_issues(author_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_assigned ON warehouse.ods_issues(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_updated ON warehouse.ods_issues(updated_on);

-- Journal 表索引
CREATE INDEX IF NOT EXISTS idx_ods_journals_issue ON warehouse.ods_journals(issue_id);
CREATE INDEX IF NOT EXISTS idx_ods_journals_user ON warehouse.ods_journals(user_id);

-- Journal Detail 表索引
CREATE INDEX IF NOT EXISTS idx_ods_journal_details_journal ON warehouse.ods_journal_details(journal_id);
CREATE INDEX IF NOT EXISTS idx_ods_journal_details_name ON warehouse.ods_journal_details(name);

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_ods_users_status ON warehouse.ods_users(status);
CREATE INDEX IF NOT EXISTS idx_ods_users_login ON warehouse.ods_users(login);

-- 组成员关系索引
CREATE INDEX IF NOT EXISTS idx_ods_group_users_user ON warehouse.ods_group_users(user_id);

-- 项目成员表索引
CREATE INDEX IF NOT EXISTS idx_ods_project_memberships_project ON warehouse.ods_project_memberships(project_id);
CREATE INDEX IF NOT EXISTS idx_ods_project_memberships_user ON warehouse.ods_project_memberships(user_id);

-- =====================================================
-- 6. 授予权限
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;

-- =====================================================
-- 7. 表注释
-- =====================================================

COMMENT ON TABLE warehouse.ods_projects IS 'ODS-项目基本信息表';
COMMENT ON TABLE warehouse.ods_issues IS 'ODS-Issue 基本信息表';
COMMENT ON TABLE warehouse.ods_journals IS 'ODS-Issue 变更日志表';
COMMENT ON TABLE warehouse.ods_journal_details IS 'ODS-Journal 变更明细表';
COMMENT ON TABLE warehouse.ods_users IS 'ODS-用户基本信息表';
COMMENT ON TABLE warehouse.ods_groups IS 'ODS-组信息表';
COMMENT ON TABLE warehouse.ods_group_users IS 'ODS-组成员关系表';
COMMENT ON TABLE warehouse.ods_project_memberships IS 'ODS-项目成员关系表';
COMMENT ON TABLE warehouse.ods_project_member_roles IS 'ODS-成员角色分配表';
COMMENT ON TABLE warehouse.ods_roles IS 'ODS-角色定义表';
COMMENT ON TABLE warehouse.ods_trackers IS 'ODS-Tracker 类型表（需求/Bug/任务）';
COMMENT ON TABLE warehouse.ods_issue_statuses IS 'ODS-Issue 状态定义表';
