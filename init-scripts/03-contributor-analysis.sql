-- Redmine MCP 数仓扩展 - 贡献者分析
-- 版本：1.0
-- 创建日期：2026-02-27

-- Issue 贡献者分析表
-- 记录每个 Issue 的所有贡献者及其角色
CREATE TABLE IF NOT EXISTS warehouse.issue_contributors (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(200),
    highest_role_id INTEGER,
    highest_role_name VARCHAR(100),
    role_category VARCHAR(20),  -- manager/implementation/developer/tester/other
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
-- 每个 Issue 的贡献者角色分布汇总
CREATE TABLE IF NOT EXISTS warehouse.issue_contributor_summary (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL UNIQUE,
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
-- 记录每个用户在项目中的最高角色
CREATE TABLE IF NOT EXISTS warehouse.user_project_role (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    highest_role_id INTEGER,
    highest_role_name VARCHAR(100),
    role_category VARCHAR(20),
    role_priority INTEGER,
    all_role_ids VARCHAR(200),
    is_direct_member BOOLEAN DEFAULT TRUE,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_user_project_role UNIQUE (project_id, user_id)
);

-- 项目角色分布表
-- 项目每日角色分布统计
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
-- 按用户和年月统计工作量
CREATE TABLE IF NOT EXISTS warehouse.user_workload (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_name VARCHAR(200),
    year_month VARCHAR(7) NOT NULL,  -- YYYY-MM format
    project_id INTEGER NOT NULL,
    total_issues INTEGER DEFAULT 0,
    total_journals INTEGER DEFAULT 0,
    as_manager INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer INTEGER DEFAULT 0,
    as_tester INTEGER DEFAULT 0,
    resolved_issues INTEGER DEFAULT 0,
    verified_issues INTEGER DEFAULT 0,
    created_at_snapshot TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_user_workload UNIQUE (user_id, year_month, project_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_contributors_issue ON warehouse.issue_contributors(issue_id);
CREATE INDEX IF NOT EXISTS idx_contributors_user ON warehouse.issue_contributors(user_id);
CREATE INDEX IF NOT EXISTS idx_contributors_category ON warehouse.issue_contributors(role_category);
CREATE INDEX IF NOT EXISTS idx_contributors_project ON warehouse.issue_contributors(project_id);
CREATE INDEX IF NOT EXISTS idx_user_role_project ON warehouse.user_project_role(project_id);
CREATE INDEX IF NOT EXISTS idx_user_role_user ON warehouse.user_project_role(user_id);
CREATE INDEX IF NOT EXISTS idx_project_role_dist_date ON warehouse.project_role_distribution(project_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_user_workload_user ON warehouse.user_workload(user_id);
CREATE INDEX IF NOT EXISTS idx_user_workload_month ON warehouse.user_workload(year_month);
CREATE INDEX IF NOT EXISTS idx_user_workload_project ON warehouse.user_workload(project_id);

-- 授予权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;

-- 刷新贡献者汇总的函数
CREATE OR REPLACE FUNCTION warehouse.refresh_contributor_summary(p_issue_id INTEGER, p_project_id INTEGER)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.issue_contributor_summary (
        issue_id, project_id,
        manager_count, implementation_count, developer_count, tester_count, other_count,
        total_contributors, total_journals
    )
    SELECT 
        p_issue_id, p_project_id,
        SUM(CASE WHEN role_category='manager' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category='implementation' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category='developer' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category='tester' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category NOT IN ('manager','implementation','developer','tester') THEN 1 ELSE 0 END),
        COUNT(*),
        SUM(journal_count)
    FROM warehouse.issue_contributors
    WHERE issue_id = p_issue_id
    ON CONFLICT (issue_id) DO UPDATE SET
        manager_count = EXCLUDED.manager_count,
        implementation_count = EXCLUDED.implementation_count,
        developer_count = EXCLUDED.developer_count,
        tester_count = EXCLUDED.tester_count,
        other_count = EXCLUDED.other_count,
        total_contributors = EXCLUDED.total_contributors,
        total_journals = EXCLUDED.total_journals,
        created_at_snapshot = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- 刷新项目角色分布的函数
CREATE OR REPLACE FUNCTION warehouse.refresh_project_role_distribution(p_project_id INTEGER, p_snapshot_date DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.project_role_distribution (
        project_id, snapshot_date,
        manager_count, implementation_count, developer_count, tester_count, other_count, total_members
    )
    SELECT 
        p_project_id, p_snapshot_date,
        SUM(CASE WHEN role_category='manager' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category='implementation' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category='developer' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category='tester' THEN 1 ELSE 0 END),
        SUM(CASE WHEN role_category NOT IN ('manager','implementation','developer','tester') THEN 1 ELSE 0 END),
        COUNT(*)
    FROM warehouse.user_project_role
    WHERE project_id = p_project_id
    ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
        manager_count = EXCLUDED.manager_count,
        implementation_count = EXCLUDED.implementation_count,
        developer_count = EXCLUDED.developer_count,
        tester_count = EXCLUDED.tester_count,
        other_count = EXCLUDED.other_count,
        total_members = EXCLUDED.total_members,
        created_at_snapshot = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- 刷新用户工作量的函数
CREATE OR REPLACE FUNCTION warehouse.refresh_user_workload(
    p_user_id INTEGER,
    p_user_name VARCHAR(200),
    p_year_month VARCHAR(7),
    p_project_id INTEGER
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.user_workload (
        user_id, user_name, year_month, project_id,
        total_issues, total_journals,
        as_manager, as_implementation, as_developer, as_tester,
        resolved_issues, verified_issues
    )
    SELECT 
        p_user_id, p_user_name, p_year_month, p_project_id,
        COUNT(DISTINCT ic.issue_id),
        SUM(ic.journal_count),
        SUM(CASE WHEN ic.role_category='manager' THEN 1 ELSE 0 END),
        SUM(CASE WHEN ic.role_category='implementation' THEN 1 ELSE 0 END),
        SUM(CASE WHEN ic.role_category='developer' THEN 1 ELSE 0 END),
        SUM(CASE WHEN ic.role_category='tester' THEN 1 ELSE 0 END),
        SUM(ic.status_change_count),
        0  -- verified_issues would need additional logic
    FROM warehouse.issue_contributors ic
    WHERE ic.user_id = p_user_id 
      AND ic.project_id = p_project_id
    ON CONFLICT (user_id, year_month, project_id) DO UPDATE SET
        total_issues = EXCLUDED.total_issues,
        total_journals = EXCLUDED.total_journals,
        as_manager = EXCLUDED.as_manager,
        as_implementation = EXCLUDED.as_implementation,
        as_developer = EXCLUDED.as_developer,
        as_tester = EXCLUDED.as_tester,
        resolved_issues = EXCLUDED.resolved_issues,
        created_at_snapshot = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE warehouse.issue_contributors IS 'Issue 贡献者分析表 - 记录每个 Issue 的所有贡献者及其角色';
COMMENT ON TABLE warehouse.issue_contributor_summary IS 'Issue 贡献者汇总表 - 每个 Issue 的贡献者角色分布';
COMMENT ON TABLE warehouse.user_project_role IS '用户项目角色表 - 记录每个用户在项目中的最高角色';
COMMENT ON TABLE warehouse.project_role_distribution IS '项目角色分布表 - 项目每日角色分布统计';
COMMENT ON TABLE warehouse.user_workload IS '用户工作量统计表 - 按用户和年月统计工作量';
