# Redmine MCP Server - Issue Tracker Documentation

**Purpose**: Documentation standards and guidelines for issue reports.

---

## 📁 Documentation Structure

```
docs/issues/
├── README.md           # This file - Documentation guidelines
├── SUMMARY.md          # Current issue summary and fix progress
└── ISSUE-*.md          # Individual issue reports
```

---

## 📄 Document Types

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| `README.md` | Documentation standards and templates | Rarely (only when process changes) |
| `SUMMARY.md` | Current issue status and statistics | Weekly |
| `ISSUE-*.md` | Detailed issue reports | As needed |

---

## 📝 How to Create an Issue Report

### 1. Check Existing Issues

Before creating a new issue, check `SUMMARY.md` to avoid duplicates.

### 2. Create Issue File

Name the file: `ISSUE-XXX-brief-description.md`

Where `XXX` is the next sequential number (001, 002, 003, etc.)

### 3. Use the Template

Copy this template into your new issue file:

```markdown
# ISSUE-XXX - [Descriptive Title]

**Created**: YYYY-MM-DD  
**Severity**: 🔴 High / 🟡 Medium / 🟢 Low  
**Status**: ⏳ Pending / 🔄 In Progress / ✅ Fixed  
**Affected Files**: [List of files]

---

## Problem Description

[Clear description of the issue]

**Error Messages**:
```
[Paste error messages here]
```

**Logs**:
```
[Paste relevant logs here]
```

---

## Root Cause Analysis

[Explain the root cause]

**Problem Files**:
- `path/to/file.py` - [Description]

**Problem Code**:
```python
[Show problematic code]
```

---

## Solution

[Detailed fix steps]

**Fix Command**:
```bash
[Commands to apply fix]
```

**Files Modified**:
- `path/to/file.py` - [Change description]

---

## Verification Steps

```bash
[Commands to verify the fix]
```

**Expected Result**:
[What should happen]

---

## Prevention

[How to avoid this issue in future]

### 1. Code Review Checklist
- [ ] Item 1
- [ ] Item 2

### 2. Automated Tests
```python
[Test code example]
```

### 3. CI/CD Checks
```yaml
[CI configuration example]
```

---

**Reported By**: [Name]  
**Fixed By**: [Name]  
**Fixed Date**: YYYY-MM-DD
```

---

## 🏷️ Issue Severity Levels

### 🔴 High Severity
- Feature completely broken
- Data loss or corruption
- Security vulnerability
- **Response Time**: Immediate

### 🟡 Medium Severity
- Feature degraded but usable
- Performance issues
- **Response Time**: Within 24 hours

### 🟢 Low Severity
- Minor inconvenience
- Enhancement requests
- Documentation issues
- **Response Time**: Within 1 week

---

## 🔄 Issue Lifecycle

```
New Issue → Triage → In Progress → Fixed → Verified → Closed
```

### Status Definitions

| Status | Description |
|--------|-------------|
| ⏳ Pending | Issue reported, awaiting triage |
| 🔄 In Progress | Actively being fixed |
| ✅ Fixed | Code fix merged |
| 🔒 Closed | Verified and closed |

---

## 📊 Current Summary

For current issue statistics and status, see **[SUMMARY.md](./SUMMARY.md)**

---

## 🛠️ Related Documentation

- [Development Guidelines](../.qwen/skills/redmine/DEVELOPMENT_GUIDELINES.md)
- [Commitment Checklist](../.commitment-checklist.md)
- [Contributing Guide](../contributing.md)

---

**Last Updated**: 2026-03-01
