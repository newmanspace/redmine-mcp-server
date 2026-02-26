# Data Synchronization Feature

**Version**: v1.2  
**Release Date**: 2026-02-26  
**Status**: ✅ Released

---

## 📋 Overview

The Redmine MCP Server provides a comprehensive data synchronization system that keeps the PostgreSQL warehouse up-to-date with Redmine issues. The system supports multiple sync strategies to balance performance, completeness, and API load.

---

## 🎯 Core Features

### 1. Subscription-Based Sync

**Purpose**: Automatically sync only subscribed projects

**How it Works**:
- Scheduler loads active subscriptions from `SubscriptionManager`
- Only subscribed projects are included in sync cycles
- Auto-adjusts when users subscribe/unsubscribe

**Benefits**:
- ✅ No manual configuration needed
- ✅ Efficient resource usage
- ✅ Real-time adaptation to user needs

---

### 2. Incremental Sync (Automatic)

**Purpose**: Keep warehouse current with minimal API calls

**Configuration**:
- **Frequency**: Every 10 minutes (configurable)
- **Time Window**: Last 13 minutes of data
- **Trigger**: Automatic (scheduler)

**Why 13 Minutes?**:
- Sync interval is 10 minutes
- Extra 3 minutes buffer prevents missing data due to:
  - API delays
  - Network latency
  - Clock skew
  - Sync processing time
- Ensures no data gaps between sync cycles

**Example**:
```
09:00 - Sync issues updated 08:47-09:00 (13-min window)
09:10 - Sync issues updated 08:57-09:10 (13-min window, 3-min overlap)
09:20 - Sync issues updated 09:07-09:20 (13-min window, 3-min overlap)
```

---

### 3. Full Sync (Manual)

**Purpose**: Complete historical data load

**Configuration**:
- **Trigger**: Manual via MCP tool
- **Time Range**: From project creation date
- **Issue Limit**: 500 per project (configurable)
- **Status Filter**: `status_id=*` (all statuses including closed)

**When to Use**:
- Initial setup
- After data corruption
- Manual refresh needed
- New project subscription

**How to Trigger**:
```bash
# Sync specific project
trigger_full_sync(project_id=341)

# Sync all subscribed projects
trigger_full_sync()
```

---

### 4. Progressive Sync (Manual)

**Purpose**: Gradual historical data load (one week at a time)

**Configuration**:
- **Trigger**: Manual via MCP tool
- **Time Range**: One week per run
- **Frequency**: On-demand (recommended: run multiple times)
- **Status Filter**: `status_id=*` (all statuses)

**When to Use**:
- Large projects (>1000 issues)
- Avoid API timeout
- Gradual data load preferred

**How to Trigger**:
```bash
trigger_progressive_sync()
```

**Example Progress**:
```
Run 1: 2024-01-01 to 2024-01-08 (Week 1)
Run 2: 2024-01-08 to 2024-01-15 (Week 2)
Run 3: 2024-01-15 to 2024-01-22 (Week 3)
...
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Enable/disable sync
WAREHOUSE_SYNC_ENABLED=true

# Incremental sync interval (minutes)
WAREHOUSE_SYNC_INTERVAL_MINUTES=10

# Max issues per sync (prevent timeout)
MAX_ISSUES_PER_SYNC=500

# Auto-detected from subscriptions
# WAREHOUSE_PROJECT_IDS=341,372
```

### Docker Compose

```yaml
environment:
  WAREHOUSE_SYNC_ENABLED: "true"
  WAREHOUSE_SYNC_INTERVAL_MINUTES: "10"
  MAX_ISSUES_PER_SYNC: "500"
  MAX_ISSUES_PER_SYNC: ${MAX_ISSUES_PER_SYNC:-500}
```

---

## 📊 Sync Strategies Comparison

| Strategy | Trigger | Frequency | Time Range | Best For |
|----------|---------|-----------|------------|----------|
| **Incremental** | Auto | Every 10 min | Last 3 min | Keeping current |
| **Full** | Manual | On-demand | From creation | Initial load |
| **Progressive** | Manual | On-demand | One week/run | Large projects |

---

## 🛠️ MCP Tools

### `trigger_full_sync`

**Description**: Trigger full data sync for warehouse (manual)

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | int | ❌ | None | Specific project ID (sync all if None) |

**Returns**:
```json
{
  "success": true,
  "project_id": 341,
  "synced_issues": 433,
  "message": "Full sync completed for project 341"
}
```

**Example**:
```bash
# Sync single project
trigger_full_sync(project_id=341)

# Sync all projects
trigger_full_sync()
```

---

### `trigger_progressive_sync`

**Description**: Trigger progressive weekly sync (manual)

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "message": "Progressive weekly sync started for 13 projects",
  "projects": [341, 356, 357, ...],
  "note": "Each run syncs one week of data. Multiple runs needed."
}
```

---

### `get_sync_progress`

**Description**: Get sync progress for all subscribed projects

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "projects": 13,
  "progress": {
    "341": {"status": "completed"},
    "356": {"status": "in_progress", "last_synced_week": "2026-02-12", "days_remaining": 14}
  },
  "sync_count": 45
}
```

---

## 📈 Performance

### Sync Speed

| Sync Type | Speed (per project) | Example (500 issues) |
|-----------|--------------------|----------------------|
| Full | ~5-10 seconds | ~5-10 seconds |
| Incremental | ~1-2 seconds | ~1-2 seconds |
| Progressive | ~2-5 seconds | ~2-5 seconds per week |

### API Usage

| Sync Type | API Calls (per project) |
|-----------|------------------------|
| Full | `ceil(total_issues / 100)` |
| Incremental | 1 (usually) |
| Progressive | `ceil(weekly_issues / 100)` |

**Example** (Project with 500 issues):
- Full sync: 5 API calls
- Incremental sync: 1 API call
- Progressive sync: 1-2 API calls per week

---

## 🔍 Monitoring

### Check Sync Status

**View logs**:
```bash
docker logs redmine-mcp-server | grep "Sync"
```

**Example output**:
```
2026-02-26 08:00:00 INFO Starting incremental sync for 13 projects...
2026-02-26 08:00:01 INFO Incremental sync for project 341 since 2026-02-26 07:57:00 (3-min window)
2026-02-26 08:00:02 INFO Synced 5 issues for project 341
2026-02-26 08:00:02 INFO Sync completed (run #45)
```

### Check Warehouse Data

```bash
docker exec redmine-mcp-warehouse-db psql -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT project_id, COUNT(DISTINCT issue_id) as issues 
      FROM warehouse.issue_daily_snapshot 
      WHERE snapshot_date = CURRENT_DATE 
      GROUP BY project_id 
      ORDER BY project_id;"
```

---

## 📝 Usage Examples

### Example 1: Initial Setup

```bash
# 1. Subscribe to projects
subscribe_project(project_id=341, frequency="daily")

# 2. Trigger full sync
trigger_full_sync(project_id=341)

# 3. Verify data
get_sync_progress()
```

### Example 2: Large Project Sync

```bash
# For projects with >1000 issues, use progressive sync
trigger_progressive_sync()

# Run multiple times until caught up
# (Each run syncs one week of data)
```

### Example 3: Manual Refresh

```bash
# Refresh specific project
trigger_full_sync(project_id=341)

# Check result
get_sync_progress()
```

---

## ⚙️ Advanced Configuration

### Increase Issue Limit

For projects with many issues:

```bash
# Edit .env.docker
MAX_ISSUES_PER_SYNC=2000

# Restart service
docker compose restart redmine-mcp-server
```

### Change Sync Interval

```bash
# Edit .env.docker
WAREHOUSE_SYNC_INTERVAL_MINUTES=5  # Sync every 5 minutes

# Restart service
docker compose restart redmine-mcp-server
```

### Disable Auto Sync

```bash
# Edit .env.docker
WAREHOUSE_SYNC_ENABLED=false

# Manual sync only
trigger_full_sync()
```

---

## 🔒 Data Integrity

### Issue Status Handling

**Important**: The sync uses `status_id=*` parameter to fetch ALL issues including closed ones.

**Before (Bug)**:
```python
params = {'project_id': project_id, 'limit': 100}
# Result: Only open issues synced
```

**After (Fixed)**:
```python
params = {'project_id': project_id, 'status_id': '*', 'limit': 100}
# Result: All issues synced (open + closed)
```

### Verification

Always verify sync completeness:

```sql
-- Compare with Redmine API
SELECT project_id, COUNT(DISTINCT issue_id) as warehouse_count
FROM warehouse.issue_daily_snapshot 
WHERE snapshot_date = CURRENT_DATE
GROUP BY project_id;

-- Should match Redmine API total_count
```

---

## 📞 Troubleshooting

### Issue 1: Sync Timeout

**Symptom**: `Timeout fetching issues`

**Cause**: Large project (>1000 issues)

**Solution**:
```bash
# Increase limit
MAX_ISSUES_PER_SYNC=2000

# Or use progressive sync
trigger_progressive_sync()
```

### Issue 2: Missing Closed Issues

**Symptom**: Warehouse count < Redmine API count

**Cause**: Missing `status_id=*` parameter

**Solution**:
```bash
# Verify code has status_id=*
# Re-run full sync
trigger_full_sync(project_id=341)
```

### Issue 3: Sync Not Running

**Symptom**: No sync logs

**Cause**: Scheduler not started

**Solution**:
```bash
# Check service status
docker ps | grep redmine-mcp-server

# Restart service
docker restart redmine-mcp-server

# Check logs
docker logs redmine-mcp-server | grep "scheduler"
```

---

## 📚 Related Documentation

- [Subscription Feature](./01-subscription-feature.md)
- [Warehouse Sync Guide](../WAREHOUSE_SYNC.md)
- [API Reference](../tool-reference.md)

---

**Last Updated**: 2026-02-26  
**Maintainer**: OpenJaw <openjaw@gmail.com>
