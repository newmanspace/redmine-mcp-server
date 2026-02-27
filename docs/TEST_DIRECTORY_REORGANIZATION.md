# 测试目录整理总结

**日期**: 2026-02-27  
**状态**: ✅ 已完成

---

## 整理后的目录结构

```
tests/
├── README.md                    # 测试目录总览
├── __init__.py
├── conftest.py                  # pytest 配置和共享 fixtures
├── run_tests.py                 # 测试运行脚本
├── .env.test                    # 测试环境变量
│
├── fixtures/                    # 测试数据
│   └── ...
│
├── unit/                        # 单元测试 (4 个文件)
│   ├── README.md
│   ├── test_file_manager.py
│   ├── test_cleanup_manager.py
│   ├── test_error_handling.py
│   └── test_issue_to_dict_selective.py
│
├── integration/                 # 集成测试 (16 个文件)
│   ├── README.md
│   ├── test_integration.py
│   ├── test_redmine_handler.py
│   ├── test_warehouse.py
│   ├── test_warehouse_read.py
│   ├── test_wiki_editing.py
│   ├── test_connection.py
│   ├── test_scheduler.py
│   ├── test_http_endpoints.py
│   ├── test_env_loading.py
│   ├── test_main.py
│   ├── test_global_search.py
│   ├── test_search_field_selection.py
│   ├── test_search_native_filters.py
│   ├── test_search_pagination.py
│   ├── test_security_validation.py
│   ├── test_ssl_configuration.py
│   └── test_ssl_integration.py
│
├── services/                    # 服务测试 (待添加)
│   ├── README.md
│   ├── test_subscription_service.py (TODO)
│   ├── test_email_service.py (TODO)
│   ├── test_report_generation_service.py (TODO)
│   └── test_trend_analysis_service.py (TODO)
│
└── manual/                      # 手动测试 (5 个文件)
    ├── README.md
    ├── test_quick.py
    ├── test_quick_mock.py
    ├── test_send_email.py
    ├── test_real_data_email.py
    └── test_subscription_push.py
```

---

## 文件统计

| 目录 | 测试文件数 | 说明 |
|------|-----------|------|
| `unit/` | 4 | 单元测试，无外部依赖 |
| `integration/` | 16 | 集成测试，需要 Redmine 和数据库 |
| `services/` | 0 (待添加) | 服务层测试 |
| `manual/` | 5 | 手动测试脚本，不参与自动测试 |
| **总计** | **25** | |

---

## 运行测试

### 运行所有自动测试

```bash
# 运行所有测试（排除 manual）
pytest tests/ -v

# 运行并生成覆盖率报告
pytest tests/ --cov=src/redmine_mcp_server --cov-report=html
```

### 运行特定目录测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 服务测试（待添加）
pytest tests/services/ -v
```

### 运行手动测试

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

---

## 目录说明

### unit/ - 单元测试

**特点**:
- 无外部依赖
- 使用 mock 对象
- 快速执行 (< 1 秒/测试)
- 覆盖率目标：80%+

**测试内容**:
- 文件管理器
- 清理任务管理器
- 错误处理
- 数据转换

### integration/ - 集成测试

**特点**:
- 需要 Redmine 和数据库连接
- 测试组件间交互
- 执行时间较长
- 部分测试标记为 `@pytest.mark.slow`

**测试内容**:
- Redmine 处理器
- 数据仓库读写
- Wiki 编辑
- 搜索功能
- SSL 配置
- 安全验证
- HTTP 端点
- 调度器

### services/ - 服务测试（待添加）

**计划添加**:
- 订阅管理服务测试
- 邮件服务测试
- 报告生成服务测试
- 趋势分析服务测试
- 订阅推送服务测试

### manual/ - 手动测试

**特点**:
- 独立脚本
- 不参与自动测试
- 用于快速验证功能
- 可能需要人工干预

**测试内容**:
- 快速功能验证
- 邮件发送测试
- 真实数据测试
- 订阅推送测试

---

## 配置文件更新

### pytest.ini

```ini
[pytest]
minversion = 6.0
addopts = -ra -q --ignore=tests/manual
testpaths = tests
markers =
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    slow: marks tests as slow running
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function

# Exclude patterns
norecursedirs = tests/manual .* build dist *.egg
```

**关键变更**:
- `--ignore=tests/manual` - 排除手动测试
- `norecursedirs` - 不递归搜索 manual 目录

---

## 文档结构

每个测试目录都有 README.md 文档：

1. **tests/README.md** - 测试目录总览
2. **tests/unit/README.md** - 单元测试说明
3. **tests/integration/README.md** - 集成测试说明
4. **tests/services/README.md** - 服务测试说明
5. **tests/manual/README.md** - 手动测试说明

---

## 待办事项

### 1. 添加服务测试

```bash
# 创建测试文件
touch tests/services/test_subscription_service.py
touch tests/services/test_email_service.py
touch tests/services/test_report_generation_service.py
touch tests/services/test_trend_analysis_service.py
touch tests/services/test_subscription_push_service.py
```

### 2. 添加测试数据 fixtures

```bash
# 创建示例数据
touch tests/fixtures/sample_issues.json
touch tests/fixtures/sample_report.json
```

### 3. 更新 CI/CD 配置

确保 GitHub Actions 只运行自动测试：

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --ignore=tests/manual
```

---

## 最佳实践

### 测试文件命名

- 单元测试：`test_<module>_<function>.py`
- 集成测试：`test_<component>_integration.py`
- 服务测试：`test_<service>_service.py`
- 手动测试：`test_<feature>.py`

### 测试标记

```python
@pytest.mark.unit
def test_unit_test():
    pass

@pytest.mark.integration
def test_integration_test():
    pass

@pytest.mark.slow
def test_slow_test():
    pass
```

### 测试数据

- 小数据：直接放在测试文件中
- 大数据：放在 `tests/fixtures/` 目录
- 敏感数据：使用环境变量或加密存储

---

## 总结

✅ **已完成**:
- 移动所有测试文件到正确目录
- 创建目录结构和 README 文档
- 更新 pytest.ini 配置
- 排除手动测试从自动测试

✅ **改进**:
- 清晰的目录结构
- 完善的文档说明
- 明确的测试分类
- 易于维护和扩展

---

**维护者**: OpenJaw  
**整理日期**: 2026-02-27
