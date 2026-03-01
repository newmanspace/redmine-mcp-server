# ISSUE-003 - 订阅推送连接池 Bug

**创建日期**: 2026-02-28  
**严重性**: 🔴 高  
**状态**: ✅ 已修复  
**影响范围**: 订阅推送、订阅列表查询

---

## 问题描述

创建订阅后，推送报告时提示连接池已关闭。

**错误信息**:
```
Error executing tool push_subscription_reports: connection pool is closed
```

**现象**:
- ✅ 创建订阅成功
- ❌ 推送报告失败
- ❌ 查询订阅列表失败

---

## 根因分析

**问题文件**: 
- `src/redmine_mcp_server/dws/services/subscription_service.py`
- `src/redmine_mcp_server/mcp/tools/subscription_tools.py`
- `src/redmine_mcp_server/mcp/tools/subscription_push_tools.py`

**核心问题**: 全局单例 + 连接池过早关闭

```python
# 1. 全局单例
subscription_manager: Optional[SubscriptionManager] = None

def get_subscription_manager() -> SubscriptionManager:
    global subscription_manager
    if subscription_manager is None:
        subscription_manager = SubscriptionManager()
    return subscription_manager  # ← 总是返回同一个实例

# 2. 订阅工具中关闭连接
async def subscribe_project(...):
    manager = get_subscription_manager()
    result = manager.subscribe(...)
    manager.close()  # ← 关闭了数据库连接池
    return result

# 3. 推送工具中再次使用
async def push_subscription_reports(...):
    manager = get_subscription_manager()  # ← 返回同一个已关闭连接的实例
    all_subs = manager.list_all_subscriptions()  # ← 报错：connection pool is closed
```

---

## 解决方案

### 方案一：关闭后重置单例（推荐）⭐

**修改文件**: `src/redmine_mcp_server/dws/services/subscription_service.py`

**修改位置**: `SubscriptionManager.close()` 方法（约第 428-433 行）

```python
def close(self):
    """Close warehouse connection"""
    if self.warehouse:
        self.warehouse.close()
        logger.info("SubscriptionManager: Warehouse connection closed")
    
    # ✅ 新增：重置全局单例，下次获取时重新创建
    global subscription_manager
    subscription_manager = None
```

**优点**:
- ✅ 最小改动（只加 2 行）
- ✅ 每次获取都是新连接
- ✅ 不影响其他功能

### 方案二：工具层不关闭连接

**修改文件**: 
- `src/redmine_mcp_server/mcp/tools/subscription_tools.py` (第 377 行)
- `src/redmine_mcp_server/mcp/tools/subscription_push_tools.py` (第 62 行)

```python
# 删除或注释掉这行
# manager.close()
```

**优点**: 连接复用，性能更好  
**缺点**: 连接可能长期占用

---

## 修复命令

```bash
cd /docker/redmine-mcp-server

# 方案一：修改 subscription_service.py
sed -i '/logger.info("SubscriptionManager: Warehouse connection closed")/a\
\    # 重置全局单例\
\    global subscription_manager\
\    subscription_manager = None' src/redmine_mcp_server/dws/services/subscription_service.py

# 重新构建并重启
docker compose build redmine-mcp-server
docker compose restart redmine-mcp-server
```

---

## 验证步骤

```bash
# 1. 创建订阅
curl -X POST http://localhost:8000/mcp ... subscribe_project ...

# 2. 推送报告
curl -X POST http://localhost:8000/mcp ... push_subscription_reports ...

# 3. 查询订阅列表
curl -X POST http://localhost:8000/mcp ... list_my_subscriptions ...
```

所有操作都应成功，无 `connection pool is closed` 错误。

---

## 如何避免

### 1. 单例模式最佳实践

```python
# 使用上下文管理器
class SubscriptionManager:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# 使用方式
async def subscribe_project(...):
    with get_subscription_manager() as manager:
        result = manager.subscribe(...)
    # 自动关闭
```

### 2. 依赖注入

```python
# 使用 FastAPI 依赖注入
from fastapi import Depends

def get_subscription_manager():
    manager = SubscriptionManager()
    try:
        yield manager
    finally:
        manager.close()

@app.post("/subscribe")
async def subscribe(manager: SubscriptionManager = Depends(get_subscription_manager)):
    ...
```

### 3. 连接池管理中间件

```python
# 创建连接池管理类
class ConnectionPool:
    def __init__(self, max_connections=10):
        self.pool = Queue(max_connections)
    
    def get_connection(self):
        if self.pool.empty():
            return create_new_connection()
        return self.pool.get()
    
    def release_connection(self, conn):
        self.pool.put(conn)
```

### 4. 代码审查清单

在 PR/MR 中添加检查项：
- [ ] 单例对象的生命周期管理正确
- [ ] 连接池关闭后不会再次使用
- [ ] 有适当的错误处理和日志记录

---

## 相关文件

- 修复文件：`src/redmine_mcp_server/dws/services/subscription_service.py`
- 相关文件：`src/redmine_mcp_server/mcp/tools/subscription_tools.py`
- 相关文件：`src/redmine_mcp_server/mcp/tools/subscription_push_tools.py`

---

**修复人**: qwen-code  
**修复日期**: 2026-02-28  
**验证人**: Jaw
