# Redmine MCP 数仓 - 数据库连接指南

**最后更新**: 2026-02-27  
**数据库**: PostgreSQL 15 Alpine

---

## 一、连接信息总览

| 项目 | 值 |
|------|-----|
| **主机（容器内）** | `warehouse-db` |
| **主机（宿主机）** | `localhost` 或 `127.0.0.1` |
| **端口** | `5432` |
| **数据库名** | `redmine_warehouse` |
| **用户名** | `redmine_warehouse` |
| **密码** | `WarehouseP@ss2026` |
| **Schema** | `warehouse` |

---

## 二、端口映射状态

### ✅ 当前状态：**已映射到宿主机**（2026-02-27 10:31 起）

数据库端口 **5432** 已映射到宿主机，可从外部访问。

```yaml
# docker-compose.yml 配置
services:
  warehouse-db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"  # 已添加端口映射
    networks:
      - mcp-network
```

**验证**:
```bash
$ docker port redmine-mcp-warehouse-db
5432/tcp -> 0.0.0.0:5432
5432/tcp -> [::]:5432
```

### 容器网络信息

- **网络名称**: `redmine-mcp-server_mcp-network`
- **网络类型**: bridge
- **容器 IP**:
  - `warehouse-db`: `172.20.0.2`
  - `redmine-mcp-server`: `172.20.0.3`

---

## 三、连接方式

### 3.1 从 MCP 服务器容器连接（推荐）

MCP 服务器通过 Docker 内部网络访问数据库：

```python
# 环境变量配置
WAREHOUSE_DB_HOST=warehouse-db
WAREHOUSE_DB_PORT=5432
WAREHOUSE_DB_NAME=redmine_warehouse
WAREHOUSE_DB_USER=redmine_warehouse
WAREHOUSE_DB_PASSWORD=WarehouseP@ss2026
```

```python
# Python 连接示例
import psycopg2

conn = psycopg2.connect(
    host="warehouse-db",
    port=5432,
    dbname="redmine_warehouse",
    user="redmine_warehouse",
    password="WarehouseP@ss2026"
)
```

### 3.2 从宿主机连接（需要端口映射）

#### 方式 A: 临时端口映射（推荐用于调试）

```bash
# 使用 docker exec 直接进入容器
docker exec -it redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse
```

#### 方式 B: 添加端口映射（永久）

修改 `docker-compose.yml`：

```yaml
services:
  warehouse-db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"  # 添加这行
    environment:
      POSTGRES_USER: redmine_warehouse
      POSTGRES_PASSWORD: WarehouseP@ss2026
      POSTGRES_DB: redmine_warehouse
```

然后重启：

```bash
cd /docker/redmine-mcp-server
docker compose up -d warehouse-db
```

连接命令：

```bash
# 使用 psql 连接
psql -h localhost -p 5432 -U redmine_warehouse -d redmine_warehouse

# 或使用 DSN
postgresql://redmine_warehouse:WarehouseP@ss2026@localhost:5432/redmine_warehouse
```

#### 方式 C: 使用 Docker 网络（无需端口映射）

```bash
# 从宿主机通过容器 IP 连接（需要安装 netcat 等工具）
# 不推荐，仅用于特殊场景
```

### 3.3 从其他容器连接

如果其他容器需要访问数仓，需加入同一网络：

```yaml
services:
  my-app:
    image: my-app:latest
    networks:
      - redmine-mcp-server_mcp-network  # 加入现有网络

networks:
  redmine-mcp-server_mcp-network:
    external: true
```

连接配置：

```python
host="warehouse-db"  # 使用服务名，不是容器名
port=5432
```

---

## 四、常用连接命令

### 4.1 使用 psql（容器内）

```bash
# 进入容器并连接
docker exec -it redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse

# 或直接执行 SQL
docker exec -it redmine-mcp-warehouse-db psql \
  -U redmine_warehouse -d redmine_warehouse \
  -c "SELECT * FROM warehouse.dwd_issue_daily_snapshot LIMIT 10;"
```

### 4.2 使用 psql（宿主机，需要端口映射）

```bash
# 连接数据库
psql -h localhost -p 5432 -U redmine_warehouse -d redmine_warehouse

# 列出所有表
\dt warehouse.*

# 查看表结构
\d warehouse.dwd_issue_daily_snapshot

# 查询数据
SELECT COUNT(*) FROM warehouse.dwd_issue_daily_snapshot;
```

### 4.3 使用 Python

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# 容器内连接
conn = psycopg2.connect(
    host="warehouse-db",
    port=5432,
    dbname="redmine_warehouse",
    user="redmine_warehouse",
    password="WarehouseP@ss2026",
    cursor_factory=RealDictCursor
)

# 宿主机连接（需要端口映射）
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="redmine_warehouse",
    user="redmine_warehouse",
    password="WarehouseP@ss2026",
    cursor_factory=RealDictCursor
)

cur = conn.cursor()
cur.execute("SELECT * FROM warehouse.dws_issue_contributors LIMIT 10;")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
```

### 4.4 使用 DBeaver / pgAdmin

**连接配置**:

| 字段 | 值（需要端口映射） |
|------|-------------------|
| Host | `localhost` |
| Port | `5432` |
| Database | `redmine_warehouse` |
| Username | `redmine_warehouse` |
| Password | `WarehouseP@ss2026` |

**JDBC URL**:
```
jdbc:postgresql://localhost:5432/redmine_warehouse
```

---

## 五、安全建议

### 5.1 生产环境配置

1. **不要暴露数据库端口**（当前配置是安全的）
2. **使用强密码**（当前密码应更换）
3. **限制网络访问**
   ```yaml
   networks:
     mcp-network:
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16
   ```
4. **启用 SSL**（可选）
   ```yaml
   environment:
     POSTGRES_SSL: require
   ```

### 5.2 开发环境便捷访问

临时开启端口映射：

```bash
# 方法 1: 使用 docker run 添加端口
docker run --rm -d \
  --network redmine-mcp-server_mcp-network \
  -p 5432:5432 \
  alpine/socat TCP-LISTEN:5432,fork TCP:warehouse-db:5432

# 方法 2: 修改 docker-compose.yml 后重启
```

---

## 六、故障排查

### 6.1 检查容器状态

```bash
# 查看容器是否运行
docker ps | grep warehouse-db

# 查看容器日志
docker logs redmine-mcp-warehouse-db

# 检查健康状态
docker inspect redmine-mcp-warehouse-db | grep -A 5 '"Health"'
```

### 6.2 测试数据库连接

```bash
# 从 MCP 服务器容器测试
docker exec redmine-mcp-server python -c "
import psycopg2
conn = psycopg2.connect(
    host='warehouse-db',
    port=5432,
    dbname='redmine_warehouse',
    user='redmine_warehouse',
    password='WarehouseP@ss2026'
)
print('Connection successful!')
conn.close()
"
```

### 6.3 常见问题

**问题 1**: `could not translate host name "warehouse-db" to address`

**解决**: 确保容器在同一网络
```bash
docker network inspect redmine-mcp-server_mcp-network
```

**问题 2**: `no pg_hba.conf entry for host`

**解决**: 检查 PostgreSQL 配置，允许对应网段连接

**问题 3**: 端口映射后仍无法连接

**解决**: 检查防火墙
```bash
sudo ufw allow 5432/tcp
```

---

## 七、快速参考

### 连接字符串

```
# 容器内
postgresql://redmine_warehouse:WarehouseP@ss2026@warehouse-db:5432/redmine_warehouse

# 宿主机（需要端口映射）
postgresql://redmine_warehouse:WarehouseP@ss2026@localhost:5432/redmine_warehouse
```

### 关键命令

```bash
# 进入数据库
docker exec -it redmine-mcp-warehouse-db psql -U redmine_warehouse -d redmine_warehouse

# 查看表
\dt warehouse.*

# 查看表结构
\d warehouse.dwd_issue_daily_snapshot

# 退出
\q
```

### 环境变量

```bash
# .env.docker
WAREHOUSE_DB_HOST=warehouse-db
WAREHOUSE_DB_PORT=5432
WAREHOUSE_DB_NAME=redmine_warehouse
WAREHOUSE_DB_USER=redmine_warehouse
WAREHOUSE_DB_PASSWORD=WarehouseP@ss2026
```

---

**维护者**: OpenJaw <openjaw@gmail.com>  
**项目**: `/docker/redmine-mcp-server/`
