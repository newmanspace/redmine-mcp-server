-- Issue 事实表（每日快照）
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

-- 项目每日统计汇总表
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
