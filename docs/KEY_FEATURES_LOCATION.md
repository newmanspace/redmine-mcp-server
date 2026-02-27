# Redmine MCP - 关键功能代码位置

**更新时间**: 2026-02-27 20:50

---

## 一、全量同步与增量同步

### 📁 代码位置

**文件**: `/docker/redmine-mcp-server/src/redmine_mcp_server/redmine_scheduler.py`

**核心方法**: `_sync_project()` (第 100-220 行)

### 1.1 增量同步 (Incremental Sync)

**位置**: 第 138-143 行

```python
elif incremental:
    # 增量同步：获取最近 13 分钟更新的 Issue
    since = datetime.now() - timedelta(minutes=13)
    params['updated_on'] = f'>={since.strftime("%Y-%m-%d %H:%M:%S")}'
    logger.info(f"Incremental sync for project {project_id} since {since} (13-min window)")
```

**逻辑**:
1. 计算 13 分钟前的时间点（包含缓冲时间，防止数据丢失）
2. 查询 `updated_on >= 13 分钟前` 的所有 Issue
3. 批量同步到数仓

**调用位置**:
- 定时任务：每 10 分钟执行一次
- 第 257 行：`_sync_all_projects(full=False)`

### 1.2 全量同步 (Full Sync)

**位置**: 第 145-156 行

```python
else:
    # 全量同步：从项目创建日期开始
    project_created = self._get_project_created_date(project_id)
    if project_created:
        params['created_on'] = f'>={project_created.strftime("%Y-%m-%d")}'
        logger.info(f"Full sync for project {project_id}, from project creation")
    else:
        # 无创建日期时，同步所有 Issue
        logger.info(f"Full sync for project {project_id}, syncing all issues")
```

**逻辑**:
1. 获取项目创建日期
2. 查询 `created_on >= 项目创建日期` 的所有 Issue
3. 分页获取所有数据（无限制）
4. 批量同步到数仓

**调用位置**:
- MCP 工具：`trigger_full_sync()` (redmine_handler.py)
- 第 257 行：`_sync_all_projects(full=True)`

### 1.3 渐进式同步 (Progressive Sync)

**位置**: 第 121-136 行

```python
if progressive:
    # 渐进式周同步：每次同步一周的数据
    sync_start = self._get_progressive_sync_start(project_id)
    sync_end = sync_start + timedelta(days=7)
    if sync_end > datetime.now():
        sync_end = datetime.now()
    
    params['created_on'] = f'>={sync_start.strftime("%Y-%m-%d")}'
    logger.info(f"Progressive sync for project {project_id}: from {sync_start}")
```

**逻辑**:
1. 从项目创建日期开始（或上次同步结束日期）
2. 每次同步 7 天的数据
3. 更新进度跟踪
4. 下次继续同步下一周

**用途**: 避免一次性同步大量历史数据导致超时

### 1.4 同步流程对比

| 类型 | 时间范围 | 频率 | 数据量 | 用途 |
|------|---------|------|--------|------|
| **增量同步** | 最近 13 分钟 | 每 10 分钟 | 少 | 日常更新 |
| **全量同步** | 项目创建至今 | 手动/每天 | 多 | 初始化/修复 |
| **渐进式** | 每周数据 | 每次 1 周 | 中 | 历史数据回填 |

---

## 二、基于 Project Members 的角色分析

### 📁 代码位置

**文件**: `/docker/redmine-mcp-server/src/redmine_mcp_server/dev_test_analyzer.py`

**核心方法**: `get_project_member_roles()` (第 382-450 行)

### 2.1 获取项目成员角色

**位置**: 第 382-450 行

```python
def get_project_member_roles(self, project_id: int) -> List[Dict]:
    """获取项目所有成员的角色"""
    
    # 1. 调用 Redmine API 获取项目成员信息
    resp = requests.get(
        f"{self.base_url}/projects/{project_id}.json",
        headers=self.headers,
        params={"include": "memberships"},
        timeout=30
    )
    
    # 2. 解析 memberships 数据
    memberships = project.get('memberships', [])
    
    for membership in memberships:
        user = membership.get('user', {})
        user_id = user.get('id')
        member_roles = membership.get('roles', [])
        
        # 3. 确定最高优先级角色
        for role in member_roles:
            role_name = role.get('name', '')
            category = self._get_role_category(role_name)
            priority = self._get_role_priority(category)
            
            if priority < highest_priority:
                highest_priority = priority
                highest_role = role
                highest_category = category
```

**角色映射逻辑**:

```python
# 第 30-50 行：角色类别映射
ROLE_CATEGORY_MAP = {
    # 管理角色
    'project manager': 'manager',
    'manager': 'manager',
    '负责人': 'manager',
    '项目经理': 'manager',
    
    # 实施角色
    'implementation': 'implementation',
    '实施': 'implementation',
    
    # 开发角色
    'developer': 'developer',
    '开发': 'developer',
    'engineer': 'developer',
    
    # 测试角色
    'tester': 'tester',
    '测试': 'tester',
    'qa': 'tester',
}

# 第 52-59 行：角色优先级
ROLE_PRIORITY = {
    'manager': 1,        # 最高优先级
    'implementation': 2,
    'developer': 3,
    'tester': 4,
    'other': 5,          # 最低优先级
}
```

### 2.2 实际工作分析（基于 Journals）

**位置**: 第 299-380 行 `extract_contributors_from_journals()`

```python
def extract_contributors_from_journals(self, journals, issue_id, project_id):
    """从 Journals 提取贡献者信息"""
    
    # 1. 遍历所有 Journals
    for journal in journals:
        user_id = journal['user']['id']
        user_name = journal['user']['name']
        
        # 2. 统计每个用户的操作
        details = journal.get('details', [])
        for detail in details:
            if detail.get('name') == 'status_id':
                contrib['status_change_count'] += 1
            elif detail.get('name') == 'notes':
                contrib['note_count'] += 1
        
        # 3. 获取用户在项目中的角色定义
        role_info = user_role_map.get(user_id, {})
        
        # 4. 结合角色定义和实际操作
        if role_info:
            contrib['role_category'] = role_info.get('role_category')
        else:
            # 回退：基于团队分类
            if self.is_developer(user_name):
                contrib['role_category'] = 'developer'
            else:
                contrib['role_category'] = 'implementation'
```

### 2.3 角色判断逻辑

**关键判断**:

| 判断依据 | 角色 | 说明 |
|----------|------|------|
| `new_value = '3'` | 开发人员 | 将状态改为"已解决" |
| `new_value = '5'` | 测试人员 | 将状态改为"已关闭" |
| `old_value = '1' AND new_value = '2'` | 实施人员 | 将状态从"新建"改为"进行中" |
| Project Members 配置 | 定义角色 | 来自 Redmine 配置 |

**实际工作 vs 定义角色**:

- **定义角色**: 来自 Project Members 配置（`get_project_member_roles()`）
- **实际工作**: 来自 Journals 变更历史（`extract_contributors_from_journals()`）

**示例**: 曾聚 (ju.zeng)
- **定义角色**: 开发人员（来自 Project Members）
- **实际工作**: 启动工作 20 次（新建→进行中）
- **说明**: 他是开发人员，但主要负责启动 Issue

---

## 三、使用示例

### 3.1 手动触发全量同步

```bash
# 通过 MCP 工具
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"trigger_full_sync","arguments":{"project_id":357}}}'
```

### 3.2 分析项目成员角色

```python
from dev_test_analyzer import DevTestAnalyzer

analyzer = DevTestAnalyzer()

# 获取项目成员角色
roles = analyzer.get_project_member_roles(project_id=357)
for role in roles:
    print(f"{role['user_name']}: {role['highest_role_name']} ({role['role_category']})")

# 分析 Issue 贡献者
contributors = analyzer.extract_contributors_from_journals(
    journals, issue_id=77816, project_id=357
)
```

---

## 四、相关文件

| 文件 | 功能 | 行号 |
|------|------|------|
| `redmine_scheduler.py` | 增量/全量同步 | 100-220 |
| `dev_test_analyzer.py` | 角色分析 | 299-450 |
| `redmine_handler.py` | MCP 工具调用 | 2486 |

---

**维护者**: OpenJaw  
**项目**: Redmine MCP Server  
**文档位置**: `/docker/redmine-mcp-server/docs/KEY_FEATURES_LOCATION.md`
