# Chinese to English Translation Guide

**Project**: Redmine MCP Server  
**Date**: 2026-02-27  
**Goal**: Translate all Chinese text to English (except i18n config files)

---

## Translation Principles

1. **Code First**: Translate user-facing code before documentation
2. **Consistency**: Use consistent terminology across all files
3. **Professional**: Use clear, professional English
4. **Preserve Functionality**: Don't change code logic, only comments and strings
5. **i18n Ready**: Move hardcoded Chinese to i18n files where appropriate

---

## Common Translations

### Status Names (状态名称)
| Chinese | English |
|---------|---------|
| 新建 | New |
| 进行中 | In Progress |
| 已解决 | Resolved |
| 已关闭 | Closed |
| 反馈 | Feedback |
| 测试中 | In Testing |

### Priority Names (优先级名称)
| Chinese | English |
|---------|---------|
| 立刻 | Immediate |
| 紧急 | Urgent |
| 高 | High |
| 普通 | Normal |
| 低 | Low |

### Report Types (报告类型)
| Chinese | English |
|---------|---------|
| 日报 | Daily Report |
| 周报 | Weekly Report |
| 月报 | Monthly Report |

### Report Levels (报告级别)
| Chinese | English |
|---------|---------|
| 简要 | Brief |
| 详细 | Detailed |
| 完整 | Comprehensive |

### Common Terms (常用术语)
| Chinese | English |
|---------|---------|
| 项目 | Project |
| 订阅 | Subscription |
| 推送 | Push/Send |
| 渠道 | Channel |
| 邮箱 | Email |
| 趋势分析 | Trend Analysis |
| 完成率 | Completion Rate |
| 平均解决天数 | Average Resolution Days |
| 高优先级 | High Priority |
| 人员负载 | Team Workload |
| 贡献者 | Contributor |
| 实施人员 | Implementation Team |
| 开发人员 | Developer |
| 测试人员 | Tester |
| 管理人员 | Manager |

---

## Files Priority

### Priority 1 (Critical - User Facing)
1. `mcp/tools/subscription_tools.py`
2. `mcp/tools/subscription_push_tools.py`
3. `mcp/tools/attachment_tools.py`
4. `dws/services/email_service.py`
5. `dws/services/subscription_service.py`
6. `dws/services/subscription_push_service.py`
7. `dws/services/report_generation_service.py`

### Priority 2 (Important - Business Logic)
1. `dws/services/trend_analysis_service.py`
2. `dws/services/analysis_service.py`
3. `dws/services/sync_service.py`
4. `scheduler/subscription_scheduler.py`
5. `scheduler/ads_scheduler.py`

### Priority 3 (Documentation)
1. All Markdown files in `docs/`
2. SQL comments in `init-scripts/`
3. Configuration comments in `.env*`

---

## Translation Patterns

### Docstring Translation
```python
# Before (Chinese)
def subscribe_project(...):
    """
    订阅项目报告
    
    Args:
        project_id: 项目 ID
        channel: 推送渠道
        
    Returns:
        订阅结果
    """

# After (English)
def subscribe_project(...):
    """
    Subscribe to project reports
    
    Args:
        project_id: Project ID
        channel: Push channel
        
    Returns:
        Subscription result
    """
```

### Comment Translation
```python
# Before (Chinese)
# 获取项目统计数据
stats = get_project_stats()

# After (English)
# Get project statistics
stats = get_project_stats()
```

### User Message Translation
```python
# Before (Chinese)
return {
    "success": True,
    "message": "已订阅项目 {project_id} 的{report_type}报告"
}

# After (English)
return {
    "success": True,
    "message": f"Subscribed to {report_type} report for project {project_id}"
}
```

### HTML Template Translation
```python
# Before (Chinese)
html = f"""
<h2>📊 {project_name} - 项目{report_type}</h2>
<p>报告日期：{date}</p>
"""

# After (English)
html = f"""
<h2>📊 {project_name} - {report_type}</h2>
<p>Report Date: {date}</p>
"""
```

---

## Quality Checklist

- [ ] All docstrings translated
- [ ] All user-facing messages translated
- [ ] All comments translated
- [ ] Hardcoded Chinese moved to i18n (if applicable)
- [ ] No Chinese in code (except i18n files)
- [ ] Consistent terminology used
- [ ] No broken code from translation
- [ ] All tests still pass

---

## Progress Tracking

See `TRANSLATION_PROGRESS.md` for detailed progress tracking.

---

**Last Updated**: 2026-02-27  
**Maintainer**: OpenJaw
