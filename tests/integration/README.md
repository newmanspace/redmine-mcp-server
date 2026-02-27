# Integration Tests - 集成测试

这个目录包含集成测试，测试组件间的交互，**需要外部依赖**（Redmine、数据库）。

## 测试文件

| 文件 | 测试内容 |
|------|----------|
| `test_integration.py` | 综合集成测试 |
| `test_redmine_handler.py` | Redmine 处理器 |
| `test_warehouse.py` | 数据仓库写入 |
| `test_warehouse_read.py` | 数据仓库读取 |
| `test_wiki_editing.py` | Wiki 编辑功能 |
| `test_connection.py` | 连接测试 |
| `test_scheduler.py` | 调度器测试 |
| `test_http_endpoints.py` | HTTP 端点测试 |
| `test_global_search.py` | 全局搜索功能 |
| `test_search_*.py` | 搜索功能相关测试 |
| `test_ssl_*.py` | SSL 配置测试 |
| `test_security_*.py` | 安全验证测试 |
| `test_env_loading.py` | 环境加载测试 |
| `test_main.py` | 主入口测试 |

## 运行集成测试

```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/integration/test_redmine_handler.py -v

# 跳过慢速测试
pytest tests/integration/ -v -m "not slow"

# 仅运行标记为集成的测试
pytest tests/integration/ -v -m integration
```

## 前置条件

运行集成测试前需要：

1. **Redmine 服务器** - 可访问的 Redmine 实例
2. **PostgreSQL 数据库** - 数据仓库数据库
3. **环境配置** - 正确的 `.env` 或 `.env.test` 配置

### 测试环境配置

```bash
# tests/.env.test
REDMINE_URL=http://test-redmine.com
REDMINE_API_KEY=test_api_key

WAREHOUSE_DB_HOST=localhost
WAREHOUSE_DB_PORT=5432
WAREHOUSE_DB_NAME=redmine_warehouse_test
WAREHOUSE_DB_USER=test_user
WAREHOUSE_DB_PASSWORD=test_password
```

## 使用 pytest fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def redmine_client():
    """创建 Redmine 客户端 fixture"""
    client = Redmine(TEST_URL, api_key=TEST_KEY)
    yield client
    client.close()

@pytest.fixture
def warehouse_db():
    """创建数据库连接 fixture"""
    db = DataWarehouse()
    yield db
    db.close()

# 测试中使用
@pytest.mark.integration
def test_with_fixtures(redmine_client, warehouse_db):
    # 测试代码
```

## 测试数据清理

集成测试可能修改数据，需要清理：

```python
@pytest.fixture
def cleanup_after_test():
    """测试后清理 fixture"""
    yield
    # 清理代码
    cleanup_test_data()

@pytest.mark.integration
def test_with_cleanup(cleanup_after_test):
    # 测试会自动清理
```

## 跳过测试

如果环境不满足，跳过测试：

```python
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('REDMINE_URL'),
    reason="Requires Redmine connection"
)
def test_integration():
    pass
```

## 超时设置

防止测试卡住：

```python
@pytest.mark.integration
@pytest.mark.timeout(30)  # 30 秒超时
def test_slow_operation():
    pass
```

## CI/CD 中的集成测试

```yaml
# .github/workflows/tests.yml
- name: Run integration tests
  env:
    REDMINE_URL: ${{ secrets.TEST_REDMINE_URL }}
    REDMINE_API_KEY: ${{ secrets.TEST_REDMINE_API_KEY }}
  run: |
    pytest tests/integration/ -v -m "not slow"
```

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
