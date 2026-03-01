-- ===========================================
-- Redmine MCP Server - Base Data
-- Version: v0.10.0
-- Type: DATA
-- Date: 2026-02-28
-- Description: Base data (INSERT statements only)
-- ===========================================

SET timezone = 'Asia/Shanghai';
SET search_path TO warehouse, public;


-- ===========================================
-- 1. Base Data
-- ===========================================

-- -----------------------------------------------------
-- 1.1 Role Categories
-- -----------------------------------------------------

INSERT INTO warehouse.dim_role_category (role_id, role_name, category, priority, description)
VALUES
    (3, 'Manager', 'manager', 1, 'Project managers and administrators'),
    (8, 'Implementation', 'implementation', 2, 'Implementation consultants and deployment personnel'),
    (4, 'Developer', 'developer', 3, 'Development engineers'),
    (7, 'Tester', 'tester', 4, 'Test engineers'),
    (5, 'Reporter', 'reporter', 5, 'Report viewers'),
    (6, 'Viewer', 'viewer', 6, 'Read-only access')
ON CONFLICT (role_id) DO NOTHING;


-- ===========================================
-- End of File
-- ===========================================
