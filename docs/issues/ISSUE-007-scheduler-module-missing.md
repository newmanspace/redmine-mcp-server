# ISSUE-007 - MCP Scheduler Module Missing

**Created**: 2026-03-01  
**Severity**: 🔴 High  
**Status**: ⏳ Pending  
**Affected Files**: `src/redmine_mcp_server/mcp/tools/analytics_tools.py`, `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`  
**Redmine Issue**: [待创建]

---

## Problem Description

The scheduler module is missing or has incorrect import paths, causing MCP tools that query sync progress and scheduler status to fail.

**Error Messages**:
```
No module named 'redmine_mcp_server.mcp.tools.redmine_scheduler'
No module named 'redmine_mcp_server.mcp.scheduler'
```

**Logs**:
```
Error executing tool get_sync_progress: No module named 'redmine_mcp_server.mcp.tools.redmine_scheduler'
Error executing tool get_subscription_scheduler_status: No module named 'redmine_mcp_server.mcp.scheduler'
```

---

## Root Cause Analysis

### Missing Module: `redmine_scheduler`

**Problem Files**:
- `src/redmine_mcp_server/mcp/tools/analytics_tools.py`
- `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`

**Problem Code**:
```python
# Incorrect import path
from .redmine_scheduler import get_scheduler
# OR
from ...scheduler.ads_scheduler import get_scheduler  # May be wrong path
```

**Analysis**: The scheduler module exists but import paths are incorrect or the module structure has changed.

---

## Solution

### 1. Verify Scheduler Module Location

```bash
# Find the actual scheduler module
find /docker/redmine-mcp-server -name "*scheduler*" -type f
```

### 2. Fix Import Paths

**Files Modified**:
- `src/redmine_mcp_server/mcp/tools/analytics_tools.py`
- `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`

**Fix**: Update imports to correct path:

```python
# Correct import (verify actual path first)
from ...scheduler.ads_scheduler import get_scheduler
# OR
from redmine_mcp_server.scheduler.ads_scheduler import get_scheduler
```

---

## Verification Steps

```bash
# 1. Test get_sync_progress
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_sync_progress","arguments":{}}}'

# 2. Test get_subscription_scheduler_status
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_subscription_scheduler_status","arguments":{}}}'
```

**Expected Result**:
- Tools return scheduler status without import errors

---

## Impact Analysis

**Affected Tools** (2 total):
| Tool | Impact |
|------|--------|
| `get_sync_progress` | Cannot query sync progress |
| `get_subscription_scheduler_status` | Cannot query scheduler status |

**Severity**: 🔴 High - Monitoring functionality broken

---

**Reported By**: OpenClaw (Jaw)  
**Fixed By**: [Pending]  
**Fixed Date**: [Pending]

---

## Related Issues

- [ISSUE-005](./ISSUE-005-scheduler-import-error.md) - Previous scheduler import fix (may be incomplete)
- [ISSUE-006](./ISSUE-006-mcp-tools-missing-definitions.md) - Similar missing definition pattern

---

**Test Report**: `/docker/redmine-mcp-server/docs/issues/2026-03-01_function_test_report.md`
