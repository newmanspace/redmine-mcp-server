# ISSUE-001 - Python 导入路径错误

**创建日期**: 2026-02-28  
**严重性**: 🔴 高  
**状态**: ✅ 已修复  
**影响范围**: 订阅推送、附件工具、ODS 同步

---

## 问题描述

多个工具文件使用了 `_handle_redmine_error` 函数但未导入，导致工具调用失败。

**错误信息**:
```
Error executing tool list_redmine_projects: name '_handle_redmine_error' is not defined
```

---

## 根因分析

**问题文件**:
- `src/redmine_mcp_server/mcp/tools/issue_tools.py`
- `src/redmine_mcp_server/mcp/tools/wiki_tools.py`
- `src/redmine_mcp_server/mcp/tools/subscription_tools.py`
- `src/redmine_mcp_server/mcp/tools/project_tools.py`
- `src/redmine_mcp_server/mcp/tools/search_tools.py`

**原因**: 
- `_handle_redmine_error` 函数定义在 `redmine_handler.py`
- 工具文件使用了该函数但未导入
- 代码审查时未发现此问题

---

## 解决方案

**修复方式**: 在每个使用 `_handle_redmine_error` 的文件中添加导入语句

```python
# 在 import 部分添加
from ...redmine_handler import _handle_redmine_error
```

**修复命令**:
```bash
cd /docker/redmine-mcp-server
sed -i '/from ..server import mcp, redmine, logger/a from ...redmine_handler import _handle_redmine_error' src/redmine_mcp_server/mcp/tools/*.py
```

**验证**:
```bash
docker compose build redmine-mcp-server
docker compose restart redmine-mcp-server
curl -X POST http://localhost:8000/mcp ... list_redmine_projects ...
```

---

## 如何避免

### 1. 代码审查清单

在 PR/MR 中添加检查项：
- [ ] 所有使用的函数都已导入
- [ ] 相对导入路径正确（`..` vs `...`）

### 2. 使用静态分析工具

```bash
# 安装 pylint
pip install pylint

# 运行检查
pylint src/redmine_mcp_server/mcp/tools/
```

### 3. 添加 CI 检查

在 `.github/workflows/ci.yml` 中添加：
```yaml
- name: Check imports
  run: |
    python -m py_compile src/redmine_mcp_server/mcp/tools/*.py
```

### 4. 统一导入规范

在 `__init__.py` 中导出常用函数：
```python
# src/redmine_mcp_server/mcp/__init__.py
from ..redmine_handler import _handle_redmine_error

__all__ = ['_handle_redmine_error']
```

然后工具文件可以统一导入：
```python
from .. import _handle_redmine_error
```

---

## 相关文件

- 修复文件：`src/redmine_mcp_server/mcp/tools/*.py`
- 函数定义：`src/redmine_mcp_server/redmine_handler.py`

---

**修复人**: qwen-code  
**修复日期**: 2026-02-28  
**验证人**: Jaw
