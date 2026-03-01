# Test Database Configuration

**Version**: 1.0  
**Date**: 2026-03-01  
**Status**: Active

---

## 📊 Database Configuration

### Production vs Test

| Environment | Database | User | Password | Purpose |
|-------------|----------|------|----------|---------|
| **Production** | `redmine_warehouse` | `redmine_warehouse` | `WarehouseP@ss2026` | Production data |
| **Test** | `redmine_warehouse_test` | `redmine_warehouse_test` | `TestWarehouseP@ss2026` | Integration & E2E tests |

---

## 🔧 Test Database Setup

### Already Configured ✅

The test database has been created with:

```sql
-- Test user (semantic naming)
CREATE USER redmine_warehouse_test WITH 
  PASSWORD 'TestWarehouseP@ss2026'
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  NOINHERIT
  LOGIN
  NOREPLICATION
  NOBYPASSRLS;

-- Test database
CREATE DATABASE redmine_warehouse_test 
  OWNER redmine_warehouse_test
  ENCODING 'UTF8'
  TEMPLATE template0;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE redmine_warehouse_test TO redmine_warehouse_test;
```

### Manual Setup (if needed)

```bash
# Connect to PostgreSQL
docker compose exec warehouse-db psql -U redmine_warehouse -d postgres

# Run setup commands
\i /path/to/test-db-setup.sql
```

---

## 🧪 Running Tests

### Default Configuration (Recommended)

Tests automatically use the test database with semantic naming:

```bash
# No environment variable needed - uses defaults
pytest tests/integration/test_db_schema.py -v
pytest tests/integration/test_subscription_e2e.py -v
pytest tests/integration/test_analytics_e2e.py -v
```

### Custom Configuration

```bash
# Override with custom URL if needed
export TEST_DATABASE_URL="postgresql://redmine_warehouse_test:TestWarehouseP@ss2026@localhost:5432/redmine_warehouse_test"
pytest tests/integration/test_db_schema.py -v
```

### All DB Tests

```bash
# Run all tests that require database (skipped in CI)
pytest -m "db_schema or e2e" -v
```

---

## 🔒 Security Features

### User Permissions

| Permission | Test User | Production User |
|------------|-----------|-----------------|
| SUPERUSER | ❌ No | ❌ No |
| CREATEDB | ❌ No | ❌ No |
| CREATEROLE | ❌ No | ❌ No |
| INHERIT | ❌ No | ❌ No |
| LOGIN | ✅ Yes | ✅ Yes |
| REPLICATION | ❌ No | ❌ No |
| BYPASSRLS | ❌ No | ❌ No |

### Database Isolation

- ✅ **Separate database**: `redmine_warehouse_test` vs `redmine_warehouse`
- ✅ **Separate user**: `redmine_warehouse_test` vs `redmine_warehouse`
- ✅ **Limited permissions**: Test user cannot access production database
- ✅ **Semantic naming**: Clear indication of purpose

---

## 📝 Connection String Format

```
postgresql://{user}:{password}@{host}:{port}/{database}
```

### Test Database

```
postgresql://redmine_warehouse_test:TestWarehouseP@ss2026@localhost:5432/redmine_warehouse_test
```

### Production Database

```
postgresql://redmine_warehouse:WarehouseP@ss2026@localhost:5432/redmine_warehouse
```

---

## 🏃 CI/CD Integration

### GitHub Actions

Tests are automatically skipped in CI:

```yaml
# .github/workflows/test.yml
- name: Run integration tests (Mock DB only)
  run: |
    pytest tests/integration/ -v -m "not db_schema and not e2e"
```

### Local Development

```bash
# Start Docker containers
docker compose up -d

# Run all tests (including DB tests)
pytest tests/ -v --cov

# Run only fast tests (no database)
pytest -m "not db_schema and not e2e" -v
```

---

## 🧹 Cleanup

### Drop Test Database

```bash
docker compose exec warehouse-db psql -U redmine_warehouse -d postgres -c "DROP DATABASE IF EXISTS redmine_warehouse_test;"
docker compose exec warehouse-db psql -U redmine_warehouse -d postgres -c "DROP USER IF EXISTS redmine_warehouse_test;"
```

### Recreate Test Database

```bash
# Run setup commands again
docker compose exec warehouse-db psql -U redmine_warehouse -d postgres << 'EOF'
CREATE USER redmine_warehouse_test WITH PASSWORD 'TestWarehouseP@ss2026' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN NOREPLICATION NOBYPASSRLS;
CREATE DATABASE redmine_warehouse_test OWNER redmine_warehouse_test ENCODING 'UTF8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE redmine_warehouse_test TO redmine_warehouse_test;
EOF
```

---

## ✅ Verification

```bash
# Verify test user exists
docker compose exec warehouse-db psql -U redmine_warehouse -d postgres -c "\du redmine_warehouse_test"

# Verify test database exists
docker compose exec warehouse-db psql -U redmine_warehouse -d postgres -c "\l redmine_warehouse_test"

# Test connection
docker compose exec warehouse-db psql -U redmine_warehouse_test -d redmine_warehouse_test -c "SELECT current_user, current_database();"
```

Expected output:
```
 current_user       |     current_database     
---------------------+--------------------------
 redmine_warehouse_test | redmine_warehouse_test
```

---

**Last Updated**: 2026-03-01  
**Maintained By**: OpenJaw
