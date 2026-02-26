# Redmine MCP 功能文档索引

本目录包含 Redmine MCP Server 所有功能的详细说明文档。

---

## 📋 功能列表

### ✅ 已发布功能

| 功能 | 状态 | 版本 | 文档 |
|------|------|------|------|
| **项目订阅** | ✅ 已发布 | v1.0 | [功能描述](./01-subscription-feature.md) \| [概要设计](./01-subscription-design.md) |
| **数仓集成** | ✅ 已发布 | v1.0 | [使用指南](../SUBSCRIPTION_GUIDE.md) |
| **日报系统** | ✅ 已发布 | v1.0 | [配置文档](../REDMINE_DAILY_REPORT.md) |

---

## 🚀 快速开始

### 新用户

1. **了解功能** → 阅读 [功能描述](./01-subscription-feature.md)
2. **快速上手** → 阅读 [使用指南](../SUBSCRIPTION_GUIDE.md)
3. **配置订阅** → 调用 `subscribe_project` 工具

### 开发者

1. **架构设计** → 阅读 [概要设计](./01-subscription-design.md)
2. **代码位置** → `src/redmine_mcp_server/`
3. **测试脚本** → `scripts/test-subscription.sh`

---

## 📖 文档结构

```
docs/
├── feature/                    # 功能文档目录
│   ├── README.md              # 本文件
│   ├── 01-subscription-feature.md   # 订阅功能描述
│   └── 01-subscription-design.md    # 订阅功能设计
├── SUBSCRIPTION_GUIDE.md      # 订阅使用指南
├── REDMINE_DAILY_REPORT.md    # 日报系统文档
└── tool-reference.md          # 工具参考手册
```

---

## 🛠️ 工具索引

### 订阅管理工具

| 工具 | 说明 | 文档 |
|------|------|------|
| `subscribe_project` | 订阅项目报告 | [功能描述](./01-subscription-feature.md#1-subscribe_project---订阅项目) |
| `unsubscribe_project` | 取消订阅 | [功能描述](./01-subscription-feature.md#2-unsubscribe_project---取消订阅) |
| `list_my_subscriptions` | 查看订阅 | [功能描述](./01-subscription-feature.md#3-list_my_subscriptions---查看我的订阅) |
| `get_subscription_stats` | 订阅统计 | [功能描述](./01-subscription-feature.md#4-get_subscription_stats---订阅统计) |
| `generate_subscription_report` | 生成报告 | [功能描述](./01-subscription-feature.md#5-generate_subscription_report---生成报告) |

### 其他工具

详见 [工具参考手册](../tool-reference.md)

---

## 🔍 搜索文档

### 按主题

- **订阅配置** → [功能描述](./01-subscription-feature.md#配置说明)
- **报告格式** → [功能描述](./01-subscription-feature.md#报告内容)
- **架构设计** → [概要设计](./01-subscription-design.md#架构设计)
- **数据流** → [概要设计](./01-subscription-design.md#数据流)

### 按问题

- **如何使用** → [功能描述 - 快速开始](./01-subscription-feature.md#快速开始)
- **配置推送时间** → [功能描述 - 推送配置](./01-subscription-feature.md#推送配置)
- **故障排查** → [概要设计 - 故障排查](./01-subscription-design.md#故障排查)

---

## 📞 获取帮助

### 文档问题

- 文档缺失 → 提交 Issue 到 GitHub
- 文档错误 → 提交 PR 修正

### 使用问题

- 功能咨询 → 在钉钉/Telegram 中提问
- 技术支持 → 查看 [故障排查](./01-subscription-design.md#故障排查)

### 代码问题

- Bug 报告 → GitHub Issues
- 功能建议 → GitHub Discussions

---

## 📈 更新日志

### v1.0 (2026-02-26)

- ✅ 发布项目订阅功能
- ✅ 5 个订阅管理工具
- ✅ 简要/详细报告生成
- ✅ 钉钉/Telegram 推送支持
- ✅ 完整文档

---

## 🔗 相关链接

- **GitHub**: https://github.com/newmanspace/redmine-mcp-server
- **文档**: /docker/redmine-mcp-server/docs/
- **代码**: /docker/redmine-mcp-server/src/redmine_mcp_server/

---

**最后更新**: 2026-02-26  
**维护者**: OpenJaw <openjaw@gmail.com>
