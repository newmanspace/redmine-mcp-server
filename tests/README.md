# Tests Directory Structure

## 目录结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest 配置和共享 fixtures
├── run_tests.py             # 测试运行脚本
├── .env.test                # 测试环境变量
│
├── fixtures/                # 测试数据和 fixtures
│   └── ...
│
├── unit/                    # 单元测试
│   ├── test_file_manager.py
│   ├── test_cleanup_manager.py
│   ├── test_error_handling.py
│   ├── test_issue_to_dict_selective.py
│   └── ...
│
├── integration/             # 集成测试
│   ├── test_integration.py
│   ├── test_redmine_handler.py
│   ├── test_warehouse.py
│   └── ...
│
├── services/                # 服务测试（新增）
│   ├── test_subscription_service.py
│   ├── test_email_service.py
│   ├── test_report_generation_service.py
│   └── test_trend_analysis_service.py
│
└── manual/                  # 手动测试脚本（不自动运行）
    ├── test_quick.py
    ├── test_quick_mock.py
    ├── test_send_email.py
    ├── test_real_data_email.py
    └── test_subscription_push.py
```

## 测试分类

### Unit Tests (单元测试)

测试单个函数或方法，不需要外部依赖。

**运行命令**:
```bash
pytest tests/unit/ -v
```

### Integration Tests (集成测试)

测试组件间的交互，需要 Redmine 和数据库连接。

**运行命令**:
```bash
pytest tests/integration/ -v
```

### Service Tests (服务测试)

测试业务服务层，需要数据库连接。

**运行命令**:
```bash
pytest tests/services/ -v
```

### Manual Tests (手动测试)

独立测试脚本，用于快速验证功能，不参与自动测试。

**运行方式**:
```bash
# 快速测试
python tests/manual/test_quick.py

# 邮件发送测试
python tests/manual/test_send_email.py

# 真实数据测试
python tests/manual/test_real_data_email.py

# 订阅推送测试
python tests/manual/test_subscription_push.py
```

## 运行所有测试

```bash
# 运行所有自动测试（不包括 manual）
pytest tests/ -v --ignore=tests/manual/

# 运行测试并生成覆盖率报告
pytest tests/ -v --ignore=tests/manual/ --cov=src/redmine_mcp_server --cov-report=html

# 运行特定测试文件
pytest tests/unit/test_file_manager.py -v

# 运行特定测试函数
pytest tests/unit/test_file_manager.py::test_cleanup_expired_files -v
```

## 测试文件命名规范

- 单元测试：`test_<module>_<function>.py`
- 集成测试：`test_<component>_integration.py`
- 服务测试：`test_<service>_service.py`
- 手动测试：`test_<feature>.py`

## 测试标记

使用 pytest markers 标记测试：

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
def test_something_else():
    pass

@pytest.mark.slow
def test_slow_test():
    pass
```

运行特定标记的测试：
```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## 测试数据

测试数据放在 `tests/fixtures/` 目录：
- JSON 文件：测试数据
- SQL 文件：数据库初始化脚本
- 配置文件：测试专用配置

## 环境变量

测试环境变量在 `tests/.env.test` 中配置：
```bash
# 测试数据库
WAREHOUSE_DB_HOST=localhost
WAREHOUSE_DB_PORT=5432
WAREHOUSE_DB_NAME=redmine_warehouse_test

# 测试 Redmine
REDMINE_URL=http://test-redmine.com
REDMINE_API_KEY=test_api_key

# 测试 SMTP
EMAIL_SMTP_SERVER=smtp.test.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=test@test.com
EMAIL_SMTP_PASSWORD=test_password
```

## CI/CD 集成

GitHub Actions 自动运行所有单元测试和部分集成测试：

```yaml
- name: Run tests
  run: |
    pytest tests/unit/ -v
    pytest tests/integration/ -v -k "not slow"
```

## 代码覆盖率

生成覆盖率报告：
```bash
pytest tests/ --ignore=tests/manual/ --cov=src/redmine_mcp_server --cov-report=html
```

查看覆盖率报告：
```bash
open htmlcov/index.html
```

目标覆盖率：**80%**

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
