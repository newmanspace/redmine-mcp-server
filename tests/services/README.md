# Services Tests - 服务层测试

这个目录包含业务服务层的测试。

## 测试文件

### 待添加的测试

1. **test_subscription_service.py** - 订阅管理服务测试
2. **test_email_service.py** - 邮件服务测试
3. **test_report_generation_service.py** - 报告生成服务测试
4. **test_trend_analysis_service.py** - 趋势分析服务测试
5. **test_subscription_push_service.py** - 订阅推送服务测试

## 运行服务测试

```bash
# 运行所有服务测试
pytest tests/services/ -v

# 运行特定测试
pytest tests/services/test_email_service.py -v

# 运行并生成覆盖率
pytest tests/services/ --cov=src/redmine_mcp_server/dws/services
```

## 测试示例

### 邮件服务测试示例

```python
# test_email_service.py
import pytest
from src.redmine_mcp_server.dws.services.email_service import EmailPushService

@pytest.mark.unit
def test_email_service_initialization():
    """测试邮件服务初始化"""
    service = EmailPushService()
    assert service is not None

@pytest.mark.unit
def test_send_email(monkeypatch):
    """测试邮件发送（使用 mock）"""
    # Mock SMTP
    def mock_sendmail(*args, **kwargs):
        return True
    
    monkeypatch.setattr("smtplib.SMTP.sendmail", mock_sendmail)
    
    service = EmailPushService()
    result = service.send_email(
        to_email="test@example.com",
        subject="Test",
        body="Test body"
    )
    
    assert result.get('success') == True
```

### 报告生成服务测试示例

```python
# test_report_generation_service.py
import pytest
from src.redmine_mcp_server.dws.services.report_generation_service import ReportGenerationService

@pytest.mark.integration
def test_generate_daily_report():
    """测试日报生成（需要 Redmine 连接）"""
    service = ReportGenerationService()
    report = service.generate_daily_report(
        project_id=341,
        level="detailed",
        include_trend=True
    )
    
    assert report is not None
    assert 'stats' in report
    assert 'type' in report
    assert report['type'] == 'daily'
```

## 测试数据

测试数据放在 `tests/fixtures/` 目录：
- `fixtures/sample_issues.json` - 示例 Issue 数据
- `fixtures/sample_report.json` - 示例报告数据

## Mock 对象

使用 pytest 的 monkeypatch 进行 Mock：

```python
def test_with_mock(monkeypatch):
    # Mock Redmine API
    def mock_redmine_get(*args, **kwargs):
        return {'issues': []}
    
    monkeypatch.setattr("requests.get", mock_redmine_get)
    
    # 测试代码...
```

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
