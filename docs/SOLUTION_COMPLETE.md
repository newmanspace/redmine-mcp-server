# Redmine MCP 数仓 - 完整解决方案

**完成时间**: 2026-02-27 18:40  
**版本**: 1.0  
**状态**: ✅ 已完成并验证

---

## 一、解决方案概述

### 1.1 核心功能

基于 Journals 的完整 Issue 生命周期分析，包括：
- ✅ Issue 基本信息同步
- ✅ Journals（变更日志）同步
- ✅ Journal Details（变更明细）同步
- ✅ 状态历史追踪（开始/结束时间）
- ✅ 基于变更历史的角色分析
- ✅ 状态耗时分析

### 1.2 数据架构

```
Redmine API
    ↓
solution_sync.py (同步脚本)
    ↓
ODS 层
├── ods_issues              - Issue 基本信息 (63 个)
├── ods_journals            - 变更日志 (197 条)
├── ods_journal_details     - 变更明细 (467 条)
└── ods_issue_status_history - 状态历史 (190 条) ⭐新增
    ↓
solution_analysis.py (分析脚本)
    ↓
分析报告
```

---

## 二、工具脚本

### 2.1 同步工具

**文件**: `/docker/redmine-mcp-server/tools/solution_sync.py`

**功能**:
- 阶段 1: 同步所有 Issue（包含已关闭）
- 阶段 2: 同步所有 Journals 和 Details
- 阶段 3: 构建状态历史（自动计算开始/结束时间）

**使用方法**:
```bash
docker cp tools/solution_sync.py redmine-mcp-server:/app/tools/
docker exec redmine-mcp-server python3 /app/tools/solution_sync.py <project_id>
```

### 2.2 分析工具

**文件**: `/docker/redmine-mcp-server/tools/solution_analysis.py`

**功能**:
- 基本信息统计
- 状态分布
- Journals 统计
- 基于 Journals 的角色分析（开发/测试/实施）
- 状态耗时分析（平均/最短/最长）
- 整体周期分析
- 月度趋势

**使用方法**:
```bash
docker cp tools/solution_analysis.py redmine-mcp-server:/app/tools/
docker exec redmine-mcp-server python3 /app/tools/solution_analysis.py <project_id>
```

---

## 三、数据库表结构

### 3.1 新增表

```sql
-- Issue 状态历史表
CREATE TABLE warehouse.ods_issue_status_history (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    status_name VARCHAR(100),
    started_at TIMESTAMP NOT NULL,      -- 状态开始时间
    ended_at TIMESTAMP,                  -- 状态结束时间
    duration_hours DECIMAL(10,2),        -- 持续时间（小时）
    changed_by_user_id INTEGER,          -- 变更人 ID
    changed_by_login VARCHAR(100),       -- 变更人登录名
    journal_id INTEGER,                  -- 关联 Journal ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 索引

```sql
CREATE INDEX idx_status_history_issue ON warehouse.ods_issue_status_history(issue_id);
CREATE INDEX idx_status_history_status ON warehouse.ods_issue_status_history(status_id);
CREATE INDEX idx_status_history_user ON warehouse.ods_issue_status_history(changed_by_user_id);
CREATE INDEX idx_status_history_started ON warehouse.ods_issue_status_history(started_at);
```

---

## 四、分析逻辑

### 4.1 角色识别

| 角色 | 判断逻辑 | SQL 条件 |
|------|---------|---------|
| **开发人员** | 将状态改为"已解决" | `new_value = '3'` |
| **测试人员** | 将状态改为"已关闭" | `new_value = '5'` |
| **实施人员** | 将状态从"新建"改为"进行中" | `old_value = '1' AND new_value = '2'` |

### 4.2 时间计算

```python
# 状态持续时间（小时）
duration_hours = EXTRACT(EPOCH FROM (ended_at - started_at)) / 3600

# 整体周期
total_cycle = SUM(duration_hours) for all statuses
```

---

## 五、PMS 项目 (357) 分析结果

### 5.1 数据同步

| 数据类型 | 数量 | 状态 |
|----------|------|------|
| Issues | 63 | ✅ 100% |
| Journals | 197 | ✅ 完整 |
| Journal Details | 467 | ✅ 完整 |
| 状态历史 | 190 | ✅ 完整 |

### 5.2 角色工作量（基于 Journals）

| 成员 | 开发 | 测试 | 实施 | 总计 |
|------|------|------|------|------|
| **yajiao.liu** (刘雅娇) | 19 | 13 | 0 | **32** |
| **ju.zeng** (曾聚) | 0 | 0 | 20 | **20** |
| **shijie.deng** (邓时杰) | 1 | 2 | 0 | **3** |

**关键发现**:
- 刘雅娇：既是开发 (19) 也是测试 (13)，多面手
- 曾聚：专职实施 (20)，负责启动工作
- 角色分工明确，基于实际变更历史

### 5.3 状态耗时分析

| 状态 | 样本数 | 平均耗时 | 最短 | 最长 |
|------|--------|---------|------|------|
| **已解决** | 30 | 2.1 周 | 0h | 1565h |
| **待发版** | 11 | 1.6 周 | 216h | 822h |
| **反馈** | 11 | 6.6 天 | 0h | 1221h |
| **代码审查** | 27 | 2.2 天 | 0h | 712h |
| **测试中** | 32 | 23.2 小时 | 0h | 187h |
| **进行中** | 29 | 0.1 小时 | 0h | 1.5h |

**瓶颈识别**:
- "已解决"状态平均耗时 2.1 周，需要优化
- "待发版"和"反馈"状态耗时较长

### 5.4 整体周期

| 指标 | 数值 |
|------|------|
| 已完成 Issue | 15 个 |
| 平均周期 | 5.5 周 |
| 最短周期 | 45.6 小时 |
| 最长周期 | 1533.4 小时 (约 64 天) |

---

## 六、使用指南

### 6.1 完整流程

```bash
# 1. 同步数据
docker cp tools/solution_sync.py redmine-mcp-server:/app/tools/
docker exec redmine-mcp-server python3 /app/tools/solution_sync.py 357

# 2. 生成分析报告
docker cp tools/solution_analysis.py redmine-mcp-server:/app/tools/
docker exec redmine-mcp-server python3 /app/tools/solution_analysis.py 357

# 3. 查看报告
# 报告将直接输出到终端
```

### 6.2 扩展其他项目

```bash
# CIM 主项目 (341)
python3 solution_sync.py 341
python3 solution_analysis.py 341

# AMS 项目 (356)
python3 solution_sync.py 356
python3 solution_analysis.py 356
```

---

## 七、优势与价值

### 7.1 数据准确性

- ✅ 基于实际变更历史，而非当前状态
- ✅ 自动计算状态持续时间
- ✅ 公平的工作量统计

### 7.2 分析深度

- ✅ 识别实际工作角色（开发/测试/实施）
- ✅ 发现流程瓶颈（状态耗时分析）
- ✅ 量化整体周期

### 7.3 决策支持

- ✅ 公平绩效评估
- ✅ 流程优化依据
- ✅ 资源分配参考

---

## 八、后续扩展

### 8.1 增量同步

开发增量同步脚本，仅同步变更的 Journals。

### 8.2 报表导出

支持导出 CSV/Excel 格式报表。

### 8.3 可视化

集成 Grafana 或其他可视化工具。

---

**维护者**: OpenJaw  
**项目**: Redmine MCP Server  
**文档位置**: `/docker/redmine-mcp-server/docs/SOLUTION_COMPLETE.md`
