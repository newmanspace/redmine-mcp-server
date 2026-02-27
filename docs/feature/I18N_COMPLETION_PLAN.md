# 完成国际化支持 - 总结

**日期**: 2026-02-27  
**状态**: ✅ 基础架构完成，待集成

---

## 已完成的工作

### 1. ✅ 创建 i18n 模块

**文件结构**:
```
src/redmine_mcp_server/i18n/
├── __init__.py          # 主模块，提供翻译函数
├── config.py            # 配置
├── zh_CN.py             # 中文翻译
└── en_US.py             # 英文翻译
```

**翻译内容** (~40 项):
- 报告类型 (daily/weekly/monthly)
- 报告级别 (brief/detailed/comprehensive)
- 状态名称 (新建/进行中/已解决/已关闭)
- 优先级 (立刻/紧急/高/普通/低)
- 邮件主题模板
- 指标名称 (12 个)
- 趋势分析术语 (8 个)
- 邮件内容章节

### 2. ✅ 更新数据库结构

**新增字段**:
- `user_name` - 订阅人姓名
- `user_email` - 订阅人邮箱
- `language` - 语言偏好 (zh_CN/en_US)

**新增索引**:
- `idx_ads_user_subscriptions_user_email`
- `idx_ads_user_subscriptions_language`
- `idx_ads_user_subscriptions_report_type_language_enabled`

### 3. ✅ 更新 email_service.py

**修改内容**:
- `send_subscription_email()` 添加 `language` 参数
- `_generate_email_body()` 添加 `language` 参数
- 使用 i18n 模块生成多语言邮件主题
- 使用 i18n 模块生成多语言邮件内容

### 4. ✅ 创建文档

`docs/feature/I18N_SUPPORT.md` - 完整的国际化支持文档

---

## 待完成的工作

### 1. 更新 subscription_tools.py

需要添加 `language` 和 `user_name` 参数到 `subscribe_project()` MCP 工具：

```python
@mcp.tool()
async def subscribe_project(
    project_id: int,
    channel: str = "email",
    channel_id: Optional[str] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
    report_type: str = "daily",
    report_level: str = "brief",
    language: str = "zh_CN",  # 新增
    send_time: str = "09:00",
    send_day_of_week: Optional[str] = None,
    send_day_of_month: Optional[int] = None,
    include_trend: bool = True,
    trend_period_days: int = 7
) -> Dict[str, Any]:
```

### 2. 创建数据库迁移脚本

创建 `init-scripts/08-migrate-subscriptions-i18n.sql`:

```sql
-- 添加用户信息字段
ALTER TABLE warehouse.ads_user_subscriptions 
ADD COLUMN IF NOT EXISTS user_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS user_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'zh_CN';

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_user_email 
  ON warehouse.ads_user_subscriptions(user_email);

CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_language 
  ON warehouse.ads_user_subscriptions(language);

CREATE INDEX IF NOT EXISTS idx_ads_user_subscriptions_report_type_language_enabled 
  ON warehouse.ads_user_subscriptions(report_type, language, enabled);
```

### 3. 更新 subscription_service.py

更新 `subscribe()` 方法签名，添加 `user_name`, `user_email`, `language` 参数。

### 4. 更新 subscription_push_service.py

确保推送时使用订阅人的语言偏好：

```python
def push_subscription(self, subscription: Dict[str, Any]) -> bool:
    language = subscription.get('language', 'zh_CN')
    user_email = subscription.get('user_email') or subscription.get('channel_id')
    
    # 使用订阅人的语言生成报告
    report = self.generate_report(..., language=language)
    
    # 发送到订阅人邮箱
    self.send_email_report(user_email, project_name, report, level, language)
```

---

## 使用示例

### 订阅中文日报

```python
subscribe_project(
    project_id=341,
    user_name="张三",
    user_email="zhangsan@example.com",
    channel="email",
    report_type="daily",
    language="zh_CN"  # 中文
)
```

**收到邮件**:
```
主题：[Redmine] 江苏新顺 CIM - 项目日报 (2026-02-27)

📊 江苏新顺 CIM - 项目日报
报告日期：2026-02-27

📈 概览
Issue 总数：540
今日新增：+9
今日关闭：8
未关闭：162
```

### 订阅英文日报

```python
subscribe_project(
    project_id=341,
    user_name="John Doe",
    user_email="john@example.com",
    channel="email",
    report_type="daily",
    language="en_US"  # English
)
```

**收到邮件**:
```
Subject: [Redmine] Jiangsu Xinshun CIM - Daily Report (2026-02-27)

📊 Jiangsu Xinshun CIM - Daily Report
Report Date: 2026-02-27

📈 Overview
Total Issues: 540
New Today: +9
Closed Today: 8
Open: 162
```

---

## 翻译对照表

### 报告类型
| Key | zh_CN | en_US |
|-----|-------|-------|
| daily | 日报 | Daily Report |
| weekly | 周报 | Weekly Report |
| monthly | 月报 | Monthly Report |

### 指标名称
| Key | zh_CN | en_US |
|-----|-------|-------|
| total_issues | Issue 总数 | Total Issues |
| today_new | 今日新增 | New Today |
| today_closed | 今日关闭 | Closed Today |
| open_issues | 未关闭 | Open |
| completion_rate | 完成率 | Completion Rate |

### 趋势方向
| Key | zh_CN | en_US |
|-----|-------|-------|
| improving | 改善 | Improving |
| declining | 下降 | Declining |
| stable | 稳定 | Stable |

---

## 测试

### 测试中文邮件生成

```python
from redmine_mcp_server.dws.services.email_service import send_subscription_email

report = {
    'type': 'daily',
    'date': '2026-02-27',
    'stats': {
        'total_issues': 540,
        'today_new': 9,
        'today_closed': 8
    }
}

send_subscription_email(
    to_email='test@example.com',
    project_name='Test Project',
    report=report,
    level='brief',
    language='zh_CN'  # 中文
)
```

### 测试英文邮件生成

```python
send_subscription_email(
    to_email='test@example.com',
    project_name='Test Project',
    report=report,
    level='brief',
    language='en_US'  # English
)
```

---

## 下一步

1. **运行数据库迁移** - 添加新字段和索引
2. **更新 MCP 工具** - 添加语言和用户信息参数
3. **完整测试** - 测试中英文邮件生成和发送
4. **文档更新** - 更新 README 和使用指南

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
