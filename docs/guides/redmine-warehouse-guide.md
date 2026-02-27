# Redmine 数据仓库使用指南

## 一、项目结构

```
/home/oracle/.openclaw/workspace/
├── redmine_warehouse.db              # SQLite 数据库
├── docs/
│   ├── redmine-warehouse-schema.md   # 详细表结构设计
│   ├── redmine-issue-analysis-schema.md
│   └── redmine-issue-analysis-summary.md
└── tools/
    ├── redmine_warehouse_init.py     # 数据库初始化
    ├── redmine_warehouse_etl.py      # 完整 ETL 工具
    ├── redmine_warehouse_demo.py     # 演示脚本
    └── redmine_issue_analyzer.py     # Issue 分析工具
```

## 二、快速开始

### 1. 初始化数据库

```bash
cd /home/oracle/.openclaw/workspace/tools
python3 redmine_warehouse_init.py
```

### 2. 运行演示（同步项目 357 + Issue 76361）

```bash
python3 redmine_warehouse_demo.py
```

### 3. 查看结果

```bash
python3 redmine_warehouse_init.py stats
```

## 三、完整 ETL 流程

### 全量同步 + 转换 + 聚合

```bash
python3 redmine_warehouse_etl.py full-pipeline
```

### 分步执行

```bash
# 1. 同步原始数据
python3 redmine_warehouse_etl.py sync-all

# 2. 数据转换
python3 redmine_warehouse_etl.py transform

# 3. 数据聚合
python3 redmine_warehouse_etl.py aggregate
```

### 增量同步

```bash
# 只同步 Issue
python3 redmine_warehouse_etl.py sync-issues

# 只同步 Journals
python3 redmine_warehouse_etl.py sync-journals

# 只同步项目成员
python3 redmine_warehouse_etl.py sync-memberships
```

## 四、数仓分层说明

### ODS 层 (原始数据层)

存储从 Redmine API 同步的原始数据：

| 表名 | 说明 |
|------|------|
| `ods_projects` | 项目信息 |
| `ods_users` | 用户信息 |
| `ods_issues` | Issue 基本信息 |
| `ods_journals` | Issue 变更日志 |
| `ods_journal_details` | 变更明细 |
| `ods_project_memberships` | 项目成员 |
| `ods_project_member_roles` | 成员角色 |
| `ods_roles` | 角色定义 |
| `ods_trackers` | Tracker 类型 |
| `ods_issue_statuses` | Issue 状态 |

### DWD 层 (明细数据层)

清洗后的明细数据，关联了维度信息：

| 表名 | 说明 |
|------|------|
| `dwd_issues_full` | Issue 完整明细（关联项目、状态、用户等） |
| `dwd_user_project_role` | 用户在项目中的角色（按优先级取最高） |
| `dwd_issue_contributors` | Issue 贡献者分析（按角色分类） |
| `dwd_journal_summary` | Journal 汇总统计 |

### DWS 层 (汇总数据层)

聚合统计信息：

| 表名 | 说明 |
|------|------|
| `dws_project_daily_stats` | 项目每日统计 |
| `dws_project_contributor_stats` | 项目贡献者统计 |
| `dws_project_role_distribution` | 项目角色分布 |
| `dws_issue_contributor_summary` | Issue 贡献者汇总 |
| `dws_user_monthly_workload` | 用户月度工作量 |
| `dws_tracker_distribution` | Tracker 类型分布 |

### ADS 层 (应用数据层)

面向应用的报表数据：

| 表名 | 说明 |
|------|------|
| `ads_project_status_report` | 项目状态报表 |
| `ads_user_workload_ranking` | 用户工作量排名 |
| `ads_issue_quality_report` | Issue 质量报表 |
| `ads_team_load_analysis` | 团队负载分析 |

### 维度表

| 表名 | 说明 |
|------|------|
| `dim_role_category` | 角色分类维度 |
| `dim_date` | 日期维度 |

## 五、角色分类规则

| 角色 ID | 角色名称 | 分类 | 优先级 |
|--------|---------|------|--------|
| 3 | 管理人员 | manager | 1 (最高) |
| 8 | 实施人员 | implementation | 2 |
| 4 | 开发人员 | developer | 3 |
| 7 | 测试人员 | tester | 4 |
| 5 | 报告人员 | reporter | 5 |
| 6 | 查询人员 | viewer | 6 (最低) |

**规则**: 用户在项目中的角色按**最高优先级**确定。

## 六、常用查询示例

### 1. 查询 Issue 的贡献者分布

```sql
SELECT 
    c.user_name,
    c.role_category,
    c.highest_role_name,
    c.journal_count,
    c.first_contribution,
    c.last_contribution
FROM dwd_issue_contributors c
WHERE c.issue_id = 76361
ORDER BY 
    CASE c.role_category 
        WHEN 'manager' THEN 1 
        WHEN 'implementation' THEN 2 
        WHEN 'developer' THEN 3 
        WHEN 'tester' THEN 4 
        ELSE 5 
    END;
```

### 2. 查询项目角色分布

```sql
SELECT 
    role_category,
    COUNT(DISTINCT user_id) as member_count
FROM dwd_user_project_role
WHERE project_id = 357
GROUP BY role_category
ORDER BY 
    CASE role_category 
        WHEN 'manager' THEN 1 
        WHEN 'implementation' THEN 2 
        WHEN 'developer' THEN 3 
        WHEN 'tester' THEN 4 
        ELSE 5 
    END;
```

### 3. 查询 Issue 汇总统计

```sql
SELECT 
    issue_id,
    manager_count,
    implementation_count,
    developer_count,
    tester_count,
    total_contributors,
    total_journals
FROM dws_issue_contributor_summary
WHERE project_id = 357;
```

### 4. 查询开发人员工作量

```sql
SELECT 
    c.user_name,
    COUNT(DISTINCT c.issue_id) as issues_involved,
    SUM(c.journal_count) as total_operations,
    SUM(i.spent_hours) as total_hours
FROM dwd_issue_contributors c
JOIN dwd_issues_full i ON c.issue_id = i.issue_id
WHERE c.role_category = 'developer'
  AND i.project_id = 357
GROUP BY c.user_id, c.user_name
ORDER BY issues_involved DESC;
```

### 5. 查询项目每日趋势

```sql
SELECT 
    stat_date,
    total_issues,
    new_issues,
    closed_issues,
    open_issues,
    active_contributors
FROM dws_project_daily_stats
WHERE project_id = 357
ORDER BY stat_date;
```

## 七、Python 查询示例

```python
import sqlite3

DB_PATH = '/home/oracle/.openclaw/workspace/redmine_warehouse.db'

def query_issue_contributors(issue_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_name, role_category, journal_count
        FROM dwd_issue_contributors
        WHERE issue_id = ?
        ORDER BY role_category
    """, (issue_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"name": r[0], "category": r[1], "journals": r[2]}
        for r in results
    ]

# 使用
contributors = query_issue_contributors(76361)
for c in contributors:
    print(f"{c['name']}: {c['category']} ({c['journals']} ops)")
```

## 八、定时同步建议

### Cron 配置示例

```bash
# 每天凌晨 2 点全量同步
0 2 * * * cd /home/oracle/.openclaw/workspace/tools && \
    python3 redmine_warehouse_etl.py full-pipeline >> /var/log/redmine_wh.log 2>&1

# 每小时增量同步 Journals
0 * * * * cd /home/oracle/.openclaw/workspace/tools && \
    python3 redmine_warehouse_etl.py sync-journals >> /var/log/redmine_wh.log 2>&1
```

### 增量同步策略

1. **Projects/Users/Groups**: 每周同步一次（变化少）
2. **Issues**: 每天同步一次
3. **Journals**: 每小时同步一次（频繁变更）
4. **Memberships**: 每周同步一次

## 九、演示结果示例

Issue #76361 分析结果：

```
【Issue #76361 贡献者分析】
------------------------------------------------------------
  👤 雅娇 刘
     角色分类：implementation (实施人员)
     操作次数：7
     时间范围：2026-01-05T01:14 ~ 2026-02-13T07:46

  👤 聚 曾
     角色分类：developer (开发人员)
     操作次数：2
     时间范围：2026-02-09T09:03 ~ 2026-02-09T09:18

【Issue #76361 角色分布汇总】
------------------------------------------------------------
  管理人员：0
  实施人员：1
  开发人员：1  ✅ 曾聚被正确识别
  测试人员：0
  其他：0
  ─────────────────
  总贡献者：2
  总操作数：9
```

## 十、扩展建议

### 1. 增加更多统计维度

- Issue 重开次数统计
- 平均解决时间分析
- 超期 Issue 分析
- 人员负载预警

### 2. 数据可视化

- 使用 Grafana 连接 SQLite
- 导出到 Excel/CSV
- 生成 PDF 报表

### 3. 数据导出 API

```python
# 创建简单的 REST API
from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/api/project/<int:project_id>/contributors')
def project_contributors(project_id):
    conn = sqlite3.connect('redmine_warehouse.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_name, role_category, COUNT(*) as issue_count
        FROM dwd_issue_contributors
        WHERE project_id = ?
        GROUP BY user_id, role_category
    """, (project_id,))
    results = cursor.fetchall()
    conn.close()
    return jsonify(results)
```

### 4. 数据质量监控

- 同步失败告警
- 数据完整性检查
- 延迟监控

## 十一、故障排查

### 问题：API 401 错误

**原因**: API Key 无效或过期

**解决**: 检查 `API_KEY` 配置，确认有足够权限

### 问题：同步速度慢

**原因**: 分页获取大量数据

**解决**: 
- 增加 `limit` 参数
- 使用多线程
- 只同步需要的项目

### 问题：数据库锁定

**原因**: 并发写入

**解决**: 
- 避免并发执行 ETL
- 使用 WAL 模式：`PRAGMA journal_mode=WAL;`

## 十二、相关文件

- [`redmine-warehouse-schema.md`](./redmine-warehouse-schema.md) - 详细表结构
- [`redmine-issue-analysis-summary.md`](./redmine-issue-analysis-summary.md) - Issue 分析方案
- [`tools/redmine_warehouse_init.py`](../tools/redmine_warehouse_init.py) - 初始化脚本
- [`tools/redmine_warehouse_etl.py`](../tools/redmine_warehouse_etl.py) - ETL 工具
- [`tools/redmine_warehouse_demo.py`](../tools/redmine_warehouse_demo.py) - 演示脚本
