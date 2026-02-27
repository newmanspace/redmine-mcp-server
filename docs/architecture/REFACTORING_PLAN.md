# Redmine MCP Handler 重构方案

**当前状态**: 2670 行，91K，30 个 MCP 工具  
**目标**: 拆分为多个模块，每个模块负责一个功能领域

---

## 一、当前问题分析

### 1.1 代码量统计

| 指标 | 数值 |
|------|------|
| 总行数 | 2670 行 |
| 文件大小 | 91K |
| MCP 工具数 | 30 个 |
| 平均每个工具 | 89 行 |

### 1.2 工具分布

| 行号范围 | 功能类别 | 工具数 |
|----------|---------|--------|
| 760-1026 | Issue 管理 | 3 |
| 1027-1210 | 项目管理 | 1 |
| 1211-1401 | Wiki 管理 | 4 |
| 1402-1531 | 附件管理 | 2 |
| 1532-1745 | 全局搜索 | 1 |
| 1746-2035 | 订阅管理 | 5 |
| 2036-2213 | 数仓同步 | 4 |
| 2214-2451 | 统计分析 | 6 |
| 2452-2568 | 贡献者分析 | 4 |
| 2569-2670 | ADS 报表 | 5 |

### 1.3 问题

1. **文件过大**: 91K 难以维护
2. **职责不清**: 所有功能混在一起
3. **依赖复杂**: 导入关系混乱
4. **测试困难**: 单元测试覆盖困难

---

## 二、重构方案

### 2.1 模块拆分

```
src/redmine_mcp_server/
├── main.py
├── redmine_handler.py (保留基础框架，约 100 行)
├── tools/
│   ├── __init__.py
│   ├── issue_tools.py          # Issue 管理 (3 个工具)
│   ├── project_tools.py        # 项目管理 (1 个工具)
│   ├── wiki_tools.py           # Wiki 管理 (4 个工具)
│   ├── attachment_tools.py     # 附件管理 (2 个工具)
│   ├── search_tools.py         # 搜索 (1 个工具)
│   ├── subscription_tools.py   # 订阅管理 (5 个工具)
│   ├── warehouse_tools.py      # 数仓同步 (4 个工具)
│   ├── analytics_tools.py      # 统计分析 (6 个工具)
│   ├── contributor_tools.py    # 贡献者分析 (4 个工具)
│   └── ads_tools.py            # ADS 报表 (5 个工具)
```

### 2.2 各模块职责

#### tools/issue_tools.py (~300 行)
- `get_redmine_issue()`
- `list_my_redmine_issues()`
- `search_redmine_issues()`

#### tools/project_tools.py (~100 行)
- `list_redmine_projects()`
- `summarize_project_status()`

#### tools/wiki_tools.py (~400 行)
- `get_redmine_wiki_page()`
- `create_redmine_wiki_page()`
- `update_redmine_wiki_page()`
- `delete_redmine_wiki_page()`

#### tools/attachment_tools.py (~200 行)
- `get_redmine_attachment_download_url()`
- `cleanup_attachment_files()`

#### tools/search_tools.py (~150 行)
- `search_entire_redmine()`

#### tools/subscription_tools.py (~500 行)
- `subscribe_project()`
- `unsubscribe_project()`
- `list_my_subscriptions()`
- `get_subscription_stats()`
- `generate_subscription_report()`

#### tools/warehouse_tools.py (~400 行)
- `trigger_full_sync()`
- `trigger_progressive_sync()`
- `get_sync_progress()`
- `backfill_historical_data()`

#### tools/analytics_tools.py (~600 行)
- `get_project_daily_stats()`
- `analyze_dev_tester_workload()`

#### tools/contributor_tools.py (~400 行)
- `analyze_issue_contributors()`
- `get_project_role_distribution()`
- `get_user_workload()`
- `trigger_contributor_sync()`

#### tools/ads_tools.py (~500 行)
- `generate_contributor_report()`
- `generate_project_health_report()`
- `get_contributor_ranking()`
- `get_project_health_latest()`

### 2.3 主文件精简

**redmine_handler.py** (保留约 100 行):
```python
"""
Redmine MCP Handler - Main Entry Point
"""

from mcp.server.fastmcp import FastMCP
from . import redmine

# 初始化 MCP 服务器
mcp = FastMCP("Redmine")

# 导入所有工具模块（自动注册到 mcp）
from .tools import (
    issue_tools,
    project_tools,
    wiki_tools,
    attachment_tools,
    search_tools,
    subscription_tools,
    warehouse_tools,
    analytics_tools,
    contributor_tools,
    ads_tools,
)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## 三、重构步骤

### 3.1 准备阶段
1. 备份当前代码
2. 确保测试覆盖
3. 创建 tools 目录

### 3.2 拆分阶段
1. 创建 tools 目录结构
2. 逐个提取工具模块
3. 精简主文件

### 3.3 测试阶段
1. 单元测试
2. 集成测试
3. 功能测试

### 3.4 验证阶段
```bash
# 验证模块导入
python3 -c "from redmine_mcp_server.tools import issue_tools"

# 验证 MCP 工具注册
curl -X POST http://localhost:8000/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## 四、预期效果

### 4.1 代码量对比

| 指标 | 重构前 | 重构后 | 改善 |
|------|--------|--------|------|
| 主文件大小 | 91K | ~10K | -89% |
| 主文件行数 | 2670 | ~100 | -96% |
| 最大模块 | 91K | ~6K | -93% |
| 模块数量 | 1 | 11 | +1000% |

### 4.2 维护性提升

- ✅ 职责清晰
- ✅ 易于测试
- ✅ 易于扩展
- ✅ 易于理解

---

## 五、实施计划

### 第一阶段（1-2 天）
- [ ] 创建 tools 目录结构
- [ ] 提取 Issue/Project/Wiki 工具
- [ ] 测试基础功能

### 第二阶段（1-2 天）
- [ ] 提取附件/搜索/订阅工具
- [ ] 测试完整流程

### 第三阶段（1-2 天）
- [ ] 提取数仓/分析/贡献者工具
- [ ] 提取 ADS 报表工具
- [ ] 完整测试

### 第四阶段（1 天）
- [ ] 精简主文件
- [ ] 更新文档
- [ ] 部署验证

---

**维护者**: OpenJaw  
**项目**: Redmine MCP Server  
**文档位置**: `/docker/redmine-mcp-server/docs/REFACTORING_PLAN.md`
