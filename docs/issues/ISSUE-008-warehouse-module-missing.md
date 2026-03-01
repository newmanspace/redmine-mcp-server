# ISSUE-008 - MCP Warehouse Module Missing

**Created**: 2026-03-01  
**Severity**: 🔴 High  
**Status**: ⏳ Pending  
**Affected Files**: `src/redmine_mcp_server/mcp/tools/redmine_warehouse.py` (module missing)  
**Redmine Issue**: [待创建]

---

## Problem Description

The warehouse module (`redmine_warehouse`) is not deployed or not properly configured, causing all data warehouse dependent MCP tools to fail with import errors.

**Error Messages**:
```
No module named 'redmine_mcp_server.mcp.tools.redmine_warehouse'
```

**Logs**:
```
Error executing tool get_project_daily_stats: No module named 'redmine_mcp_server.mcp.tools.redmine_warehouse'
Error executing tool get_project_role_distribution: No module named 'redmine_mcp_server.mcp.tools.redmine_warehouse'
Error executing tool analyze_issue_contributors: No module named 'redmine_mcp_server.mcp.tools.redmine_warehouse'
Error executing tool get_user_workload: No module named 'redmine_mcp_server.mcp.tools.redmine_warehouse'
```

---

## Root Cause Analysis

### Missing Module: `redmine_warehouse`

**Problem Files**:
- Module `src/redmine_mcp_server/mcp/tools/redmine_warehouse.py` does not exist

**Analysis**: The warehouse module was not deployed with the MCP server, or the PostgreSQL data warehouse backend is not configured.

### Additional Dependencies

**Database Requirements**:
- PostgreSQL database for ODS layer
- ODS tables: `ods_issues`, `ods_projects`, `ods_journals`, `ods_users`
- Data sync jobs to populate warehouse

---

## Solution

### 1. Deploy Warehouse Module

**Action**: Copy or create the warehouse module:

```bash
# Check if module exists elsewhere
find /docker/redmine-mcp-server -name "redmine_warehouse.py" -o -name "*warehouse*.py"

# If exists, copy to correct location
cp /path/to/redmine_warehouse.py src/redmine_mcp_server/mcp/tools/

# If not, need to create from source or backup
```

### 2. Configure PostgreSQL Connection

**Files to Create/Update**:
- `.env` - Add PostgreSQL connection string
- `src/redmine_mcp_server/db/warehouse_db.py` - Database connection

**Configuration**:
```python
# PostgreSQL connection
WAREHOUSE_DB_URL = "postgresql://user:pass@host:5432/redmine_warehouse"
```

### 3. Initialize ODS Tables

```sql
-- Create ODS layer tables
CREATE TABLE IF NOT EXISTS ods_issues (...);
CREATE TABLE IF NOT EXISTS ods_projects (...);
CREATE TABLE IF NOT EXISTS ods_journals (...);
CREATE TABLE IF NOT EXISTS ods_users (...);
```

### 4. Run Initial Data Sync

```bash
# Trigger full sync to populate warehouse
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"sync_ods_full","arguments":{}}}'
```

---

## Verification Steps

```bash
# 1. Test get_project_daily_stats
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_project_daily_stats","arguments":{"project_id":341}}}'

# 2. Test get_project_role_distribution
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_project_role_distribution","arguments":{"project_id":341}}}'

# 3. Test analyze_issue_contributors
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"analyze_issue_contributors","arguments":{"issue_id":77849}}}'

# 4. Test get_user_workload
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_user_workload","arguments":{"user_id":1427}}}'
```

**Expected Result**:
- Tools return warehouse data without import errors
- ODS sync status shows populated tables

---

## Impact Analysis

**Affected Tools** (4 total):
| Tool | Impact |
|------|--------|
| `get_project_daily_stats` | Cannot get daily statistics |
| `get_project_role_distribution` | Cannot get role distribution |
| `analyze_issue_contributors` | Cannot analyze contributors |
| `get_user_workload` | Cannot get workload stats |

**Severity**: 🔴 High - All analytics/reporting functionality broken

---

**Reported By**: OpenClaw (Jaw)  
**Fixed By**: [Pending]  
**Fixed Date**: [Pending]

---

## Related Issues

- [ISSUE-006](./ISSUE-006-mcp-tools-missing-definitions.md) - Similar missing module pattern
- [ISSUE-005](./ISSUE-005-scheduler-import-error.md) - Module deployment issue

---

**Test Report**: `/docker/redmine-mcp-server/docs/issues/2026-03-01_function_test_report.md`
