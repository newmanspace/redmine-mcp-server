-- =====================================================
-- Redmine MCP Server - Initialization Data
-- 初始化数据和函数
-- =====================================================

SET timezone = 'Asia/Shanghai';
SET search_path TO warehouse, public;

-- =====================================================
-- 1. 基础数据初始化
-- =====================================================

-- 插入角色分类基础数据
INSERT INTO warehouse.dim_role_category (role_id, role_name, category, priority, description)
VALUES
    (3, '管理人员', 'manager', 1, '项目经理、管理员'),
    (8, '实施人员', 'implementation', 2, '实施顾问、部署人员'),
    (4, '开发人员', 'developer', 3, '开发工程师'),
    (7, '测试人员', 'tester', 4, '测试工程师'),
    (5, '报告人员', 'reporter', 5, '报告查看者'),
    (6, '查询人员', 'viewer', 6, '只读权限')
ON CONFLICT (role_id) DO NOTHING;

-- =====================================================
-- 2. 存储函数
-- =====================================================

-- 刷新项目每日汇总函数
CREATE OR REPLACE FUNCTION warehouse.refresh_dws_project_daily_summary(
    p_project_id INTEGER,
    p_snapshot_date DATE
)
RETURNS VOID AS $$
BEGIN
    -- 从 DWD 层汇总数据到 DWS 层
    INSERT INTO warehouse.dws_project_daily_summary (
        project_id, snapshot_date,
        total_issues, new_issues, closed_issues, updated_issues,
        status_new, status_in_progress, status_resolved, status_closed, status_feedback,
        priority_immediate, priority_urgent, priority_high, priority_normal, priority_low,
        created_at_snapshot
    )
    SELECT
        project_id,
        snapshot_date,
        SUM(total_issues) as total_issues,
        SUM(new_issues) as new_issues,
        SUM(closed_issues) as closed_issues,
        SUM(updated_issues) as updated_issues,
        SUM(status_new) as status_new,
        SUM(status_in_progress) as status_in_progress,
        SUM(status_resolved) as status_resolved,
        SUM(status_closed) as status_closed,
        SUM(status_feedback) as status_feedback,
        SUM(priority_immediate) as priority_immediate,
        SUM(priority_urgent) as priority_urgent,
        SUM(priority_high) as priority_high,
        SUM(priority_normal) as priority_normal,
        SUM(priority_low) as priority_low,
        CURRENT_TIMESTAMP as created_at_snapshot
    FROM warehouse.project_daily_summary
    WHERE project_id = p_project_id
      AND snapshot_date = p_snapshot_date
    GROUP BY project_id, snapshot_date
    ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
        total_issues = EXCLUDED.total_issues,
        new_issues = EXCLUDED.new_issues,
        closed_issues = EXCLUDED.closed_issues,
        updated_issues = EXCLUDED.updated_issues,
        status_new = EXCLUDED.status_new,
        status_in_progress = EXCLUDED.status_in_progress,
        status_resolved = EXCLUDED.status_resolved,
        status_closed = EXCLUDED.status_closed,
        status_feedback = EXCLUDED.status_feedback,
        priority_immediate = EXCLUDED.priority_immediate,
        priority_urgent = EXCLUDED.priority_urgent,
        priority_high = EXCLUDED.priority_high,
        priority_normal = EXCLUDED.priority_normal,
        priority_low = EXCLUDED.priority_low,
        created_at_snapshot = EXCLUDED.created_at_snapshot;
END;
$$ LANGUAGE plpgsql;

-- 刷新 Issue 贡献者汇总函数
CREATE OR REPLACE FUNCTION warehouse.refresh_dws_issue_contributor_summary(
    p_issue_id INTEGER,
    p_project_id INTEGER
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.dws_issue_contributor_summary (
        issue_id, project_id,
        manager_count, implementation_count, developer_count,
        tester_count, other_count, total_contributors, total_journals,
        created_at_snapshot
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
        SUM(journal_count) as total_journals,
        CURRENT_TIMESTAMP as created_at_snapshot
    FROM warehouse.dws_issue_contributors
    WHERE issue_id = p_issue_id
      AND project_id = p_project_id
    GROUP BY issue_id, project_id
    ON CONFLICT (issue_id) DO UPDATE SET
        project_id = EXCLUDED.project_id,
        manager_count = EXCLUDED.manager_count,
        implementation_count = EXCLUDED.implementation_count,
        developer_count = EXCLUDED.developer_count,
        tester_count = EXCLUDED.tester_count,
        other_count = EXCLUDED.other_count,
        total_contributors = EXCLUDED.total_contributors,
        total_journals = EXCLUDED.total_journals,
        created_at_snapshot = EXCLUDED.created_at_snapshot;
END;
$$ LANGUAGE plpgsql;

-- 刷新项目角色分布函数
CREATE OR REPLACE FUNCTION warehouse.refresh_dws_project_role_distribution(
    p_project_id INTEGER,
    p_snapshot_date DATE
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.dws_project_role_distribution (
        project_id, snapshot_date,
        manager_count, implementation_count, developer_count,
        tester_count, other_count, total_members,
        created_at_snapshot
    )
    SELECT
        project_id,
        p_snapshot_date as snapshot_date,
        SUM(CASE WHEN role_category = 'manager' THEN 1 ELSE 0 END) as manager_count,
        SUM(CASE WHEN role_category = 'implementation' THEN 1 ELSE 0 END) as implementation_count,
        SUM(CASE WHEN role_category = 'developer' THEN 1 ELSE 0 END) as developer_count,
        SUM(CASE WHEN role_category = 'tester' THEN 1 ELSE 0 END) as tester_count,
        SUM(CASE WHEN role_category = 'other' THEN 1 ELSE 0 END) as other_count,
        COUNT(DISTINCT user_id) as total_members,
        CURRENT_TIMESTAMP as created_at_snapshot
    FROM warehouse.dwd_user_project_role
    WHERE project_id = p_project_id
    GROUP BY project_id
    ON CONFLICT (project_id, snapshot_date) DO UPDATE SET
        manager_count = EXCLUDED.manager_count,
        implementation_count = EXCLUDED.implementation_count,
        developer_count = EXCLUDED.developer_count,
        tester_count = EXCLUDED.tester_count,
        other_count = EXCLUDED.other_count,
        total_members = EXCLUDED.total_members,
        created_at_snapshot = EXCLUDED.created_at_snapshot;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. 视图定义
-- =====================================================

-- 项目实时统计视图
CREATE OR REPLACE VIEW warehouse.mv_project_realtime_stats AS
SELECT
    p.project_id,
    p.project_name,
    COUNT(DISTINCT i.issue_id) as total_issues,
    COUNT(DISTINCT CASE WHEN i.is_closed = FALSE THEN i.issue_id END) as open_issues,
    COUNT(DISTINCT CASE WHEN i.is_closed = TRUE THEN i.issue_id END) as closed_issues,
    SUM(i.spent_hours) as total_spent_hours,
    COUNT(DISTINCT ic.user_id) as total_contributors,
    MAX(i.updated_on) as last_activity
FROM warehouse.dim_project p
LEFT JOIN warehouse.dwd_issue_daily_snapshot i ON p.project_id = i.project_id
LEFT JOIN warehouse.dws_issue_contributors ic ON i.issue_id = ic.issue_id
WHERE p.is_active = TRUE
GROUP BY p.project_id, p.project_name;

-- 贡献者排行榜视图
CREATE OR REPLACE VIEW warehouse.v_contributor_ranking AS
SELECT
    project_id,
    year_month,
    user_id,
    user_name,
    role_category,
    total_issues,
    total_journals,
    resolved_issues,
    RANK() OVER (PARTITION BY project_id, year_month ORDER BY total_issues DESC) as issue_rank,
    RANK() OVER (PARTITION BY project_id, year_month ORDER BY total_journals DESC) as journal_rank
FROM warehouse.ads_contributor_report;

-- 项目健康度最新视图
CREATE OR REPLACE VIEW warehouse.v_project_health_latest AS
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

-- 用户工作量月度汇总视图
CREATE OR REPLACE VIEW warehouse.v_user_workload_monthly AS
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
-- 4. 订阅表注释
-- =====================================================

COMMENT ON COLUMN warehouse.ads_user_subscriptions.subscription_id IS '订阅 ID (格式：user_id:project_id:channel)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.user_id IS '用户 ID';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.user_name IS '订阅人姓名';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.user_email IS '订阅人邮箱 (用于接收邮件)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.project_id IS '项目 ID';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.channel IS '推送渠道 (dingtalk/telegram/email)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.channel_id IS '渠道 ID (钉钉用户 ID/Telegram chat ID/邮箱)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.report_type IS '报告类型 (daily/weekly/monthly)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.report_level IS '报告级别 (brief/detailed/comprehensive)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.language IS '语言偏好 (zh_CN/en_US)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.send_time IS '发送时间 (daily 用 "09:00", weekly 用 "Mon 09:00")';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.send_day_of_week IS '周报发送星期 (Mon-Sun)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.send_day_of_month IS '月报发送日期 (1-31)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.include_trend IS '是否包含趋势分析';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.trend_period_days IS '趋势分析周期 (天数)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.enabled IS '是否启用';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.created_at IS '创建时间';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.updated_at IS '更新时间';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.sync_time IS '数据仓库同步时间';

-- =====================================================
-- 5. 最终授权
-- =====================================================

GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA warehouse TO redmine_warehouse;
