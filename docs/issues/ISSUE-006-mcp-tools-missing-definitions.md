# ISSUE-006 - MCP Tools Missing Function and Exception Definitions

**Created**: 2026-03-01  
**Severity**: 🔴 High  
**Status**: ⏳ Pending  
**Affected Files**: `src/redmine_mcp_server/mcp/tools/issue_tools.py`, `src/redmine_mcp_server/mcp/tools/search_tools.py`  
**Redmine Issue**: #77867

---

## Problem Description

Multiple MCP tools fail due to undefined functions and exception classes, preventing core functionality like Issue queries and Wiki queries from working.

**Error Messages**:
```
name '_ensure_cleanup_started' is not defined
name 'VersionMismatchError' is not defined
```

**Logs**:
```
Error executing tool get_redmine_issue: name '_ensure_cleanup_started' is not defined
Error executing tool list_my_redmine_issues: name '_ensure_cleanup_started' is not defined
Error executing tool get_redmine_wiki_page: name '_ensure_cleanup_started' is not defined
Error executing tool search_entire_redmine: name 'VersionMismatchError' is not defined
```

---

## Root Cause Analysis

### 1. Missing Function: `_ensure_cleanup_started()`

**Problem Files**:
- `src/redmine_mcp_server/mcp/tools/issue_tools.py` - Lines 38, 143

**Problem Code**:
```python
@mcp.tool()
async def get_redmine_issue(
    issue_id: int, include_journals: bool = True, include_attachments: bool = True
) -> Dict[str, Any]:
    """Retrieve a specific Redmine issue by ID."""
    if not redmine:
        return {"error": "Redmine client not initialized."}

    # Ensure cleanup task is started (lazy initialization)
    await _ensure_cleanup_started()  # ← Function not defined!
    try:
        # ...
```

**Analysis**: The function `_ensure_cleanup_started()` is called but never defined or imported in the module.

### 2. Missing Exception: `VersionMismatchError`

**Problem Files**:
- `src/redmine_mcp_server/mcp/tools/search_tools.py` (assumed based on error)

**Problem Code**:
```python
try:
    # ... search logic ...
except VersionMismatchError as e:  # ← Exception not defined!
    # ...
```

**Analysis**: The exception class `VersionMismatchError` is used but not imported from the redmine library or defined locally.

---

## Solution

### 1. Add Missing Function Definition

**Files Modified**:
- `src/redmine_mcp_server/mcp/tools/issue_tools.py`

**Fix**: Add the missing function at module level:

```python
# Add at top of file with other imports
from ...services.cleanup_service import ensure_cleanup_started as _ensure_cleanup_started

# OR define inline:
_cleanup_task_started = False

async def _ensure_cleanup_started():
    """Ensure the cleanup task is started (lazy initialization)."""
    global _cleanup_task_started
    if not _cleanup_task_started:
        # Start cleanup task
        _cleanup_task_started = True
```

### 2. Import Missing Exception Class

**Files Modified**:
- `src/redmine_mcp_server/mcp/tools/search_tools.py`

**Fix**: Add proper import:

```python
# Add to imports
from redmine.exceptions import VersionMismatchError

# OR define locally if not available:
class VersionMismatchError(Exception):
    """Raised when there's a version mismatch."""
    pass
```

---

## Verification Steps

```bash
# 1. Test get_redmine_issue
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_redmine_issue","arguments":{"issue_id":77849}}}'

# 2. Test list_my_redmine_issues
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_my_redmine_issues","arguments":{"filters":{"limit":10}}}}'

# 3. Test search_entire_redmine
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_entire_redmine","arguments":{"query":"新顺","limit":10}}}'
```

**Expected Result**:
- Tools execute without `name is not defined` errors
- Proper data returned or appropriate error messages

**Actual Result** (before fix):
- Returns Python name errors

---

## Prevention

### 1. Code Review Checklist
- [ ] All function calls reference defined functions
- [ ] All exception classes are imported or defined
- [ ] Run `python -m py_compile` on all modules before commit
- [ ] Check for undefined names with `flake8` or similar linter

### 2. Automated Tests
```python
# test_issue_tools.py
async def test_get_redmine_issue_imports():
    """Verify all required functions are importable."""
    from redmine_mcp_server.mcp.tools.issue_tools import (
        get_redmine_issue,
        list_my_redmine_issues,
        _ensure_cleanup_started,  # This should exist
    )
    assert callable(_ensure_cleanup_started)
```

### 3. CI/CD Checks
```yaml
# .github/workflows/validate-imports.yml
- name: Validate Python imports
  run: |
    python -m py_compile src/redmine_mcp_server/mcp/tools/*.py
    flake8 src/redmine_mcp_server/mcp/tools/ --select=F821,F823
```

---

## Impact Analysis

**Affected Tools** (6 total):
| Tool | Impact |
|------|--------|
| `get_redmine_issue` | Cannot retrieve issue details |
| `list_my_redmine_issues` | Cannot list user's issues |
| `get_redmine_wiki_page` | Cannot fetch wiki pages |
| `search_entire_redmine` | Cannot search across Redmine |

**Severity**: 🔴 High - Core functionality completely broken

---

**Reported By**: OpenClaw (Jaw)  
**Fixed By**: [Pending]  
**Fixed Date**: [Pending]  
**Redmine Issue**: http://redmine.fa-software.com/issues/77867

---

## Related Issues

- [ISSUE-005](./ISSUE-005-scheduler-import-error.md) - Similar import error pattern
- [ISSUE-001](./ISSUE-001-import-path-error.md) - Import path resolution

---

**Test Report**: `/docker/redmine-mcp-server/docs/issues/2026-03-01_function_test_report.md`
