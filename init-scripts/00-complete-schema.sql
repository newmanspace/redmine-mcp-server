-- =====================================================
-- Redmine MCP Server - Database Schema
-- 完整的数据库表结构定义
-- =====================================================

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建模式
CREATE SCHEMA IF NOT EXISTS warehouse;
SET search_path TO warehouse, public;

-- =====================================================
-- 1. DWD Layer - Data Warehouse Detail (明细数据层)
-- =====================================================

-- Issue 每日快照表
CREATE TABLE IF NOT EXISTS warehouse.issue_daily_snapshot (
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
    CONSTRAINT uk_issue_snapshot UNIQUE (issue_id, snapshot_date)
);

-- 项目每日汇总表
CREATE TABLE IF NOT EXISTS warehouse.project_daily_summary (
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
    CONSTRAINT uk_project_summary UNIQUE (project_id, snapshot_date)
);

-- Issue 贡献者明细表
CREATE TABLE IF NOT EXISTS warehouse.issue_contributors (
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
    CONSTRAINT uk_issue_contributor UNIQUE (issue_id, user_id)
);

-- Issue 贡献者汇总表
CREATE TABLE IF NOT EXISTS warehouse.issue_contributor_summary (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    manager_count INTEGER DEFAULT 0,
    implementation_count INTEGER DEFAULT 0,
    developer_count INTEGER DEFAULT 0,
    tester_count INTEGER DEFAULT 0,
    other_count INTEGER DEFAULT 0,
    total_contributors INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_issue_contributor_summary UNIQUE (issue_id)
);

-- 用户项目角色表
CREATE TABLE IF NOT EXISTS warehouse.user_project_role (
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
    CONSTRAINT uk_user_project_role UNIQUE (project_id, user_id)
);

-- 项目角色分布表
CREATE TABLE IF NOT EXISTS warehouse.project_role_distribution (
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
    CONSTRAINT uk_project_role_dist UNIQUE (project_id, snapshot_date)
);

-- 用户工作量统计表
CREATE TABLE IF NOT EXISTS warehouse.user_workload (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    year_month TEXT NOT NULL,
    total_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    as_manager INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer INTEGER DEFAULT 0,
    as_tester INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_user_workload UNIQUE (user_id, year_month)
);

-- =====================================================
-- 2. ODS Layer - Operational Data Store (原始数据层)
-- =====================================================

-- 项目表
CREATE TABLE IF NOT EXISTS warehouse.ods_projects (
    project_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    identifier VARCHAR(100) NOT NULL,
    description TEXT,
    status INTEGER,
    created_on TIMESTAMP,
    updated_on TIMESTAMP,
    parent_project_id INTEGER
);

-- Issue 表
CREATE TABLE IF NOT EXISTS warehouse.ods_issues (
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

-- Journal 表
CREATE TABLE IF NOT EXISTS warehouse.ods_journals (
    journal_id INTEGER PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    notes TEXT,
    created_on TIMESTAMP
);

-- Journal Detail 表
CREATE TABLE IF NOT EXISTS warehouse.ods_journal_details (
    detail_id SERIAL PRIMARY KEY,
    journal_id INTEGER NOT NULL,
    property VARCHAR(50),
    name VARCHAR(100),
    old_value TEXT,
    new_value TEXT
);

-- 用户表
CREATE TABLE IF NOT EXISTS warehouse.ods_users (
    user_id INTEGER PRIMARY KEY,
    login VARCHAR(100) NOT NULL,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    mail VARCHAR(255),
    status INTEGER,
    created_on TIMESTAMP,
    last_login_on TIMESTAMP
);

-- 组表
CREATE TABLE IF NOT EXISTS warehouse.ods_groups (
    group_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_builtin INTEGER DEFAULT 0
);

-- 组成员关系表
CREATE TABLE IF NOT EXISTS warehouse.ods_group_users (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (group_id, user_id)
);

-- 项目成员表
CREATE TABLE IF NOT EXISTS warehouse.ods_project_memberships (
    membership_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER,
    group_id INTEGER
);

-- 成员角色表
CREATE TABLE IF NOT EXISTS warehouse.ods_project_member_roles (
    membership_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (membership_id, role_id)
);

-- 角色表
CREATE TABLE IF NOT EXISTS warehouse.ods_roles (
    role_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_builtin INTEGER DEFAULT 0,
    permissions TEXT
);

-- Tracker 表
CREATE TABLE IF NOT EXISTS warehouse.ods_trackers (
    tracker_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_in_chlog INTEGER DEFAULT 0,
    is_in_roadmap INTEGER DEFAULT 0,
    position INTEGER
);

-- Issue 状态表
CREATE TABLE IF NOT EXISTS warehouse.ods_issue_statuses (
    status_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_closed INTEGER DEFAULT 0,
    is_default INTEGER DEFAULT 0,
    position INTEGER
);

-- =====================================================
-- 3. DIM Layer - Dimension Tables (维度表)
-- =====================================================

-- 角色分类维度表
CREATE TABLE IF NOT EXISTS warehouse.dim_role_category (
    role_id INTEGER PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    priority INTEGER NOT NULL,
    description VARCHAR(255)
);

-- 日期维度表
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
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

-- 项目维度表
CREATE TABLE IF NOT EXISTS warehouse.dim_project (
    project_id INTEGER PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    project_identifier VARCHAR(100),
    parent_project_id INTEGER,
    project_level INTEGER DEFAULT 1,
    project_path TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 用户维度表
CREATE TABLE IF NOT EXISTS warehouse.dim_user (
    user_id INTEGER PRIMARY KEY,
    user_name VARCHAR(200) NOT NULL,
    login_name VARCHAR(100),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

-- Issue 维度表
CREATE TABLE IF NOT EXISTS warehouse.dim_issue (
    issue_id INTEGER PRIMARY KEY,
    issue_subject TEXT,
    tracker_name VARCHAR(100),
    status_name VARCHAR(100),
    priority_name VARCHAR(100),
    is_closed BOOLEAN DEFAULT FALSE
);

-- =====================================================
-- 4. DWS Layer - Data Warehouse Summary (汇总数据层)
-- =====================================================

-- 项目每日汇总表
CREATE TABLE IF NOT EXISTS warehouse.dws_project_daily_summary (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    snapshot_date DATE NOT NULL,
    total_issues INTEGER DEFAULT 0,
    new_issues INTEGER DEFAULT 0,
    closed_issues INTEGER DEFAULT 0,
    updated_issues INTEGER DEFAULT 0,
    status_new INTEGER DEFAULT 0,
    status_in_progress INTEGER DEFAULT 0,
    status_resolved INTEGER DEFAULT 0,
    status_closed INTEGER DEFAULT 0,
    status_feedback INTEGER DEFAULT 0,
    priority_immediate INTEGER DEFAULT 0,
    priority_urgent INTEGER DEFAULT 0,
    priority_high INTEGER DEFAULT 0,
    priority_normal INTEGER DEFAULT 0,
    priority_low INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_dws_project_summary UNIQUE (project_id, snapshot_date)
);

-- Issue 贡献者明细表
CREATE TABLE IF NOT EXISTS warehouse.dws_issue_contributors (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(200),
    highest_role_id INTEGER,
    highest_role_name VARCHAR(100),
    role_category VARCHAR(20),
    journal_count INTEGER DEFAULT 0,
    first_contribution TIMESTAMP,
    last_contribution TIMESTAMP,
    status_change_count INTEGER DEFAULT 0,
    note_count INTEGER DEFAULT 0,
    assigned_change_count INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_dws_issue_contributor UNIQUE (issue_id, user_id)
);

-- Issue 贡献者汇总表
CREATE TABLE IF NOT EXISTS warehouse.dws_issue_contributor_summary (
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

-- 用户项目角色表
CREATE TABLE IF NOT EXISTS warehouse.dwd_user_project_role (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    highest_role_id INTEGER,
    highest_role_name VARCHAR(100),
    role_category VARCHAR(20),
    role_priority INTEGER,
    all_role_ids VARCHAR(200),
    is_direct_member BOOLEAN DEFAULT TRUE,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id)
);

-- 项目角色分布表
CREATE TABLE IF NOT EXISTS warehouse.dws_project_role_distribution (
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
    CONSTRAINT uk_dws_project_role_dist UNIQUE (project_id, snapshot_date)
);

-- 用户月度工作量统计表
CREATE TABLE IF NOT EXISTS warehouse.dws_user_monthly_workload (
    user_id INTEGER NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    total_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    as_manager INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer INTEGER DEFAULT 0,
    as_tester INTEGER DEFAULT 0,
    resolved_issues INTEGER DEFAULT 0,
    verified_issues INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, year_month)
);

-- =====================================================
-- 5. ADS Layer - Application Data Store (应用数据层)
-- =====================================================

-- 贡献者分析报表
CREATE TABLE IF NOT EXISTS warehouse.ads_contributor_report (
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

-- 项目健康度报表
CREATE TABLE IF NOT EXISTS warehouse.ads_project_health_report (
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

-- 用户工作量报表
CREATE TABLE IF NOT EXISTS warehouse.ads_user_workload_report (
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

-- 团队绩效报表
CREATE TABLE IF NOT EXISTS warehouse.ads_team_performance_report (
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

-- 用户项目订阅表
CREATE TABLE IF NOT EXISTS warehouse.ads_user_subscriptions (
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
-- 6. Indexes (索引)
-- =====================================================

-- DWD 层索引
CREATE INDEX IF NOT EXISTS idx_issue_snapshot_date ON warehouse.issue_daily_snapshot(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_issue_project_date ON warehouse.issue_daily_snapshot(project_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_issue_status_name ON warehouse.issue_daily_snapshot(status_name);
CREATE INDEX IF NOT EXISTS idx_issue_priority_name ON warehouse.issue_daily_snapshot(priority_name);
CREATE INDEX IF NOT EXISTS idx_project_summary_date ON warehouse.project_daily_summary(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_issue_contributors_issue ON warehouse.issue_contributors(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_contributors_user ON warehouse.issue_contributors(user_id);
CREATE INDEX IF NOT EXISTS idx_issue_contributors_category ON warehouse.issue_contributors(role_category);
CREATE INDEX IF NOT EXISTS idx_user_project_role_project ON warehouse.user_project_role(project_id);
CREATE INDEX IF NOT EXISTS idx_user_project_role_user ON warehouse.user_project_role(user_id);
CREATE INDEX IF NOT EXISTS idx_project_role_dist_date ON warehouse.project_role_distribution(snapshot_date);

-- ODS 层索引
CREATE INDEX IF NOT EXISTS idx_ods_issues_project ON warehouse.ods_issues(project_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_status ON warehouse.ods_issues(status_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_tracker ON warehouse.ods_issues(tracker_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_author ON warehouse.ods_issues(author_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_assigned ON warehouse.ods_issues(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_ods_issues_updated ON warehouse.ods_issues(updated_on);
CREATE INDEX IF NOT EXISTS idx_ods_journals_issue ON warehouse.ods_journals(issue_id);
CREATE INDEX IF NOT EXISTS idx_ods_journals_user ON warehouse.ods_journals(user_id);

-- DWS 层索引
CREATE INDEX IF NOT EXISTS idx_dws_project_summary_date ON warehouse.dws_project_daily_summary(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_dws_issue_contributors_issue ON warehouse.dws_issue_contributors(issue_id);
CREATE INDEX IF NOT EXISTS idx_dws_issue_contributors_user ON warehouse.dws_issue_contributors(user_id);
CREATE INDEX IF NOT EXISTS idx_dws_issue_contributors_category ON warehouse.dws_issue_contributors(role_category);
CREATE INDEX IF NOT EXISTS idx_dws_project_role_distribution_date ON warehouse.dws_project_role_distribution(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_dws_user_monthly_workload_user ON warehouse.dws_user_monthly_workload(user_id);
CREATE INDEX IF NOT EXISTS idx_dws_user_monthly_workload_month ON warehouse.dws_user_monthly_workload(year_month);

-- ADS 层索引
CREATE INDEX IF NOT EXISTS idx_ads_contributor_project ON warehouse.ads_contributor_report(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_contributor_month ON warehouse.ads_contributor_report(year_month);
CREATE INDEX IF NOT EXISTS idx_ads_contributor_user ON warehouse.ads_contributor_report(user_id);
CREATE INDEX IF NOT EXISTS idx_ads_project_health_project ON warehouse.ads_project_health_report(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_project_health_date ON warehouse.ads_project_health_report(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_ads_user_workload_user ON warehouse.ads_user_workload_report(user_id);
CREATE INDEX IF NOT EXISTS idx_ads_user_workload_month ON warehouse.ads_user_workload_report(year_month);
CREATE INDEX IF NOT EXISTS idx_ads_team_performance_project ON warehouse.ads_team_performance_report(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_team_performance_month ON warehouse.ads_team_performance_report(year_month);

-- 订阅表索引
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user ON warehouse.ads_user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user_email ON warehouse.ads_user_subscriptions(user_email);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_project ON warehouse.ads_user_subscriptions(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_channel ON warehouse.ads_user_subscriptions(channel);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_language ON warehouse.ads_user_subscriptions(language);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_enabled ON warehouse.ads_user_subscriptions(enabled);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user_project ON warehouse.ads_user_subscriptions(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_report_type_language_enabled ON warehouse.ads_user_subscriptions(report_type, language, enabled);
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_send_time_enabled ON warehouse.ads_user_subscriptions(send_time, enabled);

-- =====================================================
-- 7. Grants (授权)
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;

-- =====================================================
-- 8. Comments (表注释)
-- =====================================================

COMMENT ON SCHEMA warehouse IS 'Redmine MCP 数据仓库模式';

-- DWD 层注释
COMMENT ON TABLE warehouse.issue_daily_snapshot IS 'DWD-Issue 每日快照表 - 记录每个 Issue 在每日的状态';
COMMENT ON TABLE warehouse.project_daily_summary IS 'DWD-项目每日汇总表 - 快速查询项目统计';
COMMENT ON TABLE warehouse.issue_contributors IS 'DWD-Issue 贡献者明细表 - 记录每个 Issue 的所有贡献者及其活动';
COMMENT ON TABLE warehouse.issue_contributor_summary IS 'DWD-Issue 贡献者汇总表 - 每个 Issue 的贡献者角色分布';
COMMENT ON TABLE warehouse.user_project_role IS 'DWD-用户项目角色表 - 记录每个用户在项目中的最高角色';
COMMENT ON TABLE warehouse.project_role_distribution IS 'DWD-项目角色分布表 - 项目每日角色分布统计';
COMMENT ON TABLE warehouse.user_workload IS 'DWD-用户工作量统计表 - 按用户和年月统计工作量';

-- ODS 层注释
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

-- DIM 层注释
COMMENT ON TABLE warehouse.dim_role_category IS 'DIM-角色分类维度表';
COMMENT ON TABLE warehouse.dim_date IS 'DIM-日期维度表 (2010-2030)';
COMMENT ON TABLE warehouse.dim_project IS 'DIM-项目维度表';
COMMENT ON TABLE warehouse.dim_user IS 'DIM-用户维度表';
COMMENT ON TABLE warehouse.dim_issue IS 'DIM-Issue 维度表';

-- DWS 层注释
COMMENT ON TABLE warehouse.dws_project_daily_summary IS 'DWS-项目每日汇总表 - 快速查询项目统计';
COMMENT ON TABLE warehouse.dws_issue_contributors IS 'DWS-Issue 贡献者明细表 - 记录每个 Issue 的所有贡献者及其活动';
COMMENT ON TABLE warehouse.dws_issue_contributor_summary IS 'DWS-Issue 贡献者汇总表 - 每个 Issue 的贡献者角色分布';
COMMENT ON TABLE warehouse.dwd_user_project_role IS 'DWD-用户项目角色表 - 记录每个用户在项目中的最高角色';
COMMENT ON TABLE warehouse.dws_project_role_distribution IS 'DWS-项目角色分布表 - 项目每日角色分布统计';
COMMENT ON TABLE warehouse.dws_user_monthly_workload IS 'DWS-用户工作量统计表 - 按用户和年月统计工作量';

-- ADS 层注释
COMMENT ON TABLE warehouse.ads_contributor_report IS 'ADS-贡献者分析报表（按月）';
COMMENT ON TABLE warehouse.ads_project_health_report IS 'ADS-项目健康度报表（按日）';
COMMENT ON TABLE warehouse.ads_user_workload_report IS 'ADS-用户工作量报表（按月）';
COMMENT ON TABLE warehouse.ads_team_performance_report IS 'ADS-团队绩效报表（按月）';
COMMENT ON TABLE warehouse.ads_user_subscriptions IS 'ADS-用户项目订阅表 - 存储用户对项目的订阅配置，支持日报/周报/月报';
