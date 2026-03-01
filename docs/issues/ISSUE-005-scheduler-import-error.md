# ISSUE-005 - Scheduler Module Import Error

**Created**: 2026-03-01  
**Severity**: 🔴 High  
**Status**: ✅ Fixed  
**Fixed Version**: v0.10.1  
**Fixed Date**: 2026-03-01  
**Fixed By**: qwen-code

---

## 问题描述

调度器模块导入路径错误，导致同步和调度功能完全不可用。

**错误信息**:
```
Error executing tool get_sync_progress: No module named 'redmine_mcp_server.mcp.tools.redmine_scheduler'
```

---

## 根因分析

**问题文件**:
- `src/redmine_mcp_server/mcp/tools/analytics_tools.py`
- `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`

**错误导入**:
```python
from .redmine_scheduler import get_scheduler
```

**实际模块位置**:
```
src/redmine_mcp_server/
├── mcp/
│   └── tools/
│       ├── analytics_tools.py  ← 错误导入位置
│       └── warehouse_tools.py  ← 错误导入位置
└── scheduler/                  ← 实际调度器目录
    ├── ads_scheduler.py
    ├── subscription_scheduler.py
    ├── daily_stats.py
    └── tasks.py
```

**原因**:
- 调度器模块已移动到 `scheduler/` 目录
- 工具文件中的导入路径未更新
- 与 ISSUE-001 类似，都是导入路径错误

---

## 解决方案

### 方案一：修正导入路径（推荐）

**修改文件 1**: `src/redmine_mcp_server/mcp/tools/analytics_tools.py`

```python
# 修改前
from .redmine_scheduler import get_scheduler

# 修改后
from ...scheduler.ads_scheduler import get_scheduler
```

**修改文件 2**: `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`

```python
# 修改前
from .redmine_scheduler import get_scheduler

# 修改后
from ...scheduler.ads_scheduler import get_scheduler
```

### 方案二：创建兼容层（不推荐）

在 `mcp/tools/redmine_scheduler.py` 创建转发模块：
```python
# 兼容层（不推荐）
from ...scheduler.ads_scheduler import get_scheduler
__all__ = ['get_scheduler']
```

---

## 修复命令

```bash
cd /docker/redmine-mcp-server

# 修复 analytics_tools.py
sed -i 's/from \.redmine_scheduler import get_scheduler/from ...scheduler.ads_scheduler import get_scheduler/' src/redmine_mcp_server/mcp/tools/analytics_tools.py

# 修复 warehouse_tools.py
sed -i 's/from \.redmine_scheduler import get_scheduler/from ...scheduler.ads_scheduler import get_scheduler/' src/redmine_mcp_server/mcp/tools/warehouse_tools.py

# 验证修改
git diff src/redmine_mcp_server/mcp/tools/

# 重新构建并重启
docker compose build redmine-mcp-server
docker compose restart redmine-mcp-server
```

---

## 验证步骤

```bash
# 1. 测试同步进度查询
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_sync_progress","arguments":{}}}'

# 2. 测试触发全量同步
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"trigger_full_sync","arguments":{"project_id":341}}}'

# 3. 测试订阅调度
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_subscription_scheduler_status","arguments":{}}}'
```

预期返回 JSON 结果，而非模块导入错误。

---

## 如何避免

### 1. 模块重构检查清单

当移动或重命名模块时：
- [ ] 更新所有导入该模块的文件
- [ ] 运行全局搜索确认无遗漏
- [ ] 更新相关文档
- [ ] 运行测试套件

### 2. 使用绝对导入

```python
# 相对导入（容易出错）
from .redmine_scheduler import get_scheduler
from ..scheduler import get_scheduler

# 绝对导入（更清晰）
from redmine_mcp_server.scheduler.ads_scheduler import get_scheduler
```

### 3. 添加导入测试

```python
# tests/test_imports.py
def test_all_imports_work():
    """测试所有模块导入正常"""
    from redmine_mcp_server.mcp.tools.analytics_tools import *
    from redmine_mcp_server.mcp.tools.warehouse_tools import *
    from redmine_mcp_server.scheduler.ads_scheduler import get_scheduler
    # 所有导入应成功，无 ImportError
```

### 4. CI/CD 添加导入检查

```yaml
# .github/workflows/lint.yml
- name: Check imports
  run: |
    python -c "from redmine_mcp_server.mcp.tools.analytics_tools import *"
    python -c "from redmine_mcp_server.mcp.tools.warehouse_tools import *"
    python -c "from redmine_mcp_server.scheduler.ads_scheduler import get_scheduler"
```

### 5. 使用 IDE 重构工具

使用 PyCharm 或 VSCode 的重构功能：
- Right-click module → Refactor → Move
- IDE automatically updates all import paths
- More reliable than manual changes

---

## Related Files

- Fixed files:
  - `src/redmine_mcp_server/mcp/tools/analytics_tools.py`
  - `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`
- Actual module: `src/redmine_mcp_server/scheduler/ads_scheduler.py`

---

## Related Issues

- [ISSUE-001](./ISSUE-001-import-path-error.md) - Similar import path error

---

## ✅ Resolution

**Fix Applied**:
```bash
# Fix import paths
sed -i 's/from \.redmine_scheduler import get_scheduler/from ...scheduler.ads_scheduler import get_scheduler/' analytics_tools.py
sed -i 's/from \.redmine_scheduler import get_scheduler/from ...scheduler.ads_scheduler import get_scheduler/' warehouse_tools.py
```

**Verification**:
- ✅ analytics_tools imports work
- ✅ warehouse_tools imports work
- ✅ All unit tests pass (86 tests)
- ✅ All service tests pass (29 tests)

---

**Reported By**: Jaw  
**Report Date**: 2026-03-01  
**Fixed By**: qwen-code  
**Fixed Date**: 2026-03-01  
**Fixed Commit**: 9dcc4ec
