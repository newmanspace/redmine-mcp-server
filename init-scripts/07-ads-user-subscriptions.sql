-- Redmine MCP 数仓 - ADS 层用户订阅表
-- 版本：1.2
-- 创建日期：2026-02-27
-- 说明：存储用户项目订阅信息，支持多语言和订阅人信息

-- =====================================================
-- ADS User Subscriptions Table
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse.ads_user_subscriptions (
    subscription_id   VARCHAR(255) PRIMARY KEY,
    
    -- 用户信息
    user_id           VARCHAR(100) NOT NULL,
    user_name         VARCHAR(200),                -- 订阅人姓名
    user_email        VARCHAR(255),                -- 订阅人邮箱
    
    -- 项目信息
    project_id        INTEGER NOT NULL,
    
    -- 推送渠道
    channel           VARCHAR(50) NOT NULL,        -- dingtalk/telegram/email
    channel_id        VARCHAR(255) NOT NULL,       -- 渠道 ID (钉钉用户 ID/Telegram chat ID/邮箱)
    
    -- 报告配置
    report_type       VARCHAR(20) NOT NULL DEFAULT 'daily',  -- daily/weekly/monthly
    report_level      VARCHAR(20) NOT NULL DEFAULT 'brief',  -- brief/detailed/comprehensive
    language          VARCHAR(10) DEFAULT 'zh_CN',           -- zh_CN/en_US
    
    -- 发送时间配置
    send_time         VARCHAR(50),                -- 发送时间 (HH:MM)
    send_day_of_week  VARCHAR(10),                -- 周报发送星期 (Mon-Sun)
    send_day_of_month INTEGER,                    -- 月报发送日期 (1-31)
    
    -- 趋势分析配置
    include_trend     BOOLEAN DEFAULT TRUE,       -- 是否包含趋势分析
    trend_period_days INTEGER DEFAULT 7,          -- 趋势分析周期 (天数)
    
    -- 订阅状态
    enabled           BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL,
    sync_time         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Indexes
-- =====================================================

-- 按用户查询订阅
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user 
  ON warehouse.ads_user_subscriptions(user_id);

-- 按用户邮箱查询
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user_email 
  ON warehouse.ads_user_subscriptions(user_email);

-- 按项目查询订阅者
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_project 
  ON warehouse.ads_user_subscriptions(project_id);

-- 按渠道查询
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_channel 
  ON warehouse.ads_user_subscriptions(channel);

-- 按语言查询
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_language 
  ON warehouse.ads_user_subscriptions(language);

-- 查询启用的订阅
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_enabled 
  ON warehouse.ads_user_subscriptions(enabled);

-- 复合索引：用户 + 项目
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user_project 
  ON warehouse.ads_user_subscriptions(user_id, project_id);

-- 复合索引：报告类型 + 语言 + 启用状态 (用于定时推送)
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_report_type_language_enabled 
  ON warehouse.ads_user_subscriptions(report_type, language, enabled);

-- 复合索引：发送时间 + 启用状态
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_send_time_enabled 
  ON warehouse.ads_user_subscriptions(send_time, enabled);

-- =====================================================
-- Grant Privileges
-- =====================================================

GRANT ALL PRIVILEGES ON TABLE warehouse.ads_user_subscriptions TO redmine_warehouse;

-- =====================================================
-- Table Comments
-- =====================================================

COMMENT ON TABLE warehouse.ads_user_subscriptions IS 'ADS-用户项目订阅表 - 存储用户对项目的订阅配置，支持日报/周报/月报';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.subscription_id IS '订阅 ID (格式：user_id:project_id:channel)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.user_id IS '用户 ID';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.project_id IS '项目 ID';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.channel IS '推送渠道 (dingtalk/telegram/email)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.channel_id IS '渠道 ID (钉钉用户 ID/Telegram chat ID/邮箱)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.report_type IS '报告类型 (daily/weekly/monthly)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.report_level IS '报告级别 (brief/detailed/comprehensive)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.send_time IS '发送时间 (daily 用 "09:00", weekly 用 "Mon 09:00")';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.send_day_of_week IS '周报发送星期 (Mon-Sun)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.send_day_of_month IS '月报发送日期 (1-31)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.include_trend IS '是否包含趋势分析';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.trend_period_days IS '趋势分析周期 (天数)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.enabled IS '是否启用';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.created_at IS '创建时间';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.updated_at IS '更新时间';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.sync_time IS '数据仓库同步时间';
