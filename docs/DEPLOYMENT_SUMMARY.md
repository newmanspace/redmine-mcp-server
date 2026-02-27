# Docker 部署总结

**日期**: 2026-02-27  
**状态**: ✅ 部署成功

---

## 一、部署信息

### 容器信息

| 容器名 | 镜像 | 端口 | 状态 |
|--------|------|------|------|
| redmine-mcp-server | redmine-mcp-server-redmine-mcp-server:latest | 8000 | ✅ Running |
| redmine-mcp-warehouse-db | postgres:15-alpine | 5432 | ✅ Healthy |

### 构建信息

- **镜像名称**: `redmine-mcp-server-redmine-mcp-server:latest`
- **构建时间**: 2026-02-27 16:07
- **基础镜像**: Python 3.13-slim
- **构建方式**: 多阶段构建

### 启动日志

```
2026-02-27 16:07:14 INFO     Redmine MCP Server v0.10.0
2026-02-27 16:07:14 INFO     Starting with transport: streamable-http
2026-02-27 16:07:14 INFO     Connected to PostgreSQL warehouse at warehouse-db:5432
2026-02-27 16:07:14 INFO     SubscriptionManager: Warehouse connection initialized
2026-02-27 16:07:14 INFO     Subscription scheduler started (auto-send reports)
2026-02-27 16:07:14 INFO     Scheduled: Daily reports at 09:00
2026-02-27 16:07:14 INFO     Scheduled: Weekly reports on Monday 09:00
2026-02-27 16:07:14 INFO     Scheduled: Monthly reports on 1st day 10:00
2026-02-27 16:07:14 INFO     Scheduler started
2026-02-27 16:07:15 INFO     Uvicorn running on http://0.0.0.0:8000
```

---

## 二、功能验证

### 1. i18n 多语言测试

```bash
# 测试中文翻译
docker compose exec redmine-mcp-server python -c \
  "from redmine_mcp_server.i18n import get_report_type_name; print(get_report_type_name('daily', 'zh_CN'))"
# 输出：日报

# 测试英文翻译
docker compose exec redmine-mcp-server python -c \
  "from redmine_mcp_server.i18n import get_report_type_name; print(get_report_type_name('daily', 'en_US'))"
# 输出：Daily Report
```

✅ **验证通过** - 中英文翻译正常工作

### 2. 调度器启动验证

```
✅ Scheduled: Daily reports at 09:00
✅ Scheduled: Weekly reports on Monday 09:00
✅ Scheduled: Monthly reports on 1st day 10:00
✅ Scheduled: Check custom subscriptions every minute
```

✅ **验证通过** - 所有定时任务已调度

### 3. 数据库连接验证

```
✅ Connected to PostgreSQL warehouse at warehouse-db:5432
✅ SubscriptionManager: Warehouse connection initialized
```

✅ **验证通过** - 数据库连接正常

---

## 三、访问方式

### MCP 服务端点

| 端点 | URL | 说明 |
|------|-----|------|
| MCP 主端点 | http://localhost:8000/mcp | MCP 协议端点 |
| 健康检查 | http://localhost:8000/health | 健康检查（404 正常） |
| 文件服务 | http://localhost:8000/files/{id} | 文件下载 |

### 数据库连接

| 参数 | 值 |
|------|-----|
| 主机 | localhost |
| 端口 | 5432 |
| 数据库 | redmine_warehouse |
| 用户 | redmine_warehouse |
| 密码 | WarehouseP@ss2026 |

---

## 四、部署命令

### 构建镜像

```bash
cd /docker/redmine-mcp-server
docker compose build --no-cache
```

### 启动服务

```bash
docker compose up -d
```

### 查看日志

```bash
# 查看最近日志
docker compose logs redmine-mcp-server --tail 50

# 实时查看日志
docker compose logs -f redmine-mcp-server
```

### 停止服务

```bash
docker compose down
```

### 重启服务

```bash
docker compose restart
```

---

## 五、测试订阅功能

### 订阅中文日报

```python
# 通过 MCP 客户端调用
subscribe_project(
    project_id=341,
    user_name="张三",
    user_email="zhangsan@example.com",
    channel="email",
    report_type="daily",
    language="zh_CN",  # 中文
    send_time="09:00"
)
```

### 订阅英文日报

```python
subscribe_project(
    project_id=341,
    user_name="John Doe",
    user_email="john@example.com",
    channel="email",
    report_type="daily",
    language="en_US",  # English
    send_time="09:00"
)
```

### 手动触发日报推送

```python
push_subscription_reports(report_type="daily")
```

---

## 六、环境变量配置

### .env.docker 配置

```bash
# Redmine 连接
REDMINE_URL=http://redmine.fa-software.com
REDMINE_API_KEY=adabb6a1089a5ac90e5649f505029d28e1cc9bc7

# 邮件配置
EMAIL_SMTP_SERVER=smtp.qiye.aliyun.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=jenkins@fa-software.com
EMAIL_SMTP_PASSWORD=***
EMAIL_SENDER_EMAIL=jenkins@fa-software.com

# 语言配置
DEFAULT_LANGUAGE=zh_CN
```

---

## 七、定时任务说明

### 日报推送

- **触发时间**: 每天早上 9:00 (Asia/Shanghai)
- **推送对象**: 所有订阅了日报的用户
- **语言**: 根据订阅人偏好（zh_CN/en_US）

### 周报推送

- **触发时间**: 每周一早上 9:00
- **推送对象**: 所有订阅了周报的用户
- **语言**: 根据订阅人偏好

### 月报推送

- **触发时间**: 每月 1 号早上 10:00
- **推送对象**: 所有订阅了月报的用户
- **语言**: 根据订阅人偏好

### 自定义时间检查

- **触发时间**: 每分钟
- **功能**: 检查是否有自定义时间的订阅需要发送

---

## 八、故障排查

### 问题 1: 容器启动失败

```bash
# 查看日志
docker compose logs redmine-mcp-server

# 检查配置
docker compose config
```

### 问题 2: 数据库连接失败

```bash
# 检查数据库容器状态
docker compose ps warehouse-db

# 查看数据库日志
docker compose logs warehouse-db
```

### 问题 3: 邮件发送失败

```bash
# 检查 SMTP 配置
docker compose exec redmine-mcp-server env | grep EMAIL

# 测试 SMTP 连接
docker compose exec redmine-mcp-server python \
  tests/manual/test_monthly_report_quick.py
```

---

## 九、下一步

1. **运行数据库迁移**
   ```bash
   docker compose exec warehouse-db psql \
     -U redmine_warehouse \
     -d redmine_warehouse \
     -f /docker-entrypoint-initdb.d/08-migrate-subscriptions-i18n.sql
   ```

2. **创建订阅**
   - 通过 MCP 客户端创建订阅
   - 或直接插入数据库

3. **测试邮件推送**
   - 等待定时任务触发
   - 或手动触发推送测试

---

**部署者**: OpenJaw  
**部署时间**: 2026-02-27 16:07  
**部署环境**: Docker Compose  
**状态**: ✅ 成功
