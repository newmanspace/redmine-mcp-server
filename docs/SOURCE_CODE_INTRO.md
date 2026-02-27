# Redmine MCP Server - 源代码介绍

**更新时间**: 2026-02-27 20:45  
**代码位置**: `/docker/redmine-mcp-server/src/redmine_mcp_server/`

---

## 一、目录结构

```
src/redmine_mcp_server/
├── main.py                      # 主入口文件 (4.0K)
├── redmine_handler.py           # MCP 工具实现 (91K) ⭐核心
├── redmine_warehouse.py         # 数仓数据访问 (21K) ⭐核心
├── redmine_scheduler.py         # 定时调度器 (15K)
├── dev_test_analyzer.py         # 开发/测试分析 (19K)
├── ads_reports.py               # ADS 报表工具 (9.7K)
├── ads_scheduler.py             # ADS 报表调度 (13K)
├── data_quality_monitor.py      # 数据质量监控 (14K)
├── subscriptions.py             # 订阅管理 (9.9K)
├── subscription_reporter.py     # 订阅报告 (15K)
├── backfill_sync.py             # 历史数据回填 (11K)
├── daily_stats.py               # 每日统计 (3.9K)
├── file_manager.py              # 文件管理 (4.2K)
└── __init__.py                  # 包初始化
```

**总代码量**: 约 230K (约 6000 行)

---

## 二、核心模块介绍

### 2.1 main.py - 主入口

**功能**: MCP 服务器启动、初始化调度器、配置监控

### 2.2 redmine_handler.py - MCP 工具实现 (91K) ⭐

**功能**: 实现 30+ 个 MCP 工具

**工具分类**:
- Issue 管理：5 个工具
- 项目管理：2 个工具
- Wiki 管理：4 个工具
- 订阅管理：5 个工具
- 数仓同步：4 个工具
- 统计分析：7 个工具
- 贡献者分析：4 个工具
- ADS 报表：5 个工具

### 2.3 redmine_warehouse.py - 数仓数据访问 (21K) ⭐

**功能**: PostgreSQL 数仓数据访问层

**核心类**: `DataWarehouse`

**主要方法**:
- `upsert_issues_batch()` - 批量插入/更新 Issue
- `get_project_daily_stats()` - 获取项目统计
- `get_issue_contributors()` - 获取贡献者列表
- `get_user_workload()` - 获取用户工作量

### 2.4 redmine_scheduler.py - 定时调度器 (15K)

**调度任务**:
- 增量同步：每 10 分钟
- 全量同步：每天
- 历史回填：手动

### 2.5 dev_test_analyzer.py - 开发/测试分析 (19K)

**分析逻辑**:
- 开发人员：将状态改为"已解决"的人
- 测试人员：将状态改为"已关闭"的人
- 实施人员：将状态从"新建"改为"进行中"的人

### 2.6 ads_reports.py - ADS 报表工具 (9.7K)

**功能**: 生成贡献者报表、项目健康度报告

### 2.7 ads_scheduler.py - ADS 报表调度 (13K)

**调度任务**:
- 每日 09:00: 项目健康度报告
- 每月 01 日：贡献者报表、用户工作量报表

### 2.8 data_quality_monitor.py - 数据质量监控 (14K)

**监控指标**: 表行数、数据新鲜度、空值率、一致性

### 2.9 subscriptions.py - 订阅管理 (9.9K)

**功能**: 项目订阅管理

### 2.10 subscription_reporter.py - 订阅报告 (15K)

**功能**: 生成订阅项目报告

### 2.11 backfill_sync.py - 历史数据回填 (11K)

**功能**: 回填历史 Issue 数据

### 2.12 daily_stats.py - 每日统计 (3.9K)

**功能**: 生成每日统计数据

### 2.13 file_manager.py - 文件管理 (4.2K)

**功能**: 附件下载、存储管理、过期清理

---

## 三、代码统计

| 模块 | 行数 | 占比 |
|------|------|------|
| redmine_handler.py | ~2400 | 40% |
| redmine_warehouse.py | ~550 | 9% |
| redmine_scheduler.py | ~400 | 7% |
| dev_test_analyzer.py | ~500 | 8% |
| 其他模块 | ~2150 | 36% |
| **总计** | **~6000** | **100%** |

---

## 四、测试

**测试文件位置**: `/docker/redmine-mcp-server/tests/`

**测试覆盖**: 单元测试 20+ 个文件、集成测试、安全测试

**运行测试**: `pytest tests/ -v`

---

**维护者**: OpenJaw  
**项目**: Redmine MCP Server  
**文档位置**: `/docker/redmine-mcp-server/docs/SOURCE_CODE_INTRO.md`
