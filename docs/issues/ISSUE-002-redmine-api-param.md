# ISSUE-002 - Redmine API 参数名错误

**创建日期**: 2026-02-28  
**严重性**: 🔴 高  
**状态**: ✅ 已修复  
**影响范围**: 所有 Redmine API 调用

---

## 问题描述

Redmine 客户端初始化时使用了错误的参数名，导致认证失败。

**错误信息**:
```
Authentication failed. Please check your credentials: 
1) REDMINE_API_KEY is valid, or 2) REDMINE_USERNAME and REDMINE_PASSWORD are correct
```

---

## 根因分析

**问题文件**: `src/redmine_mcp_server/mcp/server.py` (第 26 行)

**错误代码**:
```python
redmine = Redmine(REDMINE_URL, api_key=REDMINE_API_KEY)
```

**正确代码**:
```python
redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
```

**原因**:
- `python-redmine` 库使用 `key` 参数，不是 `api_key`
- 开发者可能混淆了不同库的参数命名
- 缺少单元测试覆盖此初始化代码

---

## 解决方案

**修复命令**:
```bash
cd /docker/redmine-mcp-server
sed -i 's/api_key=REDMINE_API_KEY/key=REDMINE_API_KEY/' src/redmine_mcp_server/mcp/server.py
docker compose build redmine-mcp-server
docker compose restart redmine-mcp-server
```

**验证**:
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_redmine_projects","arguments":{}}}'
```

预期返回项目列表，而非认证错误。

---

## 如何避免

### 1. 添加初始化测试

```python
# tests/test_redmine_client.py
def test_redmine_client_initialization():
    """测试 Redmine 客户端正确初始化"""
    from redminelib import Redmine
    import os
    
    redmine = Redmine(os.getenv("REDMINE_URL"), key=os.getenv("REDMINE_API_KEY"))
    
    # 测试连接
    user = redmine.user.get('current')
    assert user is not None
    assert user.login is not None
```

### 2. 文档化 API 使用规范

在 `CONTRIBUTING.md` 中添加：
```markdown
## Redmine API 使用规范

- 使用 `key` 参数传递 API Key
- 使用 `username` 和 `password` 传递用户名密码
- 参考：https://python-redmine.com/
```

### 3. 使用类型检查和自动补全

在 IDE 中配置 `python-redmine` 的类型 stub：
```bash
pip install types-python-redmine
```

### 4. 启动时自检

```python
# 在 server.py 中添加
def verify_redmine_connection():
    """验证 Redmine 连接"""
    try:
        user = redmine.user.get('current')
        logger.info(f"Connected as {user.login}")
        return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False
```

---

## 相关文件

- 修复文件：`src/redmine_mcp_server/mcp/server.py`
- 库文档：https://python-redmine.com/

---

**修复人**: qwen-code  
**修复日期**: 2026-02-28  
**验证人**: Jaw
