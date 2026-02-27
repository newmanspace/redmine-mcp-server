# Redmine Issue 贡献者分析 - 方案总结

## 一、核心逻辑

### 角色分类规则

按项目 Memberships 中的**最高角色**定义：

```
管理人员 (3) > 实施人员 (8) > 开发人员 (4) > 测试人员 (7) > 报告人员 (5) > 查询人员 (6)
```

### 贡献者识别

从 Issue 的 `journals` 中提取所有有操作记录的用户，而不是仅看 `assigned_to`。

### 覆盖规则

同一用户在 journals 中多次出现时，后面的操作覆盖前面的（统计时累加，角色以项目中最高为准）。

---

## 二、文件结构

```
/home/oracle/.openclaw/workspace/
├── docs/
│   ├── redmine-issue-analysis-schema.md    # 详细表结构设计
│   └── redmine-issue-analysis-summary.md   # 本文件（方案总结）
├── tools/
│   └── redmine_issue_analyzer.py           # 分析工具（Python）
└── issue_76361_analysis.json               # 示例输出
```

---

## 三、使用方法

### 命令行调用

```bash
cd /home/oracle/.openclaw/workspace
python3 tools/redmine_issue_analyzer.py <issue_id> <project_id>

# 示例
python3 tools/redmine_issue_analyzer.py 76361 357
```

### 输出

1. **终端输出**: 打印分析摘要
2. **JSON 文件**: `issue_<ID>_analysis.json`（当前目录）

### JSON 输出结构

```json
{
  "issue_id": 76361,
  "project_id": 357,
  "issue_subject": "【UAC】审计日志搬迁",
  "issue_status": "已解决",
  "contributors": [
    {
      "user_id": 1531,
      "user_name": "曾 聚",
      "highest_role_id": 4,
      "highest_role_name": "开发人员",
      "role_category": "developer",
      "journal_count": 2,
      "first_contribution": "2026-02-09T09:03:02Z",
      "last_contribution": "2026-02-09T09:18:57Z",
      "contribution_types": {
        "status_change": 2,
        "assigned_to_change": 1,
        "note_added": 1,
        "other_change": 1
      }
    }
  ],
  "summary": {
    "manager": [],
    "implementation": [...],
    "developer": [...],
    "tester": [],
    "other": []
  },
  "analyzed_at": "2026-02-27T08:45:25.261109"
}
```

---

## 四、核心函数

### `analyze_issue_contributors(issue_id, project_id)`

主分析函数，返回完整的分析结果。

**参数:**
- `issue_id`: Issue ID (int)
- `project_id`: 项目 ID (int)

**返回:**
```python
{
    "issue_id": int,
    "project_id": int,
    "contributors": List[dict],
    "summary": dict,
    "analyzed_at": str
}
```

### `get_user_highest_role_from_memberships(user_id, memberships)`

从项目成员列表中查找用户的最高角色。

**返回:**
```python
(role_id, role_name, role_category)
# 示例：(4, "开发人员", "developer")
```

### `extract_contributors_from_journals(journals)`

从 journals 中提取贡献者信息。

**返回:**
```python
{
    user_id: {
        "name": str,
        "journal_count": int,
        "first_contribution": str,
        "last_contribution": str,
        "contribution_types": dict
    }
}
```

---

## 五、API 依赖

需要以下 Redmine API 端点：

| 端点 | 用途 |
|------|------|
| `GET /issues/{id}.json?include=journals` | 获取 Issue 及变更历史 |
| `GET /projects/{id}/memberships.json` | 获取项目成员角色 |
| `GET /roles.json` | 获取角色定义（内置） |

---

## 六、整合方案

### 方案 A: 直接调用 Python 脚本

适合一次性分析或批处理：

```bash
# 单个 Issue
python3 tools/redmine_issue_analyzer.py 76361 357

# 批量分析（示例）
for issue_id in 76361 76362 76363; do
    python3 tools/redmine_issue_analyzer.py $issue_id 357
done
```

### 方案 B: 作为 Module 导入

在其他 Python 脚本中调用：

```python
from tools.redmine_issue_analyzer import analyze_issue_contributors

result = analyze_issue_contributors(76361, 357)
print(f"开发人员：{len(result['summary']['developer'])} 人")
```

### 方案 C: 集成到数据库

如果需要持久化存储，可以：

1. 创建 PostgreSQL/SQLite 数据库
2. 按照 `redmine-issue-analysis-schema.md` 创建表
3. 修改脚本将结果写入数据库而非 JSON 文件

### 方案 D: 定时任务

使用 cron 定期分析：

```bash
# 每天凌晨 2 点分析指定项目的所有 Issue
0 2 * * * cd /home/oracle/.openclaw/workspace && \
    python3 tools/redmine_issue_analyzer.py <issue_id> 357
```

---

## 七、曾聚案例分析

### 问题

Issue 76361 中，曾聚是实际开发人员，但容易被遗漏。

### 原因

1. 当前 `assigned_to` 是刘雅娇
2. 曾聚在 2026-02-09 提交代码后将任务转出
3. 传统统计只看"当前负责人"或"最后处理人"

### 解决方案

使用本分析工具：

```bash
python3 tools/redmine_issue_analyzer.py 76361 357
```

**结果:**
- 刘雅娇：实施人员（7 次操作）
- 曾聚：**开发人员**（2 次操作）✅

曾聚被正确识别为开发人员，因为：
1. 他在 journals 中有实际贡献记录
2. 在项目 357 中的最高角色是**开发人员**

---

## 八、后续扩展建议

### 1. 组角色继承

当前版本只处理直接用户成员，未处理通过组间接获得的角色。

**改进:** 当用户在项目中未直接定义角色时，查询其所属组的角色。

### 2. 跨项目分析

分析用户在多个项目中的角色和贡献。

### 3. 工作量统计

结合 `spent_hours` 和 journal 操作次数，估算工作量。

### 4. 时间线可视化

生成 Issue 状态变更时间线，展示每个贡献者的操作时间点。

### 5. 导出报表

支持导出 Excel/CSV 格式，便于汇报。

---

## 九、注意事项

1. **API 限流**: Redmine API 可能有速率限制，批量分析时注意间隔
2. **数据缓存**: 项目成员信息变化不频繁，可缓存减少 API 调用
3. **权限**: 确保 API Key 有足够权限访问目标项目和 Issue
4. **时区**: 所有时间戳为 UTC，显示时需转换时区

---

## 十、相关文件

- [`redmine-issue-analysis-schema.md`](./redmine-issue-analysis-schema.md) - 详细表结构设计
- [`tools/redmine_issue_analyzer.py`](../tools/redmine_issue_analyzer.py) - 分析工具源码
- [`issue_76361_analysis.json`](../issue_76361_analysis.json) - 示例输出
