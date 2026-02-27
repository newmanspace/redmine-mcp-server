-- Redmine MCP - 订阅表国际化迁移
-- 版本：1.2
-- 日期：2026-02-27
-- 说明：添加用户信息和语言偏好支持

BEGIN;

-- =====================================================
-- 1. 添加新字段
-- =====================================================

-- 订阅人姓名
ALTER TABLE warehouse.ads_user_subscriptions 
ADD COLUMN IF NOT EXISTS user_name VARCHAR(200);

-- 订阅人邮箱
ALTER TABLE warehouse.ads_user_subscriptions 
ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);

-- 语言偏好 (默认中文)
ALTER TABLE warehouse.ads_user_subscriptions 
ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'zh_CN';

-- =====================================================
-- 2. 添加索引
-- =====================================================

-- 按用户邮箱查询
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user_email 
  ON warehouse.ads_user_subscriptions(user_email);

-- 按语言查询
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_language 
  ON warehouse.ads_user_subscriptions(language);

-- 复合索引：报告类型 + 语言 + 启用状态 (用于定时推送)
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_report_type_language_enabled 
  ON warehouse.ads_user_subscriptions(report_type, language, enabled);

-- =====================================================
-- 3. 更新现有数据
-- =====================================================

-- 将现有订阅的 channel_id 复制到 user_email (对于 email 渠道)
UPDATE warehouse.ads_user_subscriptions 
SET user_email = channel_id 
WHERE channel = 'email' AND user_email IS NULL;

-- 设置默认语言
UPDATE warehouse.ads_user_subscriptions 
SET language = 'zh_CN' 
WHERE language IS NULL;

-- =====================================================
-- 4. 添加注释
-- =====================================================

COMMENT ON COLUMN warehouse.ads_user_subscriptions.user_name IS '订阅人姓名';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.user_email IS '订阅人邮箱 (用于接收邮件)';
COMMENT ON COLUMN warehouse.ads_user_subscriptions.language IS '语言偏好 (zh_CN/en_US)';

-- =====================================================
-- 5. 验证
-- =====================================================

-- 显示表结构
\d warehouse.ads_user_subscriptions

-- 显示索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'warehouse' 
  AND tablename = 'ads_user_subscriptions'
ORDER BY indexname;

-- 统计各语言订阅数
SELECT language, COUNT(*) as count 
FROM warehouse.ads_user_subscriptions 
WHERE enabled = true 
GROUP BY language;

COMMIT;

-- =====================================================
-- 回滚脚本 (如需要)
-- =====================================================
--
-- BEGIN;
-- 
-- DROP INDEX IF EXISTS warehouse.idx_ads_user_subscriptions_user_email;
-- DROP INDEX IF EXISTS warehouse.idx_ads_user_subscriptions_language;
-- DROP INDEX IF EXISTS warehouse.idx_ads_user_subscriptions_report_type_language_enabled;
-- 
-- ALTER TABLE warehouse.ads_user_subscriptions 
--   DROP COLUMN IF EXISTS user_name,
--   DROP COLUMN IF EXISTS user_email,
--   DROP COLUMN IF EXISTS language;
-- 
-- COMMIT;
