-- Redmine MCP 数仓 - DIM 层维度表
-- 版本：1.0
-- 创建日期：2026-02-27
-- 说明：维度表用于数据分析和报表

-- =====================================================
-- 1. 角色分类维度表
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_role_category (
    role_category_id   SERIAL PRIMARY KEY,
    role_category_name VARCHAR(50) NOT NULL UNIQUE,  -- manager/implementation/developer/tester/other
    role_priority      INTEGER NOT NULL,             -- 1-5，数字越小优先级越高
    description        TEXT,
    redmine_role_names TEXT,                        -- 对应的 Redmine 角色名（逗号分隔）
    is_active          BOOLEAN DEFAULT TRUE,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认角色分类
INSERT INTO warehouse.dim_role_category (role_category_name, role_priority, description, redmine_role_names) VALUES
('manager', 1, '管理人员', 'project manager,manager，负责人，项目经理'),
('implementation', 2, '实施人员', 'implementation，实施，实施人员'),
('developer', 3, '开发人员', 'developer，开发，开发人员，engineer'),
('tester', 4, '测试人员', 'tester，测试，测试人员，qa'),
('other', 5, '其他角色', 'viewer，报告者，reporter,other')
ON CONFLICT (role_category_name) DO NOTHING;

-- =====================================================
-- 2. 日期维度表
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_id           INTEGER PRIMARY KEY,      -- YYYYMMDD 格式
    full_date         DATE NOT NULL UNIQUE,
    year              INTEGER NOT NULL,
    quarter           INTEGER NOT NULL,         -- 1-4
    month             INTEGER NOT NULL,         -- 1-12
    month_name        VARCHAR(20),              -- January, February...
    day               INTEGER NOT NULL,         -- 1-31
    day_of_week       INTEGER NOT NULL,         -- 1-7 (Monday=1)
    day_name          VARCHAR(20),              -- Monday, Tuesday...
    is_weekend        BOOLEAN DEFAULT FALSE,
    is_holiday        BOOLEAN DEFAULT FALSE,
    holiday_name      VARCHAR(100),
    week_of_year      INTEGER,                  -- 1-53
    week_of_month     INTEGER,                  -- 1-6
    day_of_year       INTEGER,                  -- 1-366
    days_in_month     INTEGER,
    days_in_quarter   INTEGER,
    days_in_year      INTEGER,
    is_leap_year      BOOLEAN DEFAULT FALSE,
    season            VARCHAR(20),              -- Spring, Summer, Fall, Winter
    fiscal_year       INTEGER,
    fiscal_quarter    INTEGER,
    fiscal_month      INTEGER,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生成日期数据（2010-2030 年，共 21 年）
INSERT INTO warehouse.dim_date (
    date_id, full_date, year, quarter, month, month_name, day,
    day_of_week, day_name, is_weekend, week_of_year, week_of_month,
    day_of_year, days_in_month, days_in_year, is_leap_year, season, fiscal_year
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_id,
    d AS full_date,
    EXTRACT(YEAR FROM d)::INTEGER AS year,
    EXTRACT(QUARTER FROM d)::INTEGER AS quarter,
    EXTRACT(MONTH FROM d)::INTEGER AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(DAY FROM d)::INTEGER AS day,
    EXTRACT(ISODOW FROM d)::INTEGER AS day_of_week,
    TO_CHAR(d, 'Day') AS day_name,
    (EXTRACT(ISODOW FROM d) > 5) AS is_weekend,
    EXTRACT(WEEK FROM d)::INTEGER AS week_of_year,
    CEIL(EXTRACT(DAY FROM d)/7.0)::INTEGER AS week_of_month,
    EXTRACT(DOY FROM d)::INTEGER AS day_of_year,
    (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::DATE - DATE_TRUNC('month', d)::DATE + 1 AS days_in_month,
    (DATE_TRUNC('year', d) + INTERVAL '1 year - 1 day')::DATE - DATE_TRUNC('year', d)::DATE + 1 AS days_in_year,
    (EXTRACT(YEAR FROM d) % 4 = 0 AND (EXTRACT(YEAR FROM d) % 100 != 0 OR EXTRACT(YEAR FROM d) % 400 = 0)) AS is_leap_year,
    CASE
        WHEN EXTRACT(MONTH FROM d) IN (3,4,5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM d) IN (6,7,8) THEN 'Summer'
        WHEN EXTRACT(MONTH FROM d) IN (9,10,11) THEN 'Fall'
        ELSE 'Winter'
    END AS season,
    EXTRACT(YEAR FROM d)::INTEGER AS fiscal_year
FROM generate_series('2010-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_id) DO NOTHING;

-- =====================================================
-- 3. 项目维度表（缓慢变化维度 SCD Type 2）
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_project (
    project_key        SERIAL PRIMARY KEY,      -- 代理键
    project_id         INTEGER NOT NULL,        -- 业务键
    project_name       VARCHAR(255) NOT NULL,
    project_identifier VARCHAR(100),
    parent_project_id  INTEGER,
    project_status     INTEGER,
    is_active          BOOLEAN DEFAULT TRUE,
    effective_from     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to       TIMESTAMP,
    is_current         BOOLEAN DEFAULT TRUE,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, effective_from)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dim_project_current ON warehouse.dim_project(is_current);
CREATE INDEX IF NOT EXISTS idx_dim_project_id ON warehouse.dim_project(project_id);

-- =====================================================
-- 4. 用户维度表（缓慢变化维度 SCD Type 2）
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_user (
    user_key           SERIAL PRIMARY KEY,      -- 代理键
    user_id            INTEGER NOT NULL,        -- 业务键
    login              VARCHAR(100) NOT NULL,
    full_name          VARCHAR(200),
    email              VARCHAR(255),
    user_status        INTEGER,
    is_active          BOOLEAN DEFAULT TRUE,
    effective_from     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to       TIMESTAMP,
    is_current         BOOLEAN DEFAULT TRUE,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, effective_from)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dim_user_current ON warehouse.dim_user(is_current);
CREATE INDEX IF NOT EXISTS idx_dim_user_id ON warehouse.dim_user(user_id);

-- =====================================================
-- 5. Issue 维度表（缓慢变化维度 SCD Type 2）
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_issue (
    issue_key          SERIAL PRIMARY KEY,      -- 代理键
    issue_id           INTEGER NOT NULL,        -- 业务键
    subject            VARCHAR(500),
    tracker_id         INTEGER,
    tracker_name       VARCHAR(100),
    status_id          INTEGER,
    status_name        VARCHAR(100),
    priority_id        INTEGER,
    priority_name      VARCHAR(100),
    project_id         INTEGER,
    author_id          INTEGER,
    assigned_to_id     INTEGER,
    is_closed          BOOLEAN DEFAULT FALSE,
    effective_from     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_to       TIMESTAMP,
    is_current         BOOLEAN DEFAULT TRUE,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (issue_id, effective_from)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dim_issue_current ON warehouse.dim_issue(is_current);
CREATE INDEX IF NOT EXISTS idx_dim_issue_id ON warehouse.dim_issue(issue_id);
CREATE INDEX IF NOT EXISTS idx_dim_issue_status ON warehouse.dim_issue(status_id);

-- =====================================================
-- 6. 授予权限
-- =====================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA warehouse TO redmine_warehouse;

-- =====================================================
-- 7. 表注释
-- =====================================================

COMMENT ON TABLE warehouse.dim_role_category IS 'DIM-角色分类维度表';
COMMENT ON TABLE warehouse.dim_date IS 'DIM-日期维度表 (2020-2030)';
COMMENT ON TABLE warehouse.dim_project IS 'DIM-项目维度表 (SCD Type 2)';
COMMENT ON TABLE warehouse.dim_user IS 'DIM-用户维度表 (SCD Type 2)';
COMMENT ON TABLE warehouse.dim_issue IS 'DIM-Issue 维度表 (SCD Type 2)';

-- =====================================================
-- 8. 创建视图 - 当前有效的项目/用户/Issue
-- =====================================================

CREATE OR REPLACE VIEW warehouse.v_dim_project_current AS
SELECT * FROM warehouse.dim_project WHERE is_current = TRUE;

CREATE OR REPLACE VIEW warehouse.v_dim_user_current AS
SELECT * FROM warehouse.dim_user WHERE is_current = TRUE;

CREATE OR REPLACE VIEW warehouse.v_dim_issue_current AS
SELECT * FROM warehouse.dim_issue WHERE is_current = TRUE;

COMMENT ON VIEW warehouse.v_dim_project_current IS '视图-当前有效的项目维度';
COMMENT ON VIEW warehouse.v_dim_user_current IS '视图-当前有效的用户维度';
COMMENT ON VIEW warehouse.v_dim_issue_current IS '视图-当前有效的 Issue 维度';
