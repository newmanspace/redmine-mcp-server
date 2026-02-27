# Unit Tests - 单元测试

这个目录包含单元测试，测试单个函数或方法，**不需要外部依赖**。

## 测试文件

| 文件 | 测试内容 |
|------|----------|
| `test_file_manager.py` | AttachmentFileManager 文件管理 |
| `test_cleanup_manager.py` | CleanupTaskManager 清理任务管理 |
| `test_error_handling.py` | 错误处理逻辑 |
| `test_issue_to_dict_selective.py` | Issue 数据转换选择性字段 |

## 运行单元测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定测试文件
pytest tests/unit/test_file_manager.py -v

# 运行特定测试函数
pytest tests/unit/test_file_manager.py::test_cleanup_expired_files -v

# 生成覆盖率报告
pytest tests/unit/ --cov=src/redmine_mcp_server/core --cov-report=html
```

## 测试特点

- ✅ **无外部依赖** - 使用 mock 对象
- ✅ **快速执行** - 每个测试 < 1 秒
- ✅ **独立运行** - 测试之间无依赖
- ✅ **可重复** - 结果一致，无副作用

## Mock 使用示例

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_with_mock():
    """使用 mock 测试"""
    # 创建 mock 对象
    mock_redmine = Mock()
    mock_redmine.issue.get.return_value = {'id': 1, 'subject': 'Test'}
    
    # 注入 mock
    with patch('module.Redmine', return_value=mock_redmine):
        # 测试代码
        result = some_function()
        assert result == expected

@pytest.mark.unit
def test_with_patch():
    """使用 patch 装饰器"""
    @patch('module.requests.get')
    def test_api_call(mock_get):
        mock_get.return_value.json.return_value = {'data': []}
        # 测试代码
```

## 测试覆盖率目标

- **目标覆盖率**: 80%
- **核心模块**: 90%+
- **边界条件**: 覆盖所有异常处理路径

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
