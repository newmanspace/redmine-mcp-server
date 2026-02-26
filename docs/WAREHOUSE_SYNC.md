# Warehouse Sync Mechanism

**Version**: v1.1  
**Last Updated**: 2026-02-26

---

## 📊 Overview

The Redmine MCP Server uses a **subscription-based sync mechanism** to keep the PostgreSQL warehouse up-to-date with Redmine data.

---

## 🔄 Sync Types

### 1. Full Sync (全量同步)

**Purpose**: Initial data load or complete refresh

**How it works**:
- Fetches **ALL issues** from Redmine API
- Syncs to warehouse with change detection
- Compares with previous day's snapshot

**When to use**:
- First-time setup
- After data corruption
- Manual refresh needed

**Trigger**:
- **Automatic**: On scheduler startup (initial sync)
- **Manual**: Call `trigger_full_sync()` tool

**Example**:
```bash
# Sync all subscribed projects
trigger_full_sync()

# Sync specific project
trigger_full_sync(project_id=341)
```

---

### 2. Incremental Sync (增量同步)

**Purpose**: Regular updates with minimal API calls

**How it works**:
- Fetches only **recently updated issues**
- Default: Issues updated in last **13 minutes** (10-min interval + 3-min buffer)
- Uses `updated_on` filter

**When to use**:
- Regular scheduled sync (every 10 minutes)
- Keep warehouse current

**Trigger**:
- **Automatic**: Every 10 minutes (configurable)

**Why 13 Minutes?**:
- Sync interval is 10 minutes
- Extra 3 minutes buffer prevents missing data due to:
  - API delays
  - Network latency
  - Clock skew
  - Sync processing time
- Ensures no data gaps between sync cycles

---

## ⚙️ Configuration

### Environment Variables

```bash
# Enable/disable sync
WAREHOUSE_SYNC_ENABLED=true

# Sync interval (minutes)
WAREHOUSE_SYNC_INTERVAL_MINUTES=10

# Project IDs (optional - auto-detected from subscriptions)
# WAREHOUSE_PROJECT_IDS=341,372

# Max issues to sync per project (prevent timeout for large projects)
MAX_ISSUES_PER_SYNC=500
```

### Subscription-Based Sync

**Default behavior**: Sync projects based on active subscriptions

**How it works**:
1. Scheduler loads all active subscriptions
2. Extracts unique project IDs
3. Syncs only subscribed projects

**Benefits**:
- ✅ No manual configuration needed
- ✅ Auto-adjusts when users subscribe/unsubscribe
- ✅ Efficient resource usage

---

## 📋 Sync Process

### Full Sync Flow

```
1. Load subscribed projects (from SubscriptionManager)
   ↓
2. For each project:
   ├─ Fetch ALL issues (paginate, 100 per page)
   ├─ Get yesterday's snapshot (for comparison)
   ├─ Determine: is_new, is_closed, is_updated
   └─ Upsert to warehouse.issue_daily_snapshot
   ↓
3. Refresh summary table
   ↓
4. Log results
```

### Incremental Sync Flow

```
1. Load subscribed projects
   ↓
2. For each project:
   ├─ Calculate time window (now - 10 minutes)
   ├─ Fetch issues updated in window
   ├─ Compare with yesterday
   └─ Upsert changed issues
   ↓
3. Refresh summary table
   ↓
4. Log results
```

---

## 🛠️ Manual Sync Commands

### Via MCP Tools

**Sync all projects**:
```bash
trigger_full_sync()
```

**Sync specific project**:
```bash
trigger_full_sync(project_id=341)
```

### Via Script

**Sync all subscribed projects**:
```bash
docker exec redmine-mcp-server python /app/scripts/manual-sync.py
```

**Sync specific project**:
```bash
docker exec redmine-mcp-server python /app/scripts/manual-sync.py 341
```

---

## 📊 Monitoring

### Check Sync Status

**View logs**:
```bash
docker logs redmine-mcp-server | grep "Sync"
```

**Example output**:
```
2026-02-26 07:09:54 INFO Starting full sync for 13 projects...
2026-02-26 07:09:54 INFO Syncing 13 projects: [356, 357, 358, ...]
2026-02-26 07:09:55 INFO Synced 1 issues for project 356
2026-02-26 07:09:55 INFO Synced 13 issues for project 357
2026-02-26 07:09:55 INFO Sync completed (run #1)
```

### Check Warehouse Data

```bash
docker exec redmine-mcp-warehouse-db psql -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT project_id, snapshot_date, COUNT(*) as issues 
      FROM warehouse.issue_daily_snapshot 
      GROUP BY project_id, snapshot_date 
      ORDER BY snapshot_date DESC, project_id;"
```

---

## 🎯 Best Practices

### 1. Initial Setup

```bash
# 1. Subscribe to projects
subscribe_project(project_id=341, frequency="daily")

# 2. Trigger full sync
trigger_full_sync()

# 3. Verify data
# (Check warehouse via SQL query above)
```

### 2. Regular Operation

- **Automatic**: Scheduler runs every 10 minutes
- **No manual intervention needed**

### 3. Troubleshooting

**Issue**: Project data missing

**Solution**:
```bash
# Trigger full sync for that project
trigger_full_sync(project_id=341)
```

**Issue**: Sync taking too long

**Solution**:
- Check Redmine API performance
- Increase `WAREHOUSE_SYNC_INTERVAL_MINUTES`
- Reduce number of subscribed projects

---

## 📈 Performance

### Sync Speed

| Sync Type | Speed (per project) | Example (13 projects) |
|-----------|--------------------|----------------------|
| Full (limited) | ~2-5 seconds | ~30-60 seconds |
| Incremental (13-min window) | ~1-2 seconds | ~15-30 seconds |

### API Usage

| Sync Type | API Calls (per project) |
|-----------|------------------------|
| Full (limited) | `min(ceil(total_issues/100), MAX_ISSUES_PER_SYNC/100)` |
| Incremental | 1-2 (usually) |

**Example**:
- Project with 500 issues: Full sync = 5 API calls (with MAX_ISSUES_PER_SYNC=500)
- Project with 2000 issues: Full sync = 5 API calls (limited to 500)
- Incremental sync: 1 API call (if few updates)

### Issue Quantity Control

**Full Sync Limits**:
- **Time Range**: From project creation date (all historical data)
- **Max Issues**: 500 per project (configurable via `MAX_ISSUES_PER_SYNC`)

**Incremental Sync Window**:
- **Time Range**: Last 13 minutes (10-min interval + 3-min buffer)
- **Purpose**: Prevent missing data, ensure no gaps between cycles

**Why Limit?**:
1. Prevent timeout for large projects (1000+ issues)
2. Reduce API load on Redmine server
3. Faster sync cycles
4. Most active projects have <500 issues in 6 months

**Configure Limits**:
```bash
# Increase limit for large projects
MAX_ISSUES_PER_SYNC=1000
```

---

## 🔧 Advanced Configuration

### Custom Sync Interval

```bash
# Edit .env.docker
WAREHOUSE_SYNC_INTERVAL_MINUTES=5  # Sync every 5 minutes
```

### Force Specific Projects

```bash
# Override auto-detection
WAREHOUSE_PROJECT_IDS=341,372,311
```

### Disable Auto Sync

```bash
WAREHOUSE_SYNC_ENABLED=false
```

Then manually sync when needed:
```bash
trigger_full_sync()
```

---

## 📝 Changelog

### v1.2 (2026-02-26)

- ✅ Max issues limit per sync (`MAX_ISSUES_PER_SYNC`)
- ✅ Full sync limited to last 6 months (prevent timeout)
- ✅ Configurable limits via environment variables

### v1.1 (2026-02-26)

- ✅ Subscription-based sync (auto-detect projects)
- ✅ Manual full sync tool (`trigger_full_sync`)
- ✅ Improved logging
- ✅ Background sync to avoid timeouts

### v1.0 (2026-02-14)

- ✅ Initial sync implementation
- ✅ Incremental sync support
- ✅ PostgreSQL warehouse integration

---

**Maintainer**: OpenJaw <openjaw@gmail.com>  
**Documentation**: `/docker/redmine-mcp-server/docs/`
