# MCP Server Test Plan

**Version**: 3.0  
**Date**: 2026-03-01  
**Strategy**: Local (Mock + Real DB) | CI (Mock Only)

---

## 📊 Test Strategy Overview

### Test Distribution

| Layer | Count | Database | Local | CI | Time (Local) | Time (CI) |
|-------|-------|----------|-------|----|--------------|-----------|
| Unit | 86 | ❌ Mock | ✅ | ✅ | 30s | 30s |
| Integration (Mock) | 12 | ❌ Mock | ✅ | ✅ | 20s | 20s |
| DB Schema | 5 | ✅ Real | ✅ | ⏭️ Skip | 25s | - |
| E2E | 8 | ✅ Real | ✅ | ⏭️ Skip | 40s | - |
| **Total** | **111** | - | **111** | **98** | **~2min** | **~50s** |

### Test Markers

```python
@pytest.mark.unit          # Unit tests (always run)
@pytest.mark.integration   # Integration tests (always run)
@pytest.mark.db_schema     # DB schema tests (local only)
@pytest.mark.e2e           # E2E tests (local only)
```

---

## 🏃 GitHub CI Configuration

### Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: pip install -e .[test]
      
      - name: Run Unit Tests
        run: pytest tests/unit/ -v --cov
      
      - name: Run Integration Tests (Mock DB)
        run: pytest tests/integration/test_mcp_integration.py -v
      
      # Note: DB Schema and E2E tests run locally only
      # Developers run with: pytest -m "db_schema or e2e"
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          flags: unittests,integration
```

### Skip Logic

```python
# tests/conftest.py
import pytest
import os

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", 
        "db_schema: mark test as requiring real database (skip in CI)"
    )
    config.addinivalue_line(
        "markers", 
        "e2e: mark test as end-to-end test (skip in CI)"
    )

# tests/integration/test_db_schema.py
@pytest.mark.db_schema
@pytest.mark.skipif(
    os.environ.get('GITHUB_ACTIONS') == 'true',
    reason="Requires real database - skip in GitHub Actions"
)
class TestDBSchema:
    """Tests that verify database table structure"""
    pass
```

---

## 💻 Local Development Setup

### Option 1: Docker Compose (Recommended)

**docker-compose.test.yml**:
```yaml
version: '3.8'

services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: redmine_test
    ports:
      - "5433:5432"
    volumes:
      - ./init-scripts:/docker-entrypoint-initdb.d
```

**Run Commands**:
```bash
# 1. Start test database
docker compose -f docker-compose.test.yml up -d

# 2. Wait for database to be ready
sleep 10

# 3. Set environment
export TEST_DATABASE_URL="postgresql://test:test@localhost:5433/redmine_test"

# 4. Run all tests (including DB tests)
pytest tests/ -v --cov

# 5. Or run specific test types
pytest -m unit -v                    # Unit tests only
pytest -m integration -v             # Integration tests only
pytest -m "db_schema or e2e" -v      # DB tests only
pytest -m "not db_schema" -v         # All except DB tests

# 6. Cleanup
docker compose -f docker-compose.test.yml down
```

### Option 2: Local PostgreSQL

```bash
# 1. Create test database
createdb redmine_warehouse_test

# 2. Initialize schema
psql postgresql://$(whoami)@localhost/redmine_warehouse_test \
  -f init-scripts/v0.10.0_init-schema.sql

# 3. Set environment
export TEST_DATABASE_URL="postgresql://$(whoami)@localhost/redmine_warehouse_test"

# 4. Run tests
pytest tests/ -v --cov
```

---

## 📋 Test Cases

### 1️⃣ Unit Tests (86 tests) - ✅ CI

**Location**: `tests/unit/`

**Characteristics**:
- All dependencies mocked
- Fast execution (~30s)
- No external dependencies
- **Always runs in CI**

**Coverage**:
- `test_cleanup_manager.py` - Cleanup logic
- `test_error_handling.py` - Error handling
- `test_file_manager.py` - File operations
- `test_issue_to_dict_selective.py` - Issue conversion
- `test_tool_imports.py` - Tool imports

---

### 2️⃣ Integration Tests (12 tests) - ✅ CI

**Location**: `tests/integration/test_mcp_integration.py`

**Characteristics**:
- Database mocked
- Redmine API mocked
- Fast execution (~20s)
- **Always runs in CI**

**Coverage**:
```python
class TestMCPHTTPEndpoints:
    test_health_endpoint          # ✅
    test_root_endpoint            # ✅

class TestMCPToolsImport:
    test_issue_tools_import       # ✅
    test_project_tools_import     # ✅
    test_search_tools_import      # ✅
    test_subscription_tools_import# ✅
    test_warehouse_tools_import   # ✅
    test_analytics_tools_import   # ✅
    test_contributor_tools_import # ✅
    test_ads_tools_import         # ✅
```

---

### 3️⃣ DB Schema Tests (5 tests) - ⏭️ CI Skip

**Location**: `tests/integration/test_db_schema.py`

**Characteristics**:
- **Requires real database**
- Verifies table structure
- Verifies constraints
- Verifies indexes
- **Skipped in CI** (run locally)

**Coverage**:
```python
@pytest.mark.db_schema
@pytest.mark.skipif(CI, reason="Requires real database")
class TestDBSchema:
    test_ads_user_subscriptions_table    # Verify columns
    test_dwd_issue_daily_snapshot_table  # Verify columns
    test_dws_project_daily_summary_table # Verify columns
    test_table_constraints               # Verify PK, UK
    test_table_indexes                   # Verify indexes
```

**Local Run**:
```bash
pytest -m db_schema -v
# Output:
# ✓ test_ads_user_subscriptions_table
# ✓ test_dwd_issue_daily_snapshot_table
# ✓ test_dws_project_daily_summary_table
# ✓ test_table_constraints
# ✓ test_table_indexes
```

---

### 4️⃣ E2E Tests (8 tests) - ⏭️ CI Skip

**Location**: 
- `tests/integration/test_subscription_e2e.py`
- `tests/integration/test_analytics_e2e.py`

**Characteristics**:
- **Requires real database**
- Redmine API mocked
- Tests complete workflows
- **Skipped in CI** (run locally)

**Coverage**:
```python
@pytest.mark.e2e
@pytest.mark.skipif(CI, reason="Requires real database")
class TestSubscriptionE2E:
    test_subscribe_project         # Full subscribe flow
    test_list_subscriptions        # Query subscriptions
    test_unsubscribe_project       # Cancel subscription
    test_subscribe_error_handling  # Error scenarios

class TestAnalyticsE2E:
    test_get_project_daily_stats   # Query warehouse
    test_analyze_contributors      # Analytics query
    test_get_user_workload         # Workload analysis
```

**Local Run**:
```bash
pytest -m e2e -v
# Output:
# ✓ test_subscribe_project
# ✓ test_list_subscriptions
# ✓ test_unsubscribe_project
# ✓ test_subscribe_error_handling
# ✓ test_get_project_daily_stats
# ✓ test_analyze_contributors
# ✓ test_get_user_workload
```

---

## 📊 Test Execution Summary

### Local Development

```bash
# Run ALL tests (including DB tests)
pytest tests/ -v --cov
# Expected: 111 tests, ~2 minutes

# Run only fast tests (no database)
pytest -m "not db_schema and not e2e" -v
# Expected: 98 tests, ~50 seconds

# Run only DB tests
pytest -m "db_schema or e2e" -v
# Expected: 13 tests, ~65 seconds
```

### GitHub CI

```bash
# Automatic - runs on every push/PR
pytest tests/unit/ tests/integration/test_mcp_integration.py -v
# Expected: 98 tests, ~50 seconds
```

---

## 🎯 Benefits of This Strategy

| Benefit | Description |
|---------|-------------|
| **Fast CI** | ~50s vs ~2min, faster feedback |
| **Cost Effective** | No database service in CI |
| **Local Coverage** | Developers can run full test suite |
| **Catch Critical Issues** | Unit + Integration catch most bugs |
| **Catch Schema Issues** | DB tests catch ISSUE-004/008 locally |

---

## ⚠️ Trade-offs

| Trade-off | Impact | Mitigation |
|-----------|--------|------------|
| CI doesn't catch DB issues | Schema changes might break in production | Document: "Run `pytest -m db_schema` before pushing DB changes" |
| Developers must run DB tests | Extra step for DB changes | Add to PR checklist |
| Test environment drift | Local DB might differ from production | Document required PostgreSQL version |

---

## ✅ Developer Workflow

### Before Pushing Database Changes

```bash
# 1. Make schema change
# Edit init-scripts/v0.10.0_init-schema.sql

# 2. Start test database
docker compose -f docker-compose.test.yml up -d

# 3. Run DB schema tests
pytest -m db_schema -v

# 4. Run E2E tests
pytest -m e2e -v

# 5. If all pass, commit and push
git add -A && git commit -m "feat: add new table" && git push
```

### PR Checklist

- [ ] Unit tests pass: `pytest tests/unit/ -v`
- [ ] Integration tests pass: `pytest tests/integration/ -v`
- [ ] **If DB changes**: Run `pytest -m db_schema -v`
- [ ] **If DB changes**: Run `pytest -m e2e -v`
- [ ] Code quality passes: `flake8 src/ && black --check src/`

---

## 📝 Next Steps

1. **Implement DB Schema Tests** - `test_db_schema.py`
2. **Implement E2E Tests** - `test_subscription_e2e.py`, `test_analytics_e2e.py`
3. **Add pytest markers** - `tests/conftest.py`
4. **Update CI workflow** - `.github/workflows/test.yml`
5. **Add docker-compose.test.yml** - Local test database
6. **Update PR checklist** - Document DB test requirement

---

**Ready for implementation.**
