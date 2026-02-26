-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建模式
CREATE SCHEMA IF NOT EXISTS warehouse;
SET search_path TO warehouse, public;

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

-- 索引
CREATE INDEX IF NOT EXISTS idx_issue_snapshot_date ON warehouse.issue_daily_snapshot(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_issue_project_date ON warehouse.issue_daily_snapshot(project_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_issue_status_name ON warehouse.issue_daily_snapshot(status_name);
CREATE INDEX IF NOT EXISTS idx_issue_priority_name ON warehouse.issue_daily_snapshot(priority_name);
CREATE INDEX IF NOT EXISTS idx_project_summary_date ON warehouse.project_daily_summary(project_id, snapshot_date);

-- 授予权限
GRANT ALL PRIVILEGES ON SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO redmine_warehouse;

-- 刷新项目每日汇总数据的函数
CREATE OR REPLACE FUNCTION warehouse.refresh_daily_summary(p_project_id INTEGER, p_snapshot_date DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO warehouse.project_daily_summary (
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
    FROM warehouse.issue_daily_snapshot
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

-- Add updated_issues column if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'warehouse' 
        AND table_name = 'project_daily_summary' 
        AND column_name = 'updated_issues'
    ) THEN
        ALTER TABLE warehouse.project_daily_summary ADD COLUMN updated_issues INTEGER DEFAULT 0;
    END IF;
END $$;
