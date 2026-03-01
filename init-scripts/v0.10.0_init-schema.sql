-- =====================================================
-- Redmine MCP Server - Database Schema
-- Version: v0.10.0
-- Type: SCHEMA
-- Date: 2026-02-28
-- Description: Initial database schema
-- =====================================================

-- =====================================================
-- 1. Extensions and Schema
-- =====================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SET timezone = 'Asia/Shanghai';
CREATE SCHEMA IF NOT EXISTS warehouse;
SET search_path TO warehouse, public;


-- =====================================================
-- 2. Table Definitions
-- =====================================================

-- -----------------------------------------------------
-- 2.1 ODS Layer - Operational Data Store
-- -----------------------------------------------------

CREATE TABLE warehouse.ods_projects (
    project_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    identifier VARCHAR(100) NOT NULL,
    description TEXT,
    status INTEGER,
    created_on TIMESTAMP,
    updated_on TIMESTAMP,
    parent_project_id INTEGER
);

CREATE TABLE warehouse.ods_issues (
    issue_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    tracker_id INTEGER,
    status_id INTEGER,
    priority_id INTEGER,
    author_id INTEGER,
    assigned_to_id INTEGER,
    parent_issue_id INTEGER,
    subject VARCHAR(500),
    description TEXT,
    start_date DATE,
    due_date DATE,
    done_ratio INTEGER,
    estimated_hours DECIMAL(10,2),
    spent_hours DECIMAL(10,2),
    created_on TIMESTAMP,
    updated_on TIMESTAMP,
    closed_on TIMESTAMP
);

CREATE TABLE warehouse.ods_journals (
    journal_id INTEGER PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    notes TEXT,
    created_on TIMESTAMP
);

CREATE TABLE warehouse.ods_journal_details (
    detail_id SERIAL PRIMARY KEY,
    journal_id INTEGER NOT NULL,
    property VARCHAR(50),
    name VARCHAR(100),
    old_value TEXT,
    new_value TEXT
);

CREATE TABLE warehouse.ods_users (
    user_id INTEGER PRIMARY KEY,
    login VARCHAR(100) NOT NULL,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    mail VARCHAR(255),
    status INTEGER,
    created_on TIMESTAMP,
    last_login_on TIMESTAMP
);

CREATE TABLE warehouse.ods_groups (
    group_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_builtin INTEGER DEFAULT 0
);

CREATE TABLE warehouse.ods_group_users (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE warehouse.ods_project_memberships (
    membership_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER,
    group_id INTEGER
);

CREATE TABLE warehouse.ods_project_member_roles (
    membership_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (membership_id, role_id)
);

CREATE TABLE warehouse.ods_roles (
    role_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_builtin INTEGER DEFAULT 0,
    permissions TEXT
);

CREATE TABLE warehouse.ods_trackers (
    tracker_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_in_chlog INTEGER DEFAULT 0,
    is_in_roadmap INTEGER DEFAULT 0,
    position INTEGER
);

CREATE TABLE warehouse.ods_issue_statuses (
    status_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_closed INTEGER DEFAULT 0,
    is_default INTEGER DEFAULT 0,
    position INTEGER
);


-- -----------------------------------------------------
-- 2.2 DIM Layer - Dimension Tables (维度表)
-- -----------------------------------------------------

CREATE TABLE warehouse.dim_role_category (
    role_id INTEGER PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    priority INTEGER NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE
);

CREATE TABLE warehouse.dim_project (
    project_id INTEGER PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    project_identifier VARCHAR(100),
    parent_project_id INTEGER,
    project_level INTEGER DEFAULT 1,
    project_path TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE warehouse.dim_user (
    user_id INTEGER PRIMARY KEY,
    user_name VARCHAR(200) NOT NULL,
    login_name VARCHAR(100),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE warehouse.dim_issue (
    issue_id INTEGER PRIMARY KEY,
    issue_subject TEXT,
    tracker_name VARCHAR(100),
    status_name VARCHAR(100),
    priority_name VARCHAR(100),
    is_closed BOOLEAN DEFAULT FALSE
);


-- -----------------------------------------------------
-- 2.3 DWD Layer - Data Warehouse Detail (明细数据层)
-- -----------------------------------------------------

CREATE TABLE warehouse.dwd_issue_daily_snapshot (
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
    CONSTRAINT uk_dwd_issue_snapshot UNIQUE (issue_id, snapshot_date)
);

CREATE TABLE warehouse.dwd_user_project_role (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    highest_role_id INTEGER,
    highest_role_name TEXT,
    role_category TEXT,
    role_priority INTEGER,
    all_role_ids TEXT,
    is_direct_member BOOLEAN DEFAULT TRUE,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_dwd_user_project_role UNIQUE (project_id, user_id)
);


-- -----------------------------------------------------
-- 2.4 DWS Layer - Data Warehouse Summary (汇总数据层)
-- -----------------------------------------------------

CREATE TABLE warehouse.dws_project_daily_summary (
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
    CONSTRAINT uk_dws_project_summary UNIQUE (project_id, snapshot_date)
);

CREATE TABLE warehouse.dws_issue_contributors (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT,
    highest_role_id INTEGER,
    highest_role_name TEXT,
    role_category TEXT,
    journal_count INTEGER DEFAULT 0,
    first_contribution TIMESTAMP,
    last_contribution TIMESTAMP,
    status_change_count INTEGER DEFAULT 0,
    note_count INTEGER DEFAULT 0,
    assigned_change_count INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_dws_issue_contributor UNIQUE (issue_id, user_id)
);

CREATE TABLE warehouse.dws_issue_contributor_summary (
    issue_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    manager_count INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    tester_count INTEGER DEFAULT 0,
    other_count INTEGER DEFAULT 0,
    total_contributors INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouse.dws_project_role_distribution (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    manager_count INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    tester_count INTEGER DEFAULT 0,
    other_count INTEGER DEFAULT 0,
    total_members INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_dws_project_role_distribution UNIQUE (project_id, snapshot_date)
);

CREATE TABLE warehouse.dws_user_monthly_workload (
    user_id INTEGER NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    total_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    as_manager INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer INTEGER DEFAULT 0,
    as_tester INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, year_month)
);


-- -----------------------------------------------------
-- 2.5 ADS Layer - Application Data Store (应用数据层)
-- -----------------------------------------------------

CREATE TABLE warehouse.ads_contributor_report (
    report_id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    project_name VARCHAR(255),
    year_month VARCHAR(7) NOT NULL,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(200),
    role_category VARCHAR(20),
    total_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    resolved_issues INTEGER DEFAULT 0,
    verified_issues INTEGER DEFAULT 0,
    as_manager INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer INTEGER DEFAULT 0,
    as_tester INTEGER DEFAULT 0,
    avg_resolution_days DECIMAL(10,2),
    report_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, year_month, user_id)
);

CREATE TABLE warehouse.ads_project_health_report (
    report_id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    project_name VARCHAR(255),
    snapshot_date DATE NOT NULL,
    total_issues INTEGER DEFAULT 0,
    new_issues INTEGER DEFAULT 0,
    closed_issues INTEGER DEFAULT 0,
    open_issues INTEGER DEFAULT 0,
    status_new INTEGER DEFAULT 0,
    status_in_progress INTEGER DEFAULT 0,
    status_resolved INTEGER DEFAULT 0,
    status_closed INTEGER DEFAULT 0,
    priority_immediate INTEGER DEFAULT 0,
    priority_urgent INTEGER DEFAULT 0,
    priority_high INTEGER DEFAULT 0,
    health_score DECIMAL(5,2),
    issue_velocity DECIMAL(10,2),
    avg_age_days DECIMAL(10,2),
    overdue_rate DECIMAL(5,4),
    new_trend DECIMAL(5,2),
    closed_trend DECIMAL(5,2),
    risk_level VARCHAR(20),
    risk_factors TEXT,
    report_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, snapshot_date)
);

CREATE TABLE warehouse.ads_team_performance_report (
    report_id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    project_name VARCHAR(255),
    year_month VARCHAR(7) NOT NULL,
    total_members INTEGER DEFAULT 0,
    manager_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    tester_count INTEGER DEFAULT 0,
    total_issues INTEGER DEFAULT 0,
    resolved_issues INTEGER DEFAULT 0,
    closed_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    avg_resolution_days DECIMAL(10,2),
    issues_per_member DECIMAL(10,2),
    journals_per_member DECIMAL(10,2),
    collaboration_rate DECIMAL(5,2),
    self_resolve_rate DECIMAL(5,2),
    reopen_rate DECIMAL(5,4),
    overdue_rate DECIMAL(5,4),
    mom_growth DECIMAL(5,2),
    yoy_growth DECIMAL(5,2),
    performance_score DECIMAL(5,2),
    performance_level VARCHAR(20),
    report_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, year_month)
);

CREATE TABLE warehouse.ads_user_workload_report (
    report_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(200),
    year_month VARCHAR(7) NOT NULL,
    total_projects INTEGER DEFAULT 0,
    total_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    as_manager INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer INTEGER DEFAULT 0,
    as_tester INTEGER DEFAULT 0,
    resolved_issues INTEGER DEFAULT 0,
    verified_issues INTEGER DEFAULT 0,
    created_issues INTEGER DEFAULT 0,
    avg_resolution_days DECIMAL(10,2),
    issues_per_day DECIMAL(10,2),
    project_details JSONB,
    rank_in_month INTEGER,
    percentile DECIMAL(5,2),
    report_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, year_month)
);

CREATE TABLE warehouse.ads_user_subscriptions (
    subscription_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(200),
    user_email VARCHAR(255),
    project_id INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL,
    channel_id VARCHAR(255) NOT NULL,
    report_type VARCHAR(20) NOT NULL DEFAULT 'daily',
    report_level VARCHAR(20) NOT NULL DEFAULT 'brief',
    language VARCHAR(10) DEFAULT 'zh_CN',
    send_time VARCHAR(50),
    send_day_of_week VARCHAR(10),
    send_day_of_month INTEGER,
    include_trend BOOLEAN DEFAULT TRUE,
    trend_period_days INTEGER DEFAULT 7,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- 3. 索引 (Indexes)
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_ods_issues_project ON warehouse.ods_issues(project_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_status ON warehouse.ods_issues(status_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_assigned ON warehouse.ods_issues(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_ods_journals_issue ON warehouse.ods_journals(issue_id);


-- =====================================================
-- 4. 授权 (Grants)
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;


-- =====================================================
-- 5. 注释 (Comments)
-- =====================================================

COMMENT ON SCHEMA warehouse IS 'Redmine MCP data warehouse schema';

COMMENT ON TABLE warehouse.ods_projects IS 'ODS projects base table';
COMMENT ON TABLE warehouse.ods_issues IS 'ODS issues base table';
COMMENT ON TABLE warehouse.ods_journals IS 'ODS issue journals';
COMMENT ON TABLE warehouse.ods_journal_details IS 'ODS journal details';
COMMENT ON TABLE warehouse.ods_users IS 'ODS users base table';
COMMENT ON TABLE warehouse.ods_groups IS 'ODS groups';
COMMENT ON TABLE warehouse.ods_group_users IS 'ODS group members';
COMMENT ON TABLE warehouse.ods_project_memberships IS 'ODS project memberships';
COMMENT ON TABLE warehouse.ods_project_member_roles IS 'ODS project member roles';
COMMENT ON TABLE warehouse.ods_roles IS 'ODS roles';
COMMENT ON TABLE warehouse.ods_trackers IS 'ODS trackers';
COMMENT ON TABLE warehouse.ods_issue_statuses IS 'ODS issue statuses';

COMMENT ON TABLE warehouse.dim_role_category IS 'DIM role categories';
COMMENT ON TABLE warehouse.dim_date IS 'DIM date dimension';
COMMENT ON TABLE warehouse.dim_project IS 'DIM projects';
COMMENT ON TABLE warehouse.dim_user IS 'DIM users';
COMMENT ON TABLE warehouse.dim_issue IS 'DIM issues';

COMMENT ON TABLE warehouse.dwd_issue_daily_snapshot IS 'DWD issue daily snapshots';
COMMENT ON TABLE warehouse.dwd_user_project_role IS 'DWD user project roles';

COMMENT ON TABLE warehouse.dws_project_daily_summary IS 'DWS project daily summaries';
COMMENT ON TABLE warehouse.dws_issue_contributors IS 'DWS issue contributors';
COMMENT ON TABLE warehouse.dws_issue_contributor_summary IS 'DWS issue contributor summary';
COMMENT ON TABLE warehouse.dws_project_role_distribution IS 'DWS project role distribution';
COMMENT ON TABLE warehouse.dws_user_monthly_workload IS 'DWS user monthly workload';

COMMENT ON TABLE warehouse.ads_contributor_report IS 'ADS contributor analysis';
COMMENT ON TABLE warehouse.ads_project_health_report IS 'ADS project health';
COMMENT ON TABLE warehouse.ads_team_performance_report IS 'ADS team performance';
COMMENT ON TABLE warehouse.ads_user_workload_report IS 'ADS user workload';
COMMENT ON TABLE warehouse.ads_user_subscriptions IS 'ADS user subscriptions';


-- =====================================================
-- End of File
-- =====================================================


-- =====================================================
-- 3. 存储函数 (Storage Functions)
-- =====================================================

-- 3.1 项目每日汇总刷新函数
CREATE OR REPLACE FUNCTION warehouse.refresh_daily_summary(
    p_project_id INTEGER,
    p_snapshot_date DATE
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.dws_project_daily_summary (
        project_id, snapshot_date,
        total_issues, new_issues, closed_issues,
        status_new, status_in_progress, status_resolved, status_closed,
        priority_immediate, priority_urgent, priority_high, priority_normal, priority_low
    )
    SELECT 
        project_id,
        snapshot_date,
        COUNT(*) as total_issues,
        SUM(CASE WHEN is_new THEN 1 ELSE 0 END) as new_issues,
        SUM(CASE WHEN is_closed THEN 1 ELSE 0 END) as closed_issues,
        SUM(CASE WHEN status_name = '新建' THEN 1 ELSE 0 END) as status_new,
        SUM(CASE WHEN status_name = '进行中' THEN 1 ELSE 0 END) as status_in_progress,
        SUM(CASE WHEN status_name = '已解决' THEN 1 ELSE 0 END) as status_resolved,
        SUM(CASE WHEN status_name = '已关闭' THEN 1 ELSE 0 END) as status_closed,
        SUM(CASE WHEN priority_name = '立刻' THEN 1 ELSE 0 END) as priority_immediate,
        SUM(CASE WHEN priority_name = '紧急' THEN 1 ELSE 0 END) as priority_urgent,
        SUM(CASE WHEN priority_name = '高' THEN 1 ELSE 0 END) as priority_high,
        SUM(CASE WHEN priority_name = '普通' THEN 1 ELSE 0 END) as priority_normal,
        SUM(CASE WHEN priority_name = '低' THEN 1 ELSE 0 END) as priority_low
    FROM warehouse.dwd_issue_daily_snapshot
    WHERE project_id = p_project_id AND snapshot_date = p_snapshot_date
    GROUP BY project_id, snapshot_date
    ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
        total_issues = EXCLUDED.total_issues,
        new_issues = EXCLUDED.new_issues,
        closed_issues = EXCLUDED.closed_issues,
        status_new = EXCLUDED.status_new,
        status_in_progress = EXCLUDED.status_in_progress,
        status_resolved = EXCLUDED.status_resolved,
        status_closed = EXCLUDED.status_closed,
        priority_immediate = EXCLUDED.priority_immediate,
        priority_urgent = EXCLUDED.priority_urgent,
        priority_high = EXCLUDED.priority_high,
        priority_normal = EXCLUDED.priority_normal,
        priority_low = EXCLUDED.priority_low;
END;
$$ LANGUAGE plpgsql;

-- 3.2 Issue 贡献者汇总刷新函数
CREATE OR REPLACE FUNCTION warehouse.refresh_contributor_summary(
    p_issue_id INTEGER,
    p_project_id INTEGER
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.dws_issue_contributor_summary (
        issue_id, project_id,
        manager_count, implementation_count, developer_count,
        tester_count, other_count, total_contributors, total_journals
    )
    SELECT
        issue_id,
        project_id,
        SUM(CASE WHEN role_category = 'manager' THEN 1 ELSE 0 END) as manager_count,
        SUM(CASE WHEN role_category = 'implementation' THEN 1 ELSE 0 END) as implementation_count,
        SUM(CASE WHEN role_category = 'developer' THEN 1 ELSE 0 END) as developer_count,
        SUM(CASE WHEN role_category = 'tester' THEN 1 ELSE 0 END) as tester_count,
        SUM(CASE WHEN role_category = 'other' THEN 1 ELSE 0 END) as other_count,
        COUNT(DISTINCT user_id) as total_contributors,
        SUM(journal_count) as total_journals
    FROM warehouse.dws_issue_contributors
    WHERE issue_id = p_issue_id AND project_id = p_project_id
    GROUP BY issue_id, project_id
    ON CONFLICT (issue_id) DO UPDATE SET
        project_id = EXCLUDED.project_id,
        manager_count = EXCLUDED.manager_count,
        implementation_count = EXCLUDED.implementation_count,
        developer_count = EXCLUDED.developer_count,
        tester_count = EXCLUDED.tester_count,
        other_count = EXCLUDED.other_count,
        total_contributors = EXCLUDED.total_contributors,
        total_journals = EXCLUDED.total_journals;
END;
$$ LANGUAGE plpgsql;

-- 3.3 项目角色分布刷新函数
CREATE OR REPLACE FUNCTION warehouse.refresh_project_role_distribution(
    p_project_id INTEGER,
    p_snapshot_date DATE
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.dws_project_role_distribution (
        project_id, snapshot_date,
        manager_count, implementation_count, developer_count,
        tester_count, other_count, total_members
    )
    SELECT 
        project_id,
        p_snapshot_date as snapshot_date,
        SUM(CASE WHEN role_category = 'manager' THEN 1 ELSE 0 END) as manager_count,
        SUM(CASE WHEN role_category = 'implementation' THEN 1 ELSE 0 END) as implementation_count,
        SUM(CASE WHEN role_category = 'developer' THEN 1 ELSE 0 END) as developer_count,
        SUM(CASE WHEN role_category = 'tester' THEN 1 ELSE 0 END) as tester_count,
        SUM(CASE WHEN role_category = 'other' THEN 1 ELSE 0 END) as other_count,
        COUNT(DISTINCT user_id) as total_members
    FROM warehouse.dwd_user_project_role
    WHERE project_id = p_project_id
    GROUP BY project_id
    ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
        manager_count = EXCLUDED.manager_count,
        implementation_count = EXCLUDED.implementation_count,
        developer_count = EXCLUDED.developer_count,
        tester_count = EXCLUDED.tester_count,
        other_count = EXCLUDED.other_count,
        total_members = EXCLUDED.total_members;
END;
$$ LANGUAGE plpgsql;

-- 3.4 用户工作量刷新函数
CREATE OR REPLACE FUNCTION warehouse.refresh_user_workload(
    p_user_id INTEGER,
    p_user_name VARCHAR,
    p_year_month VARCHAR,
    p_project_id INTEGER
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.dws_user_monthly_workload (
        user_id, year_month,
        total_issues, total_journals,
        as_manager, as_implementation, as_developer, as_tester
    )
    SELECT 
        p_user_id,
        p_year_month,
        COUNT(DISTINCT ic.issue_id) as total_issues,
        SUM(ic.journal_count) as total_journals,
        SUM(CASE WHEN ic.role_category = 'manager' THEN 1 ELSE 0 END) as as_manager,
        SUM(CASE WHEN ic.role_category = 'implementation' THEN 1 ELSE 0 END) as as_implementation,
        SUM(CASE WHEN ic.role_category = 'developer' THEN 1 ELSE 0 END) as as_developer,
        SUM(CASE WHEN ic.role_category = 'tester' THEN 1 ELSE 0 END) as as_tester
    FROM warehouse.dws_issue_contributors ic
    WHERE ic.user_id = p_user_id 
      AND ic.project_id = p_project_id
    GROUP BY ic.user_id
    ON CONFLICT (user_id, year_month) DO UPDATE SET
        total_issues = EXCLUDED.total_issues,
        total_journals = EXCLUDED.total_journals,
        as_manager = EXCLUDED.as_manager,
        as_implementation = EXCLUDED.as_implementation,
        as_developer = EXCLUDED.as_developer,
        as_tester = EXCLUDED.as_tester;
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- 4. 视图 (Views)
-- =====================================================

-- 4.1 贡献者排行榜视图
CREATE OR REPLACE VIEW warehouse.v_ads_contributor_ranking AS
SELECT
    project_id,
    year_month,
    user_id,
    user_name,
    role_category,
    total_issues,
    total_journals,
    resolved_issues,
    RANK() OVER (PARTITION BY project_id, year_month 
                 ORDER BY total_issues DESC) AS issue_rank,
    RANK() OVER (PARTITION BY project_id, year_month 
                 ORDER BY total_journals DESC) AS journal_rank
FROM warehouse.ads_contributor_report;

-- 4.2 项目维度当前视图
CREATE OR REPLACE VIEW warehouse.v_dim_project_current AS
SELECT 
    project_id,
    project_name,
    project_identifier,
    parent_project_id,
    project_level,
    project_path,
    is_active
FROM warehouse.dim_project;

-- 4.3 用户维度当前视图
CREATE OR REPLACE VIEW warehouse.v_dim_user_current AS
SELECT 
    user_id,
    user_name,
    login_name,
    email,
    is_active
FROM warehouse.dim_user;

-- 4.4 Issue 维度当前视图
CREATE OR REPLACE VIEW warehouse.v_dim_issue_current AS
SELECT 
    issue_id,
    issue_subject,
    tracker_name,
    status_name,
    priority_name,
    is_closed
FROM warehouse.dim_issue;

-- 4.5 项目健康度最新视图
CREATE OR REPLACE VIEW warehouse.v_ads_project_health_latest AS
SELECT DISTINCT ON (project_id)
    project_id,
    project_name,
    snapshot_date,
    health_score,
    risk_level,
    total_issues,
    open_issues,
    avg_age_days
FROM warehouse.ads_project_health_report
ORDER BY project_id, snapshot_date DESC;

-- 4.6 用户工作量月度汇总视图
CREATE OR REPLACE VIEW warehouse.v_ads_user_workload_monthly AS
SELECT
    user_id,
    user_name,
    year_month,
    total_projects,
    total_issues,
    total_journals,
    resolved_issues,
    issues_per_day,
    rank_in_month
FROM warehouse.ads_user_workload_report
ORDER BY year_month DESC, rank_in_month;


-- =====================================================
-- 5. 最终授权 (Final Grants)
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA warehouse TO redmine_warehouse;


-- =====================================================
-- End of File
-- =====================================================
