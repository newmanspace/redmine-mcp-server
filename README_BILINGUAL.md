# Redmine MCP Server - Bilingual Documentation / 双语文档

**Version**: 0.10.0  
**语言**: 中文 / English  
**最后更新**: 2026-02-28

---

## Quick Start / 快速开始

### English

The Redmine MCP Server provides Model Context Protocol (MCP) tools for integrating with Redmine project management systems.

**Key Features**:
- ✅ Subscription management (daily/weekly/monthly reports)
- ✅ Multi-language support (Chinese/English)
- ✅ Email notifications
- ✅ Automated scheduling
- ✅ Trend analysis
- ✅ PostgreSQL data warehouse

### 中文

Redmine MCP Server 提供用于集成 Redmine 项目管理系统的模型上下文协议 (MCP) 工具。

**主要功能**:
- ✅ 订阅管理（日报/周报/月报）
- ✅ 多语言支持（中文/英文）
- ✅ 邮件通知
- ✅ 自动调度
- ✅ 趋势分析
- ✅ PostgreSQL 数据仓库

---

## Installation / 安装

### Docker Deployment / Docker 部署

```bash
# Clone repository / 克隆仓库
git clone https://github.com/jztan/redmine-mcp-server.git
cd redmine-mcp-server

# Configure environment / 配置环境
cp .env.example .env
nano .env  # Edit configuration / 编辑配置

# Start services / 启动服务
docker compose up -d

# Check status / 检查状态
docker compose ps
```

### Environment Variables / 环境变量

| Variable / 变量 | Required / 必需 | Default / 默认 | Description / 描述 |
|----------------|-----------------|----------------|-------------------|
| `REDMINE_URL` | ✅ Yes | - | Redmine server URL / Redmine 服务器地址 |
| `REDMINE_API_KEY` | ✅ Yes | - | API key for authentication / API 密钥 |
| `EMAIL_SMTP_SERVER` | ❌ No | - | SMTP server for email / SMTP 服务器 |
| `DEFAULT_LANGUAGE` | ❌ No | `zh_CN` | Default language / 默认语言 |

---

## Usage / 使用

### Subscribe to Reports / 订阅报告

#### English

```python
# Subscribe to daily report in English
subscribe_project(
    project_id=341,
    channel="email",
    user_email="user@example.com",
    report_type="daily",      # daily/weekly/monthly
    report_level="brief",     # brief/detailed/comprehensive
    language="en_US",         # en_US/zh_CN
    send_time="09:00"
)
```

#### 中文

```python
# 订阅中文日报
subscribe_project(
    project_id=341,
    channel="email",
    user_email="user@example.com",
    report_type="daily",      # daily/weekly/monthly
    report_level="brief",     # brief/detailed/comprehensive
    language="zh_CN",         # en_US/zh_CN
    send_time="09:00"
)
```

### Report Types / 报告类型

| Type / 类型 | Frequency / 频率 | Description / 描述 |
|------------|------------------|-------------------|
| Daily / 日报 | Every day / 每天 | Key metrics overview / 关键指标概览 |
| Weekly / 周报 | Every Monday / 每周一 | Weekly summary with trends / 周度总结带趋势 |
| Monthly / 月报 | 1st of month / 每月 1 号 | Comprehensive analysis / 完整分析 |

### Report Levels / 报告级别

| Level / 级别 | Content / 内容 |
|-------------|---------------|
| Brief / 简要 | Key metrics only / 仅关键指标 |
| Detailed / 详细 | + High priority issues + Team workload / + 高优先级 Issue + 人员负载 |
| Comprehensive / 完整 | + Trend analysis / + 趋势分析 |

---

## Architecture / 架构

### Components / 组件

```
┌─────────────────┐
│  MCP Client     │  (Claude, VSCode, etc.)
│  MCP 客户端      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MCP Server     │  Port 8000 / 端口 8000
│  MCP 服务器      │
└────────┬────────┘
         │
         ├──► Subscription Service / 订阅服务
         ├──► Email Service / 邮件服务
         ├──► Report Service / 报告服务
         └──► Scheduler / 调度器
               │
               ▼
         ┌─────────────┐
         │ PostgreSQL  │  Port 5432
         │ 数据库      │
         └─────────────┘
```

### Data Flow / 数据流

#### English

1. User subscribes to project reports via MCP tool
2. Subscription saved to PostgreSQL database
3. Scheduler triggers at configured time
4. Report generated from Redmine API
5. Email sent to subscriber in configured language

#### 中文

1. 用户通过 MCP 工具订阅项目报告
2. 订阅保存到 PostgreSQL 数据库
3. 调度器在配置时间触发
4. 从 Redmine API 生成报告
5. 按配置语言发送邮件给订阅者

---

## API Reference / API 参考

### MCP Tools / MCP 工具

#### subscribe_project

**English**: Subscribe to project reports  
**中文**: 订阅项目报告

**Parameters / 参数**:
- `project_id` (int): Project ID / 项目 ID
- `channel` (str): Push channel / 推送渠道 (email/dingtalk/telegram)
- `user_email` (str): Subscriber email / 订阅人邮箱
- `report_type` (str): Report type / 报告类型 (daily/weekly/monthly)
- `report_level` (str): Report level / 报告级别 (brief/detailed/comprehensive)
- `language` (str): Language / 语言 (zh_CN/en_US)
- `send_time` (str): Send time / 发送时间 (HH:MM)

#### push_subscription_reports

**English**: Manually trigger report push  
**中文**: 手动触发报告推送

**Parameters / 参数**:
- `report_type` (str): Report type / 报告类型
- `project_id` (int): Project ID (optional) / 项目 ID（可选）

---

## Troubleshooting / 故障排查

### Issue: Container not starting / 容器无法启动

**English**:
```bash
# Check logs / 查看日志
docker compose logs redmine-mcp-server

# Restart service / 重启服务
docker compose restart
```

**中文**:
```bash
# 查看日志
docker compose logs redmine-mcp-server

# 重启服务
docker compose restart
```

### Issue: Email not sending / 邮件无法发送

**English**:
1. Check SMTP configuration in `.env`
2. Test connection: `test_email_service(to_email="test@example.com")`
3. Verify firewall allows SMTP port

**中文**:
1. 检查 `.env` 中的 SMTP 配置
2. 测试连接：`test_email_service(to_email="test@example.com")`
3. 验证防火墙允许 SMTP 端口

---

## Development / 开发

### Translation Status / 翻译状态

| Component / 组件 | Status / 状态 | Coverage / 覆盖率 |
|-----------------|--------------|-----------------|
| MCP Tools / MCP 工具 | ✅ Complete | 100% |
| Services / 服务层 | ✅ Complete | 100% |
| Scheduler / 调度器 | ✅ Complete | 100% |
| Code Comments / 代码注释 | 🔄 In Progress | 80% |
| Documentation / 文档 | 🔄 In Progress | 50% |

### Contributing / 贡献

**English**: Pull requests welcome! Please ensure bilingual support (Chinese + English).  
**中文**: 欢迎提交 Pull Request！请确保提供双语支持（中文 + 英文）。

---

## Links / 链接

- [GitHub Repository](https://github.com/jztan/redmine-mcp-server)
- [Translation Progress](TRANSLATION_COMPLETE_REPORT.md)
- [Deployment Guide](DEPLOYMENT_REPORT.md)
- [i18n Configuration](src/redmine_mcp_server/i18n/)

---

**License / 许可证**: MIT  
**Maintainer / 维护者**: OpenJaw  
**Contact / 联系**: jingzheng.tan@gmail.com
