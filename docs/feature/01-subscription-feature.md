# Project Subscription Feature

**Version**: v1.0  
**Release Date**: 2026-02-26  
**Status**: ✅ Released

---

## 📋 Overview

The Project Subscription feature allows users to subscribe to Redmine project status reports. The system automatically pushes project information to specified channels (DingTalk/Telegram) based on configured frequency.

### Core Value

- 📊 **Stay Updated** - No need to manually query, important info pushed automatically
- ⏰ **Flexible Frequency** - Support realtime/daily/weekly/monthly
- 📝 **Two Report Levels** - Brief for quick view, Detailed for deep analysis
- 💬 **Multi-Channel** - DingTalk and Telegram support
- 🎯 **Smart Risk Detection** - Automatic overdue Issue and workload alert

---

## 🎯 Use Cases

### Use Case 1: Daily PM Follow-up
> As a project manager, I want to receive brief reports every morning at 9 AM to quickly understand yesterday's progress.

**Configuration**:
```bash
subscribe_project(project_id=341, frequency="daily", level="brief", push_time="09:00")
```

### Use Case 2: Weekly Tech Lead Review
> As a tech lead, I want detailed reports every Monday to analyze team workload and project risks.

**Configuration**:
```bash
subscribe_project(project_id=341, frequency="weekly", level="detailed", push_time="Mon 09:00")
```

### Use Case 3: Multi-Project Management
> As a department head, I need to monitor multiple projects simultaneously.

**Configuration**:
```bash
subscribe_project(project_id=341, frequency="daily", push_time="09:00")
subscribe_project(project_id=372, frequency="daily", push_time="09:30")
subscribe_project(project_id=356, frequency="weekly", push_time="Mon 10:00")
```

### Use Case 4: Ad-hoc Project Check
> I need to temporarily check a project's current status without regular subscription.

**Configuration**:
```bash
generate_subscription_report(project_id=341, level="detailed")
```

---

## 🔧 Features

### 1. Subscription Management

| Feature | Description | Tool Name |
|---------|-------------|-----------|
| Create Subscription | Subscribe to a project | `subscribe_project` |
| Cancel Subscription | Cancel one or all subscriptions | `unsubscribe_project` |
| View Subscriptions | View all my subscriptions | `list_my_subscriptions` |
| Statistics | View subscription statistics | `get_subscription_stats` |

### 2. Report Generation

| Feature | Description | Tool Name |
|---------|-------------|-----------|
| Manual Generate | Generate project report immediately | `generate_subscription_report` |
| Auto Push | Scheduled push to channels | (Scheduler auto-executes) |

### 3. Push Configuration

| Setting | Options | Default | Description |
|---------|---------|---------|-------------|
| **Frequency** | `realtime`, `daily`, `weekly`, `monthly` | `daily` | Push frequency |
| **Level** | `brief`, `detailed` | `brief` | Report detail level |
| **Time** | `"HH:MM"`, `"Ddd HH:MM"`, `"DD HH:MM"` | `09:00` | Push time |
| **Channel** | `dingtalk`, `telegram` | `dingtalk` | Push channel |

---

## 📊 Report Content

### Brief Report

**Token Usage**: ~500 tokens  
**Best For**: Quick overview, mobile viewing

**Includes**:
- 📈 Status Snapshot
  - Total Issues
  - New/Closed/Updated today
- 🔴 Priority Highlights
  - Immediate/Urgent/High count
  - TOP 5 high priority issues

**Example**:
```
📊 Project Subscription Report
📁 Project ID: 341
📅 2026-02-26 09:00

━━━

### 📈 Status Snapshot
- Total Issues: 129
- New (Today): 129
- Closed (Today): 0
- Updated (Today): 21

**Priority Distribution**:
- 🔴 Immediate: 2
- 🟠 Urgent: 13
- 🟡 High: 19

### 🔴 High Priority Issues
- 🔴 #77684 Export intermediate DB—contact admin
- 🔴 #76820 Batch job interface optimization
- 🟠 #75858 [Summary] Process Planning
...

━━━
```

---

### Detailed Report

**Token Usage**: ~2000 tokens  
**Best For**: Deep analysis, weekly/monthly reports

**Includes**:
- ✅ All brief report content
- 📊 Complete priority distribution
- 📊 Complete status distribution
- 👥 Top 10 assignees by workload
- 🔴 High priority issue details (up to 20)
- ⚠️ Overdue risk identification (>30 days unclosed)
- 💡 Project insights and recommendations

**Example**:
```
📊 Project Subscription Report (Detailed)
📁 Project ID: 341
📅 2026-02-26 09:00

━━━

### 📈 Status Snapshot
- Total Issues: 129
- New (Today): 129
- Closed (Today): 0
- Updated (Today): 21

### 📊 Priority Distribution
- 🔴 Immediate: 2
- 🟠 Urgent: 13
- 🟡 High: 19
- ⚪ Normal: 94
- 🔵 Low: 1

### 📊 Status Distribution
- New: 86
- In Progress: 16
- Resolved: 5
- Closed: 0
- Feedback: 9

### 👥 Top 5 Assignees
- Fu Zhibin: 50 tasks (48 in progress)
- Bai Rufeng: 18 tasks (13 in progress)
- Wang Xiaojuan: 14 tasks (12 in progress)
...

### ⚠️ Overdue Risks (>30 days)
- #75364 Order Management Module Migration - Fu Zhibin (107 days)
- #75418 WIP Query - Fu Zhibin (106 days)
- #75421 Special WIP Management - Zeng Fei (106 days)
...

### 💡 Recommended Actions
1. Prioritize 10 overdue urgent issues this week
2. Fu Zhibin is overloaded, consider redistributing tasks
3. Multiple issues created over 100 days ago need attention

━━━
```

---

## 🚀 Quick Start

### Step 1: View Available Tools

Send in DingTalk or Telegram:
```
/tools
```

Find subscription tools:
- `subscribe_project`
- `unsubscribe_project`
- `list_my_subscriptions`
- `get_subscription_stats`
- `generate_subscription_report`

### Step 2: Subscribe to First Project

Call tool via message:
```json
{
  "name": "subscribe_project",
  "arguments": {
    "project_id": 341,
    "frequency": "daily",
    "level": "brief",
    "push_time": "09:00"
  }
}
```

Or say in chat:
> Subscribe me to project 341, send brief report daily at 9 AM

### Step 3: View Subscriptions

```json
{
  "name": "list_my_subscriptions",
  "arguments": {}
}
```

### Step 4: Receive Reports

System automatically pushes reports to DingTalk/Telegram at configured times.

---

## 📖 Usage Examples

### Example 1: Subscribe Multiple Projects

```bash
# Xinshun CIM - Daily Brief
subscribe_project(project_id=341, frequency="daily", level="brief", push_time="09:00")

# GYRI MES - Daily Brief
subscribe_project(project_id=372, frequency="daily", level="brief", push_time="09:30")

# View subscriptions
list_my_subscriptions()
```

### Example 2: Modify Subscription

```bash
# Cancel first
unsubscribe_project(project_id=341)

# Resubscribe (change to detailed)
subscribe_project(project_id=341, frequency="daily", level="detailed", push_time="09:00")
```

### Example 3: Generate Ad-hoc Report

```bash
# Brief report
generate_subscription_report(project_id=341, level="brief")

# Detailed report
generate_subscription_report(project_id=341, level="detailed")
```

### Example 4: View Statistics

```bash
get_subscription_stats()
```

Returns:
```json
{
  "total_subscriptions": 2,
  "by_frequency": {"daily": 2},
  "by_channel": {"dingtalk": 2},
  "by_project": {"341": 1, "372": 1},
  "active_subscriptions": 2
}
```

---

## ⚙️ Configuration

### Environment Variables

Configure in `.env.docker`:

```bash
# Subscription configuration
SUBSCRIPTIONS_FILE=./data/subscriptions.json

# Push channels
DINGTALK_ENABLED=true
TELEGRAM_ENABLED=true

# Default settings
DEFAULT_SUBSCRIPTION_FREQUENCY=daily
DEFAULT_SUBSCRIPTION_LEVEL=brief
DEFAULT_PUSH_TIME=09:00
```

### Data Storage

Subscriptions stored in `./data/subscriptions.json`:

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
  }
}
```

---

## 🔍 FAQ

### Q1: How to change push time?

**A**: Cancel subscription and resubscribe with new `push_time`.

### Q2: Can I subscribe to multiple projects?

**A**: Yes, no limit.

### Q3: What's the difference between brief and detailed reports?

**A**: 
- Brief: ~500 tokens, key metrics + TOP 5 high priority issues
- Detailed: ~2000 tokens, full analysis + risk identification + recommendations

### Q4: How to pause subscription?

**A**: Use `unsubscribe_project()` to cancel, resubscribe when needed.

### Q5: Is email push supported?

**A**: Current version supports DingTalk and Telegram. Email is planned.

---

## 📞 Support

- **Documentation**: `/docker/redmine-mcp-server/docs/feature/`
- **Logs**: `docker logs redmine-mcp-server`
- **GitHub**: https://github.com/newmanspace/redmine-mcp-server

---

**Last Updated**: 2026-02-26  
**Maintainer**: OpenJaw <openjaw@gmail.com>
