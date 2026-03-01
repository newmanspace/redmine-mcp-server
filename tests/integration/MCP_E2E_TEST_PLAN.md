# MCP Server E2E Integration Test Plan

**Version**: 2.0  
**Date**: 2026-03-01  
**Status**: Ready for Implementation  
**CI/CD**: GitHub Actions Compatible

---

## 📋 Test Strategy

### Test Pyramid

```
                    ┌─────────────┐
                   /   E2E Tests   \
                  /  (Real DB +     \
                 /   Mock Redmine)   \
                ├─────────────────────┤
               /   DB Schema Tests    \
              /    (Real Database)     \
             ├──────────────────────────┤
            /   Integration Tests       \
           /    (Mock Database)          \
          ├───────────────────────────────┤
         /      Unit Tests                \
        /       (All Mocked)               \
        └──────────────────────────────────┘
```

### Test Distribution

| Test Layer | Count | Database | Redmine | CI Time |
|------------|-------|----------|---------|---------|
| Unit Tests | 86 | ❌ Mock | ❌ Mock | ~30s |
| Integration (Mock DB) | 12 | ❌ Mock | ❌ Mock | ~20s |
| DB Schema Tests | 5 | ✅ Real | N/A | ~30s |
| E2E Tests | 8 | ✅ Real | ❌ Mock | ~60s |
| **Total** | **111** | - | - | **~2.5min** |

---

## 🗄️ Database Test Configuration

### GitHub Actions Setup

```yaml
# .github/workflows/test.yml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: redmine_warehouse_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### Test Database Migration

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_database():
    """Initialize test database with schema"""
    db_url = os.environ.get('TEST_DATABASE_URL')
    
    # Run schema creation
    subprocess.run([
        'psql', db_url,
        '-f', 'init-scripts/v0.10.0_init-schema.sql'
    ], check=True)
    
    yield db_url
    
    # Cleanup (optional - GitHub resets container)
```

---

## 1️⃣ Core MCP Protocol Tests (3 tests)

### TC-001: MCP Server Health Check

**Layer**: Integration  
**Database**: ❌ Not Required  
**Redmine**: ❌ Not Required  
**CI Time**: ~2s

**Objective**: Verify MCP server health endpoint works correctly

**Test Steps**:
1. Send HTTP GET to `/health`
2. Verify status 200
3. Verify response structure

**Expected**:
```json
{
  "status": "healthy",
  "version": "0.10.0",
  "timestamp": "ISO8601"
}
```

---

### TC-002: MCP Tools List

**Layer**: Integration  
**Database**: ❌ Not Required  
**Redmine**: ❌ Not Required  
**CI Time**: ~5s

**Objective**: Verify tools/list returns all available tools

**Test Steps**:
1. POST to `/mcp` with `{"method": "tools/list"}`
2. Verify tools array
3. Verify tool count >= 14

**Expected**:
- Each tool has: `name`, `description`, `inputSchema`

---

### TC-003: MCP Root Endpoint

**Layer**: Integration  
**Database**: ❌ Not Required  
**Redmine**: ❌ Not Required  
**CI Time**: ~2s

**Objective**: Verify root endpoint returns server info

**Expected**:
```json
{
  "name": "Redmine MCP Server",
  "version": "0.10.0",
  "endpoints": {
    "health": "/health",
    "mcp": "/mcp",
    "files": "/files/{id}"
  }
}
```

---

## 2️⃣ Redmine Project Management Tests (4 tests)

### TC-010: List Redmine Projects

**Layer**: Integration  
**Database**: ❌ Mock  
**Redmine**: ❌ Mock  
**CI Time**: ~5s

**Mock Data**:
```python
mock.projects.list.return_value = [
    MagicMock(id=341, name="Alpha", identifier="alpha"),
    MagicMock(id=342, name="Beta", identifier="beta"),
    MagicMock(id=343, name="Gamma", identifier="gamma")
]
```

**Expected**:
- `success: true`
- 3 projects returned
- Each has: `id`, `name`, `identifier`

---

### TC-011: Summarize Project Status

**Layer**: Integration  
**Database**: ❌ Mock  
**Redmine**: ❌ Mock  
**CI Time**: ~5s

**Expected**:
- `success: true`
- `summary` contains: `project`, `issues`, `status`

---

### TC-012: List Projects Error Handling

**Layer**: Integration  
**Database**: ❌ Mock  
**Redmine**: ❌ Mock (Error)  
**CI Time**: ~3s

**Mock**: `mock.projects.list.side_effect = ConnectionError("API Error")`

**Expected**:
- `success: false`
- `error` contains message

---

### TC-013: List Projects with Pagination

**Layer**: Integration  
**Database**: ❌ Mock  
**Redmine**: ❌ Mock  
**CI Time**: ~5s

**Expected**:
- Pagination works correctly
- No duplicate projects

---

## 3️⃣ Redmine Issue Management Tests (5 tests)

### TC-020: Get Redmine Issue

**Layer**: Integration  
**Database**: ❌ Mock  
**Redmine**: ❌ Mock  
**CI Time**: ~5s

**Mock Data**:
```python
mock.issues.get.return_value = MagicMock(
    id=1,
    subject="Test Bug",
    status=MagicMock(id=1, name="New"),
    priority=MagicMock(id=2, name="High")
)
```

**Expected**:
- `success: true`
- `issue` contains all fields

---

### TC-021 to TC-024

Similar pattern - Mock Redmine API, verify tool logic.

---

## 4️⃣ Database Schema Tests (5 tests) ⭐ NEW

### TC-080: Verify ads_user_subscriptions Table

**Layer**: DB Schema  
**Database**: ✅ Real  
**Redmine**: N/A  
**CI Time**: ~5s

**Test Steps**:
1. Query `information_schema.columns`
2. Verify all required columns exist
3. Verify data types

**Expected Columns**:
| Column | Type | Nullable |
|--------|------|----------|
| subscription_id | VARCHAR(255) | NO |
| user_id | VARCHAR(100) | NO |
| user_name | VARCHAR(200) | YES |
| user_email | VARCHAR(255) | YES |
| project_id | INTEGER | NO |
| channel | VARCHAR(50) | NO |
| channel_id | VARCHAR(255) | NO |
| report_type | VARCHAR(20) | NO |
| report_level | VARCHAR(20) | NO |
| send_time | VARCHAR(50) | YES |
| enabled | BOOLEAN | YES |
| created_at | TIMESTAMP | NO |
| updated_at | TIMESTAMP | NO |

---

### TC-081: Verify Table Constraints

**Layer**: DB Schema  
**Database**: ✅ Real  
**CI Time**: ~5s

**Test Steps**:
1. Query `information_schema.table_constraints`
2. Verify PRIMARY KEY exists
3. Verify UNIQUE constraints

**Expected**:
- PRIMARY KEY on `subscription_id`
- UNIQUE constraint on `subscription_id`

---

### TC-082: Verify Indexes

**Layer**: DB Schema  
**Database**: ✅ Real  
**CI Time**: ~5s

**Expected Indexes**:
- `idx_ads_user_subscriptions_user`
- `idx_ads_user_subscriptions_project`
- `idx_ads_user_subscriptions_channel`
- `idx_ads_user_subscriptions_enabled`

---

### TC-083: Verify dwd_issue_daily_snapshot Table

**Layer**: DB Schema  
**Database**: ✅ Real  
**CI Time**: ~5s

**Verify**:
- All DWD layer columns
- Composite unique constraint (issue_id, snapshot_date)

---

### TC-084: Verify dws_project_daily_summary Table

**Layer**: DB Schema  
**Database**: ✅ Real  
**CI Time**: ~5s

**Verify**:
- All DWS layer columns
- Composite unique constraint (project_id, snapshot_date)

---

## 5️⃣ Subscription E2E Tests (4 tests)

### TC-050: Subscribe to Project (E2E)

**Layer**: E2E  
**Database**: ✅ Real  
**Redmine**: ❌ Mock  
**CI Time**: ~10s

**Test Steps**:
1. Call `subscribe_project(project_id=341, channel="email", ...)`
2. Verify response
3. Query database to verify insert

**SQL Verification**:
```python
# Verify insert
result = db.execute(
    "SELECT * FROM ads_user_subscriptions WHERE subscription_id = %s",
    (subscription_id,)
)
assert result.fetchone() is not None
```

**Expected**:
- `success: true`
- Database contains new record

---

### TC-051: List My Subscriptions (E2E)

**Layer**: E2E  
**Database**: ✅ Real (Pre-populated)  
**Redmine**: ❌ Mock  
**CI Time**: ~10s

**Setup**:
```python
# Insert test data
db.execute(
    "INSERT INTO ads_user_subscriptions VALUES (...)",
    [("user1:341:email", "user1", 341, "email", ...)]
)
```

**Expected**:
- `success: true`
- Returns pre-populated subscriptions

---

### TC-052: Unsubscribe (E2E)

**Layer**: E2E  
**Database**: ✅ Real  
**CI Time**: ~10s

**Verify**:
- `success: true`
- Database record deleted

---

### TC-053: Subscribe Error Handling

**Layer**: E2E  
**Database**: ✅ Real  
**CI Time**: ~5s

**Test**: Invalid project_id, duplicate subscription

**Expected**:
- `success: false`
- Appropriate error message

---

## 6️⃣ Analytics E2E Tests (4 tests)

### TC-070 to TC-073

**Pattern**: Real DB + Mock Redmine

**Setup**:
```python
# Pre-populate warehouse tables
db.execute("INSERT INTO dwd_issue_daily_snapshot VALUES (...)")
db.execute("INSERT INTO dws_project_daily_summary VALUES (...)")
```

**Verify**:
- Analytics functions return correct aggregations
- SQL queries work correctly

---

## 📊 Test Summary

| Category | Tests | DB | Redmine | Time |
|----------|-------|----|---------|------|
| Core MCP | 3 | ❌ | ❌ | 10s |
| Projects | 4 | ❌ | Mock | 20s |
| Issues | 5 | ❌ | Mock | 25s |
| **DB Schema** | **5** | **✅** | N/A | **25s** |
| Subscription E2E | 4 | ✅ | Mock | 40s |
| Analytics E2E | 4 | ✅ | Mock | 40s |
| **Total** | **25** | - | - | **~160s** |

---

## 🏃 GitHub Actions Integration

### Workflow File

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: redmine_warehouse_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e .[test]
      
      - name: Initialize test database
        run: |
          psql postgresql://test_user:test_password@localhost:5432/redmine_warehouse_test \
            -f init-scripts/v0.10.0_init-schema.sql
      
      - name: Run Unit Tests
        run: |
          pytest tests/unit/ -v --cov
      
      - name: Run Integration Tests (Mock DB)
        run: |
          pytest tests/integration/test_mcp_integration.py -v
      
      - name: Run DB Schema Tests
        run: |
          pytest tests/integration/test_db_schema.py -v
      
      - name: Run E2E Tests
        run: |
          pytest tests/integration/test_subscription_e2e.py \
                 tests/integration/test_analytics_e2e.py -v
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v4
```

---

## ✅ Next Steps

1. **Review this test plan** - Confirm coverage is complete
2. **Implement tests** - Start with DB Schema tests (highest value)
3. **Add to CI/CD** - Update GitHub Actions workflow
4. **Run and verify** - All tests pass in CI

---

**Ready for implementation after approval.**
