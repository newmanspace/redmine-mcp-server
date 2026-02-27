# Redmine MCP 数仓 - 完整解决方案设计

**版本**: 1.0  
**日期**: 2026-02-27  
**目标**: 基于 Journals 的完整 Issue 生命周期分析

---

## 一、数据同步架构

### 1.1 数据层次

```
Redmine API
    ↓
同步脚本 (complete_sync.py)
    ↓
ODS 层 (原始数据)
├── ods_issues           - Issue 基本信息
├── ods_journals         - 变更日志
├── ods_journal_details  - 变更明细
└── ods_issue_status_history (新增) - 状态历史追踪
    ↓
分析脚本 (complete_analysis.py)
    ↓
分析报告
```

### 1.2 新增表设计

```sql
-- Issue 状态历史表
CREATE TABLE IF NOT EXISTS warehouse.ods_issue_status_history (
    id BIGSERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    status_name VARCHAR(100),
    started_at TIMESTAMP NOT NULL,      -- 状态开始时间
    ended_at TIMESTAMP,                  -- 状态结束时间
    duration_hours DECIMAL(10,2),        -- 状态持续时间（小时）
    changed_by_user_id INTEGER,          -- 变更人
    changed_by_login VARCHAR(100),       -- 变更人登录名
    journal_id INTEGER,                  -- 关联的 Journal ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_status_history_issue ON warehouse.ods_issue_status_history(issue_id);
CREATE INDEX idx_status_history_status ON warehouse.ods_issue_status_history(status_id);
CREATE INDEX idx_status_history_user ON warehouse.ods_issue_status_history(changed_by_user_id);
CREATE INDEX idx_status_history_started ON warehouse.ods_issue_status_history(started_at);

-- 注释
COMMENT ON TABLE warehouse.ods_issue_status_history IS 'Issue 状态历史追踪表 - 记录每个状态的开始/结束时间';
COMMENT ON COLUMN warehouse.ods_issue_status_history.started_at IS '进入该状态的时间';
COMMENT ON COLUMN warehouse.ods_issue_status_history.ended_at IS '离开该状态的时间（NULL 表示当前状态）';
COMMENT ON COLUMN warehouse.ods_issue_status_history.duration_hours IS '在该状态花费的时间（小时）';
```

---

## 二、同步流程

### 2.1 Issue 同步

```python
def sync_issues(project_id):
    """同步所有 Issue 基本信息"""
    # 1. 获取 Issue 列表（包含所有状态）
    # 2. 批量插入/更新到 ods_issues
    # 3. 返回 Issue ID 列表
```

### 2.2 Journals 同步

```python
def sync_journals(project_id, issue_ids):
    """同步所有 Issue 的 Journals"""
    # 1. 遍历每个 Issue
    # 2. 获取 Issue 详情（include=journals）
    # 3. 插入 Journals 到 ods_journals
    # 4. 插入 Details 到 ods_journal_details
```

### 2.3 状态历史构建

```python
def build_status_history(project_id):
    """从 Journals 构建状态历史"""
    # 1. 查询所有 status_id 变更的 Journal Details
    # 2. 按 Issue 和 时间排序
    # 3. 计算每个状态的开始/结束时间
    # 4. 插入到 ods_issue_status_history
```

---

## 三、分析指标

### 3.1 角色分析（基于 Journals）

| 角色 | 判断逻辑 |
|------|---------|
| **开发人员** | 将状态改为"已解决"（status_id=3） |
| **测试人员** | 将状态改为"已关闭"（status_id=5） |
| **实施人员** | 将状态从"新建"改为"进行中"（1→2） |

### 3.2 时间分析

| 指标 | 计算方式 |
|------|---------|
| **新建停留时间** | 状态 1 的持续时间 |
| **开发耗时** | 状态 2（进行中）的持续时间 |
| **测试耗时** | 状态 7（测试中）的持续时间 |
| **总周期** | 从新建到已关闭的总时间 |
| **状态流转效率** | 各状态平均耗时对比 |

### 3.3 报表类型

1. **项目概览报表**
   - Issue 总数/状态分布
   - 团队成员工作量
   - 平均周期时间

2. **成员绩效报表**
   - 开发/测试/实施工作量
   - 平均处理时间
   - 关闭率

3. **时间分析报表**
   - 各状态平均耗时
   - 瓶颈状态识别
   - 趋势分析

---

## 四、工具脚本

### 4.1 同步工具

| 脚本 | 功能 |
|------|------|
| `complete_sync.py` | Issues + Journals + 状态历史完整同步 |
| `sync_incremental.py` | 增量同步（仅同步变更） |

### 4.2 分析工具

| 脚本 | 功能 |
|------|------|
| `complete_analysis.py` | 完整分析报告（角色 + 时间） |
| `time_analysis.py` | 专项时间分析 |
| `role_analysis.py` | 专项角色分析 |

### 4.3 报表工具

| 脚本 | 功能 |
|------|------|
| `generate_report.py` | 生成 Markdown 报告 |
| `export_csv.py` | 导出 CSV 数据 |

---

## 五、使用流程

```bash
# 1. 完整同步
python3 tools/complete_sync.py 357

# 2. 构建状态历史
python3 tools/build_status_history.py 357

# 3. 生成分析报告
python3 tools/complete_analysis.py 357

# 4. 导出报表
python3 tools/generate_report.py 357 --output report.md
```

---

## 六、预期成果

### 6.1 数据完整性

- ✅ Issue 基本信息 100%
- ✅ Journals 100%
- ✅ Journal Details 100%
- ✅ 状态历史 100%

### 6.2 分析准确性

- ✅ 角色识别准确（基于实际变更）
- ✅ 时间统计准确（基于状态历史）
- ✅ 工作量统计准确（基于 Journals）

### 6.3 报表价值

- ✅ 识别瓶颈状态
- ✅ 优化工作流程
- ✅ 公平绩效评估

---

**维护者**: OpenJaw  
**项目**: Redmine MCP Server
