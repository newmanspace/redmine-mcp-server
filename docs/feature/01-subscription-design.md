# Project Subscription Feature - Design Overview

**Version**: v1.0  
**Release Date**: 2026-02-26  
**Status**: ✅ Implemented

---

## 📐 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │  MCP Tools  │───▶│ Subscription │───▶│   Message   │   │
│  │  (5 tools)  │    │   Manager    │    │   Channel   │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
│                            │                                │
│                            ▼                                │
│                   ┌──────────────┐                         │
│                   │ Subscription │                         │
│                   │   Reporter   │                         │
│                   └──────────────┘                         │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Redmine   │ │  Warehouse  │ │  DingTalk/  │
    │     API     │ │  (Postgres) │ │  Telegram   │
    └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 🏗️ Component Design

### 1. SubscriptionManager

**File**: `src/redmine_mcp_server/subscriptions.py`

**Responsibilities**:
- CRUD operations for subscription configurations
- Subscription data persistence (JSON file)
- Subscription queries and statistics

**Core Methods**:
```python
class SubscriptionManager:
    def subscribe(...) -> Dict           # Create subscription
    def unsubscribe(...) -> Dict         # Cancel subscription
    def get_user_subscriptions(...) -> List  # Query user subscriptions
    def get_project_subscribers(...) -> List  # Query project subscribers
    def get_due_subscriptions(...) -> List    # Get due subscriptions
    def update_subscription(...) -> Dict      # Update subscription
    def get_stats(...) -> Dict                # Get statistics
```

**Data Structure**:
```json
{
  "subscription_id": "user_id:project_id:channel",
  "user_id": "string",
  "project_id": 341,
  "channel": "dingtalk",
  "channel_id": "string",
  "frequency": "daily",
  "level": "brief",
  "push_time": "09:00",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "enabled": true
}
```

---

### 2. SubscriptionReporter

**File**: `src/redmine_mcp_server/subscription_reporter.py`

**Responsibilities**:
- Generate brief reports
- Generate detailed reports
- Report formatting (adapt to different channels)
- Smart analysis (overdue detection, workload alerts)

**Core Methods**:
```python
class SubscriptionReporter:
    def generate_brief_report(...) -> Dict      # Brief report
    def generate_detailed_report(...) -> Dict   # Detailed report
    def format_report_for_message(...) -> str   # Format message
    def _generate_insights(...) -> Dict         # Generate insights
```

**Report Generation Flow**:
```
1. Check warehouse cache
   ├─ Has cache → Read from PostgreSQL
   └─ No cache → Call Redmine API
   
2. Generate statistics
   ├─ Priority distribution
   ├─ Status distribution
   └─ Workload analysis
   
3. Identify risks
   ├─ Overdue Issues (>30 days)
   └─ Workload alerts (>30 tasks)
   
4. Generate recommendations
   └─ Based on data analysis
```

---

### 3. MCP Tools Interface

**File**: `src/redmine_mcp_server/redmine_handler.py`

**Tools List**:

| Tool | Parameters | Returns | Description |
|------|------------|---------|-------------|
| `subscribe_project` | project_id, frequency, level, push_time | subscription | Subscribe to project |
| `unsubscribe_project` | project_id (optional) | removed_count | Cancel subscription |
| `list_my_subscriptions` | - | List[subscription] | View subscriptions |
| `get_subscription_stats` | - | stats | Subscription statistics |
| `generate_subscription_report` | project_id, level | report | Generate report |

**Tool Invocation Flow**:
```
User Request (DingTalk/Telegram)
    ↓
OpenClaw Gateway
    ↓
MCP Protocol
    ↓
redmine_handler.py (Tool Implementation)
    ↓
SubscriptionManager / SubscriptionReporter
    ↓
Return Result → Format → Push to User
```

---

## 🔄 Data Flow

### Subscription Creation Flow

```
User calls subscribe_project
    ↓
Validate parameters (project_id, frequency, level)
    ↓
Generate subscription_id (user_id:project_id:channel)
    ↓
Create subscription object
    ↓
Save to subscriptions.json
    ↓
Return subscription result
```

### Auto Push Flow

```
Scheduler triggers periodically (check every minute)
    ↓
Get time-matched subscriptions (get_due_subscriptions)
    ↓
For each subscription:
    ├─ Call generate_subscription_report
    ├─ Format report (format_report_for_message)
    └─ Push via channel (dingtalk/telegram)
    ↓
Log push result
```

---

## 📦 Storage Design

### subscriptions.json

**Path**: `./data/subscriptions.json`

**Structure**:
```json
{
  "user123:341:dingtalk": {
    "user_id": "user123",
    "project_id": 341,
    "channel": "dingtalk",
    "channel_id": "default",
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00",
    "created_at": "2026-02-26T06:05:12.384523",
    "updated_at": "2026-02-26T06:05:12.384523",
    "enabled": true
  },
  "user123:372:telegram": { ... }
}
```

**Indexing**:
- Primary key: `subscription_id` (composite: user_id + project_id + channel)
- Query optimization: Filter by `user_id`, `project_id`, `frequency`

---

## 🔌 Integration Points

### 1. Redmine API

**Purpose**: Fetch Issue data (when warehouse cache miss)

**APIs**:
- `redmine.issue.filter()` - Query issues
- `redmine.project.get()` - Get project info

**Optimization**: Prefer warehouse cache to reduce API calls

---

### 2. PostgreSQL Warehouse

**Purpose**: Fast project statistics retrieval

**Tables**:
- `warehouse.issue_daily_snapshot` - Issue snapshots
- `warehouse.project_daily_summary` - Project summaries

**Query**:
```sql
SELECT * FROM warehouse.project_daily_summary
WHERE project_id = 341 AND snapshot_date = '2026-02-26'
```

---

### 3. Message Channels

**Supported Channels**:
- DingTalk
- Telegram

**Push Method**:
- DingTalk: Stream mode WebSocket
- Telegram: Bot API

**Message Format**: Markdown text

---

## ⚡ Performance Optimization

### 1. Caching Strategy

- **Warehouse Cache**: Prefer PostgreSQL for statistics
- **Subscription Cache**: In-memory cache to reduce file I/O
- **Report Cache**: Cache same-parameter reports for 5 minutes

### 2. Token Optimization

| Report Type | Token Usage | Optimization |
|-------------|-------------|--------------|
| Brief | ~500 | Only key metrics |
| Detailed | ~2000 | Limit issues (TOP 20) |

### 3. Push Optimization

- **Batch Push**: Merge multiple projects for same user
- **Time Window**: Allow ±5 minutes float for push time
- **Retry**: Auto-retry 3 times on failure

---

## 🔒 Security Design

### 1. Access Control

- **Subscription Isolation**: Users can only view/manage own subscriptions
- **Project Permissions**: Based on Redmine project permissions (TODO)
- **Channel Verification**: Verify channel ID ownership (TODO)

### 2. Data Protection

- **File Permissions**: subscriptions.json writable by appuser only
- **Sensitive Info**: No user credentials stored
- **Log Sanitization**: Hide sensitive data in logs

---

## 🧪 Testing Strategy

### Unit Tests

```python
# Test subscription management
def test_subscribe():
    manager = SubscriptionManager()
    result = manager.subscribe("user1", 341, "dingtalk", "default")
    assert result["success"] == True

# Test report generation
def test_generate_brief_report():
    reporter = SubscriptionReporter()
    report = reporter.generate_brief_report(341)
    assert "summary" in report
```

### Integration Tests

```bash
# Test script
./scripts/test-subscription.sh
```

**Test Coverage**:
- ✅ Subscribe/Unsubscribe
- ✅ Brief/Detailed report generation
- ✅ Subscription statistics
- ✅ Data persistence

---

## 📈 Monitoring Metrics

### Business Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Total Subscriptions | - | - |
| Active Subscription Rate | >90% | <80% |
| Push Success Rate | 100% | <99% |
| Report Generation Time | <5s | >10s |

### Technical Metrics

| Metric | Collection Method |
|--------|-------------------|
| subscriptions.json size | File system |
| Query response time | Log analysis |
| Push failure count | Error logs |

---

## 🚀 Roadmap

### v1.1 (Short-term)

- [ ] Auto user identification (from session)
- [ ] Subscription templates (quick subscribe)
- [ ] Push history

### v1.2 (Mid-term)

- [ ] Email push channel
- [ ] Custom report templates
- [ ] Subscription groups

### v2.0 (Long-term)

- [ ] Real-time push (Issue change notification)
- [ ] Smart recommendations (based on user behavior)
- [ ] Multi-language support

---

## 📞 Troubleshooting

### Issue 1: Subscription Save Failed

**Symptom**: `Failed to save subscriptions: Permission denied`

**Cause**: data directory permission issue

**Solution**:
```bash
sudo chmod 777 /docker/redmine-mcp-server/data
docker restart redmine-mcp-server
```

### Issue 2: Report Generation Timeout

**Symptom**: `Timeout generating report`

**Cause**: Warehouse cache miss, slow API calls

**Solution**:
1. Check warehouse sync status
2. Manually trigger sync: `python /app/scripts/manual-sync.py`
3. Increase timeout

### Issue 3: Push Failed

**Symptom**: `Failed to push message`

**Cause**: Channel configuration error or network issue

**Solution**:
1. Check channel configuration
2. Verify network connectivity
3. Check channel logs

---

## 📚 Related Documentation

- [Feature Description](./01-subscription-feature.md)
- [Usage Guide](../SUBSCRIPTION_GUIDE.md)
- [API Reference](../tool-reference.md)

---

**Last Updated**: 2026-02-26  
**Maintainer**: OpenJaw <openjaw@gmail.com>  
**Code Location**: `src/redmine_mcp_server/subscriptions.py`, `subscription_reporter.py`
