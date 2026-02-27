# Redmine MCP 数仓 - 文档索引

**项目位置**: `/docker/redmine-mcp-server/`  
**最后更新**: 2026-02-27

---

## 📚 文档分类

### 核心架构文档

| 文档 | 说明 | 用途 |
|------|------|------|
| [`MCP_WAREHOUSE_SUMMARY.md`](./MCP_WAREHOUSE_SUMMARY.md) | 架构总结 | **快速了解整体架构** |
| [`MCP_WAREHOUSE_ARCHITECTURE.md`](./MCP_WAREHOUSE_ARCHITECTURE.md) | 架构设计 | 详细架构设计文档 |
| [`IMPLEMENTED_FEATURES.md`](./IMPLEMENTED_FEATURES.md) | 已实现功能 | **当前功能清单** |

### 数仓设计文档

| 文档 | 说明 | 用途 |
|------|------|------|
| [`redmine-warehouse-schema.md`](./redmine-warehouse-schema.md) | 表结构设计 | 完整数据库表设计 |
| [`redmine-warehouse-tables.md`](./redmine-warehouse-tables.md) | 表分类清单 | 按层分类的表结构 |
| [`redmine-warehouse-guide.md`](./redmine-warehouse-guide.md) | 使用指南 | 数仓使用手册 |

### 功能设计文档

| 文档 | 说明 | 用途 |
|------|------|------|
| [`feature/01-subscription-feature.md`](./feature/01-subscription-feature.md) | 订阅功能 | 项目订阅机制 |
| [`feature/02-data-sync.md`](./feature/02-data-sync.md) | 数据同步 | 同步机制设计 |
| [`feature/03-dev-test-analyzer.md`](./feature/03-dev-test-analyzer.md) | 开发/测试分析 | 工作量分析功能 |

### 扩展方案文档

| 文档 | 说明 | 用途 |
|------|------|------|
| [`WAREHOUSE_CONTRIBUTOR_EXTENSION.md`](./WAREHOUSE_CONTRIBUTOR_EXTENSION.md) | 贡献者扩展 | **如何扩展贡献者分析** |
| [`redmine-issue-analysis-schema.md`](./redmine-issue-analysis-schema.md) | Issue 分析表结构 | 贡献者分析表设计 |
| [`redmine-issue-analysis-summary.md`](./redmine-issue-analysis-summary.md) | Issue 分析方案 | 贡献者分析方案 |

### 运维文档

| 文档 | 说明 | 用途 |
|------|------|------|
| [`WAREHOUSE_SYNC.md`](./WAREHOUSE_SYNC.md) | 数仓同步机制 | 同步配置和运维 |
| [`SUBSCRIPTION_GUIDE.md`](./SUBSCRIPTION_GUIDE.md) | 订阅指南 | 用户订阅说明 |
| [`tool-reference.md`](./tool-reference.md) | 工具参考 | MCP 工具完整列表 |
| [`troubleshooting.md`](./troubleshooting.md) | 故障排查 | 常见问题解决 |

---

## 🚀 快速导航

### 新手入门

1. 阅读 [`MCP_WAREHOUSE_SUMMARY.md`](./MCP_WAREHOUSE_SUMMARY.md) 了解架构
2. 查看 [`IMPLEMENTED_FEATURES.md`](./IMPLEMENTED_FEATURES.md) 了解已实现功能
3. 参考 [`WAREHOUSE_SYNC.md`](./WAREHOUSE_SYNC.md) 配置同步

### 开发人员

1. 阅读 [`MCP_WAREHOUSE_ARCHITECTURE.md`](./MCP_WAREHOUSE_ARCHITECTURE.md) 了解架构设计
2. 查看 [`redmine-warehouse-schema.md`](./redmine-warehouse-schema.md) 了解表结构
3. 参考 [`WAREHOUSE_CONTRIBUTOR_EXTENSION.md`](./WAREHOUSE_CONTRIBUTOR_EXTENSION.md) 进行扩展

### 运维人员

1. 阅读 [`WAREHOUSE_SYNC.md`](./WAREHOUSE_SYNC.md) 了解同步机制
2. 查看 [`troubleshooting.md`](./troubleshooting.md) 解决常见问题
3. 参考 [`tool-reference.md`](./tool-reference.md) 使用 MCP 工具

---

## 📁 项目结构

```
/docker/redmine-mcp-server/          ← 完整项目目录
├── src/redmine_mcp_server/
│   ├── main.py                    # MCP 入口
│   ├── redmine_handler.py         # MCP Tools 实现 (26 个工具)
│   ├── redmine_warehouse.py       # 数仓访问层 ✅
│   ├── redmine_scheduler.py       # 定时同步调度器 ✅
│   └── dev_test_analyzer.py       # 开发/测试分析器 ✅
├── docs/                          # 📚 所有文档
│   ├── README.md                  ← 文档索引
│   ├── MCP_WAREHOUSE_SUMMARY.md   ← 架构总结
│   ├── IMPLEMENTED_FEATURES.md    ← 已实现功能
│   └── ...
├── scripts/
│   ├── manual-sync.py             # 手动同步脚本
│   ├── analyze_all_history.py     # 历史分析
│   └── batch_analyze_history.py   # 批量分析
├── init-scripts/                  # 🗄️ 数据库初始化脚本
│   └── 01-schema.sql
├── data/                          # 💾 SQLite 数据库
│   └── redmine_warehouse.db
└── docker-compose.yml
```

---

## 🗄️ 数据库

**数仓完全整合在 MCP Server 中**，使用 SQLite 数据库：

```
/docker/redmine-mcp-server/data/redmine_warehouse.db
```

**初始化脚本**: `/docker/redmine-mcp-server/init-scripts/`

---

## 📊 核心数据流

```
Redmine API
    ↓
MCP Server (每 10 分钟增量同步)
    ↓
PostgreSQL Warehouse
    ↓
MCP Tools (查询统计)
```

---

## 🛠️ 核心 MCP 工具

| 分类 | 工具 | 说明 |
|------|------|------|
| **统计** | `get_project_daily_stats` | 项目每日统计 |
| **分析** | `analyze_dev_tester_workload` | 开发/测试工作量分析 |
| **同步** | `trigger_full_sync` | 触发全量同步 |
| **订阅** | `subscribe_project` | 订阅项目 |

---

## 📈 后续扩展

### 短期（1-2 周）

- [ ] Issue 贡献者分析（按角色分类）
- [ ] 项目角色分布统计
- [ ] 用户工作量跨项目统计

### 中期（1 个月）

- [ ] Issue 质量报表
- [ ] 团队负载分析
- [ ] 趋势分析

### 长期（3 个月）

- [ ] 预测分析
- [ ] 自动化报告
- [ ] Grafana 可视化

---

## 🔗 相关链接

- **MCP Server**: `/docker/redmine-mcp-server/`
- **Warehouse DB**: `/docker/redmine-warehouse/`
- **Redmine**: `http://redmine.fa-software.com`

---

**维护者**: OpenJaw <openjaw@gmail.com>
