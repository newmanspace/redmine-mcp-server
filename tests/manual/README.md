# Manual Tests - 手动测试脚本

这个目录包含独立测试脚本，用于快速验证功能，**不参与自动测试**。

## 测试脚本说明

### 1. test_quick.py
**用途**: 快速测试 MCP 服务器基本功能

**运行方式**:
```bash
cd /docker/redmine-mcp-server
python tests/manual/test_quick.py
```

**测试内容**:
- MCP 工具注册
- 基本工具调用

---

### 2. test_quick_mock.py
**用途**: 使用 mock 数据测试，不需要真实 Redmine 连接

**运行方式**:
```bash
python tests/manual/test_quick_mock.py
```

**测试内容**:
- Mock 环境下的工具调用
- 响应格式验证

---

### 3. test_send_email.py
**用途**: 测试邮件发送功能（使用模拟数据）

**运行方式**:
```bash
python tests/manual/test_send_email.py
```

**测试内容**:
- SMTP 连接
- HTML 邮件生成
- 邮件发送

**前置条件**:
- 配置 `.env` 或 `.env.docker` 中的 SMTP 设置

---

### 4. test_real_data_email.py
**用途**: 使用真实 Redmine 数据生成并发送项目日报

**运行方式**:
```bash
python tests/manual/test_real_data_email.py
```

**测试内容**:
- Redmine API 连接
- 真实项目数据获取
- 统计数据计算
- 邮件发送

**前置条件**:
- 配置 `.env.docker` 中的 Redmine 和 SMTP 设置
- Redmine 服务器可访问

**输出示例**:
```
======================================================================
测试发送真实的江苏新顺 CIM 项目日报
======================================================================

Redmine URL: http://redmine.fa-software.com
Project ID: 341
SMTP Server: smtp.qiye.aliyun.com
Sender: jenkins@fa-software.com

正在统计项目数据...
  Issue 总数：540
  未关闭：162
  已关闭：378
  今日新增：9
  今日关闭：8

正在生成邮件内容...
正在发送邮件到：jenkins@fa-software.com
主题：[Redmine] 江苏新顺 CIM - 项目详细状态报告 (2026-02-27)

======================================================================
✅ 邮件发送成功!
======================================================================
```

---

### 5. test_subscription_push.py
**用途**: 测试订阅推送服务

**运行方式**:
```bash
python tests/manual/test_subscription_push.py
```

**测试内容**:
- 订阅推送服务初始化
- 项目统计数据获取
- 邮件报告生成和发送

**前置条件**:
- 配置 `.env.docker`
- 数据库中有订阅记录

---

## 快速测试所有手动测试

```bash
cd /docker/redmine-mcp-server/tests/manual

# 运行所有测试
for test in test_*.py; do
    echo "Running $test..."
    python "$test"
    echo ""
done
```

---

## 与自动测试的区别

| 特性 | 手动测试 | 自动测试 |
|------|----------|----------|
| 位置 | `tests/manual/` | `tests/unit/`, `tests/integration/` |
| 运行方式 | 手动执行 | pytest 自动运行 |
| 依赖 | 可能需要真实环境 | 单元测试无依赖，集成测试需要环境 |
| 用途 | 快速验证、调试 | 质量保证、CI/CD |
| 覆盖率 | 不计入 | 计入代码覆盖率 |

---

## 何时使用手动测试

1. **开发新功能时** - 快速验证功能是否工作
2. **调试问题时** - 隔离问题原因
3. **演示功能时** - 展示具体功能效果
4. **性能测试时** - 测试大数据量场景

---

## 注意事项

1. **不要将手动测试纳入 CI/CD** - 这些测试可能需要人工干预
2. **敏感信息** - 确保测试数据不包含真实密码等敏感信息
3. **清理工作** - 测试后清理生成的测试数据
4. **文档更新** - 如果测试脚本有变更，更新此 README

---

**维护者**: OpenJaw  
**最后更新**: 2026-02-27
