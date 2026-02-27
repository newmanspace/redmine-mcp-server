-- Redmine MCP 数仓 - 表命名规范迁移脚本
-- 版本：1.0
-- 日期：2026-02-27
-- 说明：将现有表重命名为符合命名规范的新名称

BEGIN;

-- =====================================================
-- 1. 表重命名
-- =====================================================

-- DWD 层
ALTER TABLE warehouse.issue_daily_snapshot 
  RENAME TO dwd_issue_daily_snapshot;

-- DWS 层
ALTER TABLE warehouse.project_daily_summary 
  RENAME TO dws_project_daily_summary;

ALTER TABLE warehouse.issue_contributors 
  RENAME TO dws_issue_contributors;

ALTER TABLE warehouse.issue_contributor_summary 
  RENAME TO dws_issue_contributor_summary;

ALTER TABLE warehouse.user_project_role 
  RENAME TO dwd_user_project_role;

ALTER TABLE warehouse.project_role_distribution 
  RENAME TO dws_project_role_distribution;

ALTER TABLE warehouse.user_workload 
  RENAME TO dws_user_monthly_workload;

-- =====================================================
-- 2. 主键和序列重命名
-- =====================================================

-- dwd_issue_daily_snapshot
ALTER SEQUENCE warehouse.issue_daily_snapshot_id_seq 
  RENAME TO seq_dwd_issue_daily_snapshot_id;
ALTER INDEX warehouse.issue_daily_snapshot_pkey 
  RENAME TO pk_dwd_issue_daily_snapshot;

-- dws_project_daily_summary
ALTER SEQUENCE warehouse.project_daily_summary_id_seq 
  RENAME TO seq_dws_project_daily_summary_id;
ALTER INDEX warehouse.project_daily_summary_pkey 
  RENAME TO pk_dws_project_daily_summary;

-- dws_issue_contributors
ALTER SEQUENCE warehouse.issue_contributors_id_seq 
  RENAME TO seq_dws_issue_contributors_id;
ALTER INDEX warehouse.issue_contributors_pkey 
  RENAME TO pk_dws_issue_contributors;

-- dws_issue_contributor_summary
ALTER SEQUENCE warehouse.issue_contributor_summary_id_seq 
  RENAME TO seq_dws_issue_contributor_summary_id;
ALTER INDEX warehouse.issue_contributor_summary_pkey 
  RENAME TO pk_dws_issue_contributor_summary;

-- dwd_user_project_role
ALTER SEQUENCE warehouse.user_project_role_id_seq 
  RENAME TO seq_dwd_user_project_role_id;
ALTER INDEX warehouse.user_project_role_pkey 
  RENAME TO pk_dwd_user_project_role;

-- dws_project_role_distribution
ALTER SEQUENCE warehouse.project_role_distribution_id_seq 
  RENAME TO seq_dws_project_role_distribution_id;
ALTER INDEX warehouse.project_role_distribution_pkey 
  RENAME TO pk_dws_project_role_distribution;

-- dws_user_monthly_workload
ALTER SEQUENCE warehouse.user_workload_id_seq 
  RENAME TO seq_dws_user_monthly_workload_id;
ALTER INDEX warehouse.user_workload_pkey 
  RENAME TO pk_dws_user_monthly_workload;

-- =====================================================
-- 3. 唯一约束和索引重命名
-- =====================================================

-- dwd_issue_daily_snapshot
ALTER INDEX warehouse.uk_issue_snapshot 
  RENAME TO uk_dwd_issue_snapshot;
ALTER INDEX warehouse.idx_issue_snapshot_date 
  RENAME TO idx_dwd_issue_snapshot_date;
ALTER INDEX warehouse.idx_issue_project_date 
  RENAME TO idx_dwd_issue_project_date;
ALTER INDEX warehouse.idx_issue_status_name 
  RENAME TO idx_dwd_issue_status_name;
ALTER INDEX warehouse.idx_issue_priority_name 
  RENAME TO idx_dwd_issue_priority_name;

-- dws_project_daily_summary
ALTER INDEX warehouse.uk_project_summary 
  RENAME TO uk_dws_project_summary;
ALTER INDEX warehouse.idx_project_summary_date 
  RENAME TO idx_dws_project_summary_date;

-- dws_issue_contributors
ALTER INDEX warehouse.uk_issue_contributor 
  RENAME TO uk_dws_issue_contributor;
ALTER INDEX warehouse.idx_contributors_issue 
  RENAME TO idx_dws_issue_contributors_issue;
ALTER INDEX warehouse.idx_contributors_user 
  RENAME TO idx_dws_issue_contributors_user;
ALTER INDEX warehouse.idx_contributors_category 
  RENAME TO idx_dws_issue_contributors_category;
ALTER INDEX warehouse.idx_contributors_project 
  RENAME TO idx_dws_issue_contributors_project;

-- dws_issue_contributor_summary
ALTER INDEX warehouse.issue_contributor_summary_issue_id_key 
  RENAME TO uk_dws_issue_contributor_summary;

-- dwd_user_project_role
ALTER INDEX warehouse.uk_user_project_role 
  RENAME TO uk_dwd_user_project_role;
ALTER INDEX warehouse.idx_user_role_project 
  RENAME TO idx_dwd_user_project_role_project;
ALTER INDEX warehouse.idx_user_role_user 
  RENAME TO idx_dwd_user_project_role_user;

-- dws_project_role_distribution
ALTER INDEX warehouse.uk_project_role_dist 
  RENAME TO uk_dws_project_role_distribution;
ALTER INDEX warehouse.idx_project_role_dist_date 
  RENAME TO idx_dws_project_role_distribution_date;

-- dws_user_monthly_workload
ALTER INDEX warehouse.uk_user_workload 
  RENAME TO uk_dws_user_monthly_workload;
ALTER INDEX warehouse.idx_user_workload_user 
  RENAME TO idx_dws_user_monthly_workload_user;
ALTER INDEX warehouse.idx_user_workload_month 
  RENAME TO idx_dws_user_monthly_workload_month;
ALTER INDEX warehouse.idx_user_workload_project 
  RENAME TO idx_dws_user_monthly_workload_project;

-- =====================================================
-- 4. 存储函数重命名
-- =====================================================

-- 刷新项目每日汇总
ALTER FUNCTION warehouse.refresh_daily_summary(INTEGER, DATE)
  RENAME TO refresh_dws_project_daily_summary;

-- 刷新 Issue 贡献者汇总
ALTER FUNCTION warehouse.refresh_contributor_summary(INTEGER, INTEGER)
  RENAME TO refresh_dws_issue_contributor_summary;

-- 刷新项目角色分布
ALTER FUNCTION warehouse.refresh_project_role_distribution(INTEGER, DATE)
  RENAME TO refresh_dws_project_role_distribution;

-- 刷新用户工作量
ALTER FUNCTION warehouse.refresh_user_workload(INTEGER, VARCHAR, VARCHAR, INTEGER)
  RENAME TO refresh_dws_user_monthly_workload;

-- =====================================================
-- 5. 更新表注释
-- =====================================================

COMMENT ON TABLE warehouse.dwd_issue_daily_snapshot IS 'DWD-Issue 每日快照表 - 记录每个 Issue 在每日的状态';
COMMENT ON TABLE warehouse.dws_project_daily_summary IS 'DWS-项目每日汇总表 - 快速查询项目统计';
COMMENT ON TABLE warehouse.dws_issue_contributors IS 'DWS-Issue 贡献者明细表 - 记录每个 Issue 的所有贡献者及其活动';
COMMENT ON TABLE warehouse.dws_issue_contributor_summary IS 'DWS-Issue 贡献者汇总表 - 每个 Issue 的贡献者角色分布';
COMMENT ON TABLE warehouse.dwd_user_project_role IS 'DWD-用户项目角色表 - 记录每个用户在项目中的最高角色';
COMMENT ON TABLE warehouse.dws_project_role_distribution IS 'DWS-项目角色分布表 - 项目每日角色分布统计';
COMMENT ON TABLE warehouse.dws_user_monthly_workload IS 'DWS-用户工作量统计表 - 按用户和年月统计工作量';

-- =====================================================
-- 6. 验证
-- =====================================================

-- 显示所有表（验证重命名）
SELECT 
  schemaname,
  tablename,
  tableowner
FROM pg_tables 
WHERE schemaname = 'warehouse'
ORDER BY tablename;

-- 显示所有索引（验证重命名）
SELECT 
  schemaname,
  tablename,
  indexname
FROM pg_indexes 
WHERE schemaname = 'warehouse'
ORDER BY tablename, indexname;

-- 显示所有函数（验证重命名）
SELECT 
  n.nspname as schema_name,
  p.proname as function_name,
  pg_get_function_arguments(p.oid) as arguments
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'warehouse'
ORDER BY function_name;

COMMIT;

-- =====================================================
-- 回滚脚本（如需要）
-- =====================================================
-- 
-- BEGIN;
-- 
-- ALTER TABLE warehouse.dwd_issue_daily_snapshot RENAME TO issue_daily_snapshot;
-- ALTER TABLE warehouse.dws_project_daily_summary RENAME TO project_daily_summary;
-- ALTER TABLE warehouse.dws_issue_contributors RENAME TO issue_contributors;
-- ALTER TABLE warehouse.dws_issue_contributor_summary RENAME TO issue_contributor_summary;
-- ALTER TABLE warehouse.dwd_user_project_role RENAME TO user_project_role;
-- ALTER TABLE warehouse.dws_project_role_distribution RENAME TO project_role_distribution;
-- ALTER TABLE warehouse.dws_user_monthly_workload RENAME TO user_workload;
-- 
-- -- 恢复索引和序列名...
-- 
-- COMMIT;
