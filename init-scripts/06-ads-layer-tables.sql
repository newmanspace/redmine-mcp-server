-- Redmine MCP 数仓 - ADS 层应用报表表
-- 版本：1.0
-- 创建日期：2026-02-27
-- 说明：面向报表和应用的数据表

-- =====================================================
-- 1. 贡献者分析报表
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.ads_contributor_report (
    report_id        BIGSERIAL PRIMARY KEY,
    project_id       INTEGER NOT NULL,
    project_name     VARCHAR(255),
    year_month       VARCHAR(7) NOT NULL,      -- YYYY-MM
    user_id          INTEGER NOT NULL,
    user_name        VARCHAR(200),
    role_category    VARCHAR(20),
    total_issues     INTEGER DEFAULT 0,         -- 参与 Issue 数
    total_journals   INTEGER DEFAULT 0,         -- 总操作数
    resolved_issues  INTEGER DEFAULT 0,         -- 解决 Issue 数
    verified_issues  INTEGER DEFAULT 0,         -- 验证 Issue 数
    as_manager       INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer     INTEGER DEFAULT 0,
    as_tester        INTEGER DEFAULT 0,
    avg_resolution_days DECIMAL(10,2),          -- 平均解决天数
    report_date      DATE DEFAULT CURRENT_DATE,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, year_month, user_id)
);

CREATE INDEX IF NOT EXISTS idx_ads_contributor_project ON warehouse.ads_contributor_report(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_contributor_month ON warehouse.ads_contributor_report(year_month);
CREATE INDEX IF NOT EXISTS idx_ads_contributor_user ON warehouse.ads_contributor_report(user_id);

-- =====================================================
-- 2. 项目健康度报表
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.ads_project_health_report (
    report_id        BIGSERIAL PRIMARY KEY,
    project_id       INTEGER NOT NULL,
    project_name     VARCHAR(255),
    snapshot_date    DATE NOT NULL,
    
    -- 基础指标
    total_issues     INTEGER DEFAULT 0,
    new_issues       INTEGER DEFAULT 0,
    closed_issues    INTEGER DEFAULT 0,
    open_issues      INTEGER DEFAULT 0,
    
    -- 状态分布
    status_new       INTEGER DEFAULT 0,
    status_in_progress INTEGER DEFAULT 0,
    status_resolved  INTEGER DEFAULT 0,
    status_closed    INTEGER DEFAULT 0,
    
    -- 优先级分布
    priority_immediate INTEGER DEFAULT 0,
    priority_urgent  INTEGER DEFAULT 0,
    priority_high    INTEGER DEFAULT 0,
    
    -- 健康度评分 (0-100)
    health_score     DECIMAL(5,2),             -- 综合健康度
    issue_velocity   DECIMAL(10,2),            -- Issue 处理速度（个/天）
    avg_age_days     DECIMAL(10,2),            -- 平均 Issue 年龄
    overdue_rate     DECIMAL(5,4),             -- 逾期率
    
    -- 趋势指标
    new_trend        DECIMAL(5,2),             -- 新增趋势（环比）
    closed_trend     DECIMAL(5,2),             -- 关闭趋势（环比）
    
    -- 风险标识
    risk_level       VARCHAR(20),              -- low/medium/high/critical
    risk_factors     TEXT,                     -- 风险因素说明
    
    report_date      DATE DEFAULT CURRENT_DATE,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_ads_project_health_project ON warehouse.ads_project_health_report(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_project_health_date ON warehouse.ads_project_health_report(snapshot_date);

-- =====================================================
-- 3. 用户工作量报表
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.ads_user_workload_report (
    report_id        BIGSERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    user_name        VARCHAR(200),
    year_month       VARCHAR(7) NOT NULL,      -- YYYY-MM
    
    -- 跨项目统计
    total_projects   INTEGER DEFAULT 0,        -- 参与项目数
    total_issues     INTEGER DEFAULT 0,        -- 总 Issue 数
    total_journals   INTEGER DEFAULT 0,        -- 总操作数
    
    -- 角色分布
    as_manager       INTEGER DEFAULT 0,
    as_implementation INTEGER DEFAULT 0,
    as_developer     INTEGER DEFAULT 0,
    as_tester        INTEGER DEFAULT 0,
    
    -- 工作量指标
    resolved_issues  INTEGER DEFAULT 0,        -- 解决数
    verified_issues  INTEGER DEFAULT 0,        -- 验证数
    created_issues   INTEGER DEFAULT 0,        -- 创建数
    
    -- 效率指标
    avg_resolution_days DECIMAL(10,2),         -- 平均解决天数
    issues_per_day   DECIMAL(10,2),            -- 日均处理数
    
    -- 项目明细（JSON 格式）
    project_details  JSONB,                    -- 各项目工作量明细
    
    -- 排名
    rank_in_month  INTEGER,                    -- 月度排名
    percentile     DECIMAL(5,2),               -- 百分位
    
    report_date    DATE DEFAULT CURRENT_DATE,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, year_month)
);

CREATE INDEX IF NOT EXISTS idx_ads_user_workload_user ON warehouse.ads_user_workload_report(user_id);
CREATE INDEX IF NOT EXISTS idx_ads_user_workload_month ON warehouse.ads_user_workload_report(year_month);

-- =====================================================
-- 4. 团队绩效报表
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.ads_team_performance_report (
    report_id        BIGSERIAL PRIMARY KEY,
    project_id       INTEGER NOT NULL,
    project_name     VARCHAR(255),
    year_month       VARCHAR(7) NOT NULL,      -- YYYY-MM
    
    -- 团队规模
    total_members    INTEGER DEFAULT 0,
    manager_count    INTEGER DEFAULT 0,
    developer_count  INTEGER DEFAULT 0,
    tester_count     INTEGER DEFAULT 0,
    
    -- 整体产出
    total_issues     INTEGER DEFAULT 0,
    resolved_issues  INTEGER DEFAULT 0,
    closed_issues    INTEGER DEFAULT 0,
    total_journals   INTEGER DEFAULT 0,
    
    -- 效率指标
    avg_resolution_days DECIMAL(10,2),
    issues_per_member   DECIMAL(10,2),         -- 人均 Issue 数
    journals_per_member DECIMAL(10,2),         -- 人均操作数
    
    -- 协作指标
    collaboration_rate  DECIMAL(5,2),          -- 协作率
    self_resolve_rate   DECIMAL(5,2),          -- 自解自测率
    
    -- 质量指标
    reopen_rate      DECIMAL(5,4),             -- 重开率
    overdue_rate     DECIMAL(5,4),             -- 逾期率
    
    -- 趋势
    mom_growth       DECIMAL(5,2),             -- 环比增长
    yoy_growth       DECIMAL(5,2),             -- 同比增长
    
    -- 绩效评分
    performance_score DECIMAL(5,2),            -- 综合绩效分 (0-100)
    performance_level VARCHAR(20),             -- S/A/B/C/D
    
    report_date      DATE DEFAULT CURRENT_DATE,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, year_month)
);

CREATE INDEX IF NOT EXISTS idx_ads_team_performance_project ON warehouse.ads_team_performance_report(project_id);
CREATE INDEX IF NOT EXISTS idx_ads_team_performance_month ON warehouse.ads_team_performance_report(year_month);

-- =====================================================
-- 5. 创建视图
-- =====================================================

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
-- 6. 授予权限
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA warehouse TO redmine_warehouse;

-- =====================================================
-- 7. 表注释
-- =====================================================

COMMENT ON TABLE warehouse.ads_contributor_report IS 'ADS-贡献者分析报表（按月）';
COMMENT ON TABLE warehouse.ads_project_health_report IS 'ADS-项目健康度报表（按日）';
COMMENT ON TABLE warehouse.ads_user_workload_report IS 'ADS-用户工作量报表（按月）';
COMMENT ON TABLE warehouse.ads_team_performance_report IS 'ADS-团队绩效报表（按月）';

COMMENT ON VIEW warehouse.v_contributor_ranking IS '视图-贡献者排行榜';
COMMENT ON VIEW warehouse.v_project_health_latest IS '视图-项目健康度最新';
COMMENT ON VIEW warehouse.v_user_workload_monthly IS '视图-用户工作量月度汇总';
