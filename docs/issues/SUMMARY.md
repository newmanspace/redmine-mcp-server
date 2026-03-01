# Redmine MCP Server - Issue Summary

**Last Updated**: 2026-03-01  
**Status**: Active Development  
**Total Issues**: 5

---

## 📊 Quick Stats

```
✅ Fixed:   3 (60%)
⏳ Pending: 2 (40%)
🔴 High:   5 (100%)
```

---

## 📋 Issue List

| ID | Title | Severity | Status | Fixed Version |
|----|-------|----------|--------|---------------|
| [001](./ISSUE-001-import-path-error.md) | Python Import Path Error | 🔴 | ✅ Fixed | v0.10.0 |
| [002](./ISSUE-002-redmine-api-param.md) | Redmine API Parameter Name Error | 🔴 | ✅ Fixed | v0.10.0 |
| [003](./ISSUE-003-connection-pool-closed.md) | Subscription Push Connection Pool Bug | 🔴 | ✅ Fixed | v0.10.0 |
| [004](./ISSUE-004-subscription-schema-mismatch.md) | Subscription Table Field Mismatch | 🔴 | ⏳ Pending | - |
| [005](./ISSUE-005-scheduler-import-error.md) | Scheduler Module Import Error | 🔴 | ⏳ Pending | - |

---

## 🎯 Next Actions

### Priority P0 (Immediate)

1. **ISSUE-004** - Subscription Table Field Mismatch
   - **Impact**: Subscription creation/query broken
   - **ETA**: 30 minutes
   - **Fix**: Update field names in subscription_service.py

2. **ISSUE-005** - Scheduler Module Import Error
   - **Impact**: Data sync and scheduling broken
   - **ETA**: 15 minutes
   - **Fix**: Update import paths in tool files

---

## 📝 Recent Activity

### 2026-03-01
- Created ISSUE-005 (Scheduler Import Error)
- Created fix plan for ISSUE-004 and ISSUE-005

### 2026-02-28
- ✅ Fixed ISSUE-001 (Import Path Error)
- ✅ Fixed ISSUE-002 (API Parameter Error)
- ✅ Fixed ISSUE-003 (Connection Pool Bug)
- Created ISSUE-004 (Subscription Schema Mismatch)

---

## 📈 Trend Analysis

### Issue Velocity
```
Week of 2026-02-28:
- Opened: 5
- Closed: 3
- Net Change: +2
```

### Resolution Rate
```
Total Issues:  5
Resolved:      3
Resolution Rate: 60%
Avg Resolution Time: < 1 day
```

---

## 🛠️ Fix History

| Date | Issue | Action | Result |
|------|-------|--------|--------|
| 2026-02-28 | ISSUE-001 | Fixed import paths | ✅ Verified |
| 2026-02-28 | ISSUE-002 | Fixed API param names | ✅ Verified |
| 2026-02-28 | ISSUE-003 | Fixed connection pool lifecycle | ✅ Verified |
| 2026-02-28 | ISSUE-004 | Identified root cause | ⏳ Pending fix |
| 2026-03-01 | ISSUE-005 | Created issue report | ⏳ Pending fix |

---

## 📋 Open Issues Detail

### ISSUE-004: Subscription Table Field Name Mismatch

**Problem**: Code field names don't match database schema

| Code (Old) | Database (New) |
|------------|----------------|
| `frequency` | `report_type` |
| `level` | `report_level` |
| `push_time` | `send_time` |

**Files to Fix**:
- `src/redmine_mcp_server/dws/services/subscription_service.py`

**Fix Command**:
```bash
sed -i 's/"frequency"/"report_type"/g' src/redmine_mcp_server/dws/services/subscription_service.py
sed -i 's/"level"/"report_level"/g' src/redmine_mcp_server/dws/services/subscription_service.py
sed -i 's/"push_time"/"send_time"/g' src/redmine_mcp_server/dws/services/subscription_service.py
```

---

### ISSUE-005: Scheduler Module Import Error

**Problem**: Import path points to non-existent module

**Wrong**:
```python
from .redmine_scheduler import get_scheduler
```

**Correct**:
```python
from ...scheduler.ads_scheduler import get_scheduler
```

**Files to Fix**:
- `src/redmine_mcp_server/mcp/tools/analytics_tools.py`
- `src/redmine_mcp_server/mcp/tools/warehouse_tools.py`

**Fix Command**:
```bash
sed -i 's/from \.redmine_scheduler import get_scheduler/from ...scheduler.ads_scheduler import get_scheduler/' src/redmine_mcp_server/mcp/tools/analytics_tools.py
sed -i 's/from \.redmine_scheduler import get_scheduler/from ...scheduler.ads_scheduler import get_scheduler/' src/redmine_mcp_server/mcp/tools/warehouse_tools.py
```

---

## 🎯 Goals

### Short-term (This Week)
- [ ] Fix ISSUE-004 (Subscription Schema)
- [ ] Fix ISSUE-005 (Scheduler Import)
- [ ] Achieve 100% resolution rate

### Mid-term (Next Week)
- [ ] Add integration tests for subscription flow
- [ ] Add import validation tests
- [ ] Set up CI/CD checks for common issues

### Long-term (This Month)
- [ ] Reduce issue creation rate by 50%
- [ ] Implement automated issue detection
- [ ] Create comprehensive test coverage

---

## 📞 Contact

**Report Tool**: OpenClaw (Jaw)  
**Workspace**: `/docker/redmine-mcp-server`

---

**Last Review**: 2026-03-01  
**Next Review**: 2026-03-02
