-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建模式
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS reporting;

-- 设置搜索路径
SET search_path TO warehouse, reporting, public;

-- 授予权限
GRANT ALL PRIVILEGES ON SCHEMA warehouse TO redmine_warehouse;
GRANT ALL PRIVILEGES ON SCHEMA reporting TO redmine_warehouse;
