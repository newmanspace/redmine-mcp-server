# Redmine MCP Feature Documentation

This directory contains detailed documentation for all Redmine MCP Server features.

---

## 📋 Feature List

### ✅ Released Features

| Feature | Status | Version | Documentation |
|---------|--------|---------|---------------|
| **Project Subscription** | ✅ Released | v1.0 | [Description](./01-subscription-feature.md) \| [Design](./01-subscription-design.md) |
| **Data Synchronization** | ✅ Released | v1.2 | [Guide](./02-data-sync.md) |
| **Warehouse Integration** | ✅ Released | v1.0 | [Guide](../SUBSCRIPTION_GUIDE.md) |
| **Daily Report System** | ✅ Released | v1.0 | [Config](../REDMINE_DAILY_REPORT.md) |

---

## 🚀 Quick Start

### For Users

1. **Subscribe to Projects** → Read [Subscription Guide](./01-subscription-feature.md)
2. **Configure Sync** → Read [Sync Guide](./02-data-sync.md)
3. **Generate Reports** → Call `generate_subscription_report` tool

### For Developers

1. **Architecture** → Read [Design Overview](./01-subscription-design.md)
2. **Sync Strategies** → Read [Sync Documentation](./02-data-sync.md)
3. **Code Location** → `src/redmine_mcp_server/`
4. **Test Scripts** → `scripts/test-subscription.sh`, `scripts/manual-sync.py`

---

## 📖 Documentation Structure

```
docs/
├── feature/                    # Feature documentation
│   ├── README.md              # This file
│   ├── 01-subscription-feature.md   # Subscription feature description
│   └── 01-subscription-design.md    # Subscription feature design
├── SUBSCRIPTION_GUIDE.md      # Subscription usage guide
├── REDMINE_DAILY_REPORT.md    # Daily report system docs
└── tool-reference.md          # Tool reference manual
```

---

## 🛠️ Tool Index

### Subscription Management Tools

| Tool | Description | Docs |
|------|-------------|------|
| `subscribe_project` | Subscribe to project reports | [Description](./01-subscription-feature.md#1-subscribe_project) |
| `unsubscribe_project` | Cancel subscription | [Description](./01-subscription-feature.md#2-unsubscribe_project) |
| `list_my_subscriptions` | View subscriptions | [Description](./01-subscription-feature.md#3-list_my_subscriptions) |
| `get_subscription_stats` | Get statistics | [Description](./01-subscription-feature.md#4-get_subscription_stats) |
| `generate_subscription_report` | Generate report | [Description](./01-subscription-feature.md#5-generate_subscription_report) |

### Data Sync Tools

| Tool | Description | Docs |
|------|-------------|------|
| `trigger_full_sync` | Trigger full data sync | [Sync Guide](./02-data-sync.md#trigger_full_sync) |
| `trigger_progressive_sync` | Trigger progressive weekly sync | [Sync Guide](./02-data-sync.md#trigger_progressive_sync) |
| `get_sync_progress` | Get sync progress status | [Sync Guide](./02-data-sync.md#get_sync_progress) |

### Other Tools

See [Tool Reference Manual](../tool-reference.md)

---

## 🔍 Search Documentation

### By Topic

- **Subscription Config** → [Feature Description - Config](./01-subscription-feature.md#configuration)
- **Report Format** → [Feature Description - Report Content](./01-subscription-feature.md#report-content)
- **Sync Strategies** → [Sync Guide - Overview](./02-data-sync.md#overview)
- **Incremental Sync** → [Sync Guide - Incremental](./02-data-sync.md#2-incremental-sync-automatic)
- **Full Sync** → [Sync Guide - Full Sync](./02-data-sync.md#3-full-sync-manual)
- **Architecture** → [Design - Architecture](./01-subscription-design.md#architecture)
- **Data Flow** → [Design - Data Flow](./01-subscription-design.md#data-flow)

### By Question

- **How to subscribe** → [Subscription Guide - Quick Start](./01-subscription-feature.md#quick-start)
- **Configure push time** → [Subscription Guide - Push Config](./01-subscription-feature.md#push-configuration)
- **How to sync data** → [Sync Guide - Usage Examples](./02-data-sync.md#usage-examples)
- **Check sync progress** → [Sync Guide - Monitoring](./02-data-sync.md#monitoring)
- **Troubleshooting** → [Sync Guide - Troubleshooting](./02-data-sync.md#troubleshooting)

---

## 📞 Get Help

### Documentation Issues

- Missing docs → Submit Issue to GitHub
- Doc errors → Submit PR to fix

### Usage Questions

- Feature inquiry → Ask in DingTalk/Telegram
- Technical support → Check [Troubleshooting](./01-subscription-design.md#troubleshooting)

### Code Issues

- Bug reports → GitHub Issues
- Feature requests → GitHub Discussions

---

## 📈 Changelog

### v1.2 (2026-02-26)

- ✅ Data synchronization system
- ✅ Incremental sync (auto, every 10 min)
- ✅ Full sync (manual, from project creation)
- ✅ Progressive sync (manual, weekly)
- ✅ Sync progress tracking
- ✅ Bug fix: `status_id=*` for all issues

### v1.0 (2026-02-26)

- ✅ Release project subscription feature
- ✅ 5 subscription management tools
- ✅ Brief/Detailed report generation
- ✅ DingTalk/Telegram push support
- ✅ Complete documentation

---

## 🔗 Related Links

- **GitHub**: https://github.com/newmanspace/redmine-mcp-server
- **Docs**: /docker/redmine-mcp-server/docs/
- **Code**: /docker/redmine-mcp-server/src/redmine_mcp_server/

---

**Last Updated**: 2026-02-26  
**Maintainer**: OpenJaw <openjaw@gmail.com>
