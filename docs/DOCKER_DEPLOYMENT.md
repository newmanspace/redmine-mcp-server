# Docker Deployment Guide / Docker 部署指南

**Version**: 2.0  
**Last Updated**: 2026-02-28  
**Status**: Production Ready

---

## 🚀 Quick Start / 快速开始

### Standard Deployment / 标准部署

```bash
cd /docker/redmine-mcp-server

# Run deployment script
./deploy.sh

# Or use docker compose directly
docker compose up -d
```

### Force Rebuild / 强制重新构建

```bash
cd /docker/redmine-mcp-server

# Using deployment script (Recommended)
./deploy.sh --force-rebuild

# Using docker compose
docker compose build --no-cache --force-rm redmine-mcp-server

# Complete clean rebuild
docker compose down --remove-orphans
docker builder prune -a -f
docker compose build --no-cache redmine-mcp-server
docker compose up -d
```

---

## 📋 Deployment Script Options / 部署脚本选项

### Available Options / 可用选项

| Option | Description | Chinese |
|--------|-------------|---------|
| `--build-only` | Build image only | 只构建镜像 |
| `--force-rebuild` | Force rebuild without cache | 强制重新构建（无缓存） |
| `--no-test` | Skip deployment testing | 跳过部署测试 |
| `--cleanup` | Stop and remove container | 停止并删除容器 |
| `--logs` | Show container logs | 显示容器日志 |
| `--status` | Show container status | 显示容器状态 |
| `--help` | Show help message | 显示帮助信息 |

### Usage Examples / 使用示例

```bash
# Full deployment (build + run + test)
./deploy.sh

# Force rebuild with no cache
./deploy.sh --force-rebuild

# Build image only
./deploy.sh --build-only

# Force rebuild and skip tests
./deploy.sh --force-rebuild --no-test

# Clean up existing deployment
./deploy.sh --cleanup

# View container logs
./deploy.sh --logs

# Check container status
./deploy.sh --status
```

---

## 🔨 Force Build Commands / 强制构建命令

### Method 1: Using deploy.sh Script (Recommended) / 使用部署脚本（推荐）

```bash
cd /docker/redmine-mcp-server

# Force rebuild (no cache, force remove intermediate containers)
./deploy.sh --force-rebuild

# Force build image only
./deploy.sh --force-rebuild --build-only
```

**What it does**:
- `--no-cache`: Builds without using Docker cache
- `--force-rm`: Removes intermediate containers after build
- Ensures clean build from scratch

### Method 2: Using docker compose / 使用 docker compose

```bash
cd /docker/redmine-mcp-server

# Basic force rebuild
docker compose build --no-cache --force-rm redmine-mcp-server

# Force rebuild and deploy
docker compose build --no-cache --force-rm redmine-mcp-server && docker compose up -d

# Complete clean rebuild
docker compose down --remove-orphans
docker builder prune -a -f
docker compose build --no-cache redmine-mcp-server
docker compose up -d
```

### Method 3: Using docker build / 使用 docker build

```bash
cd /docker/redmine-mcp-server

# Direct docker build
docker build --no-cache --force-rm -t redmine-mcp:latest .

# With pull latest base image
docker build --pull --no-cache --force-rm -t redmine-mcp:latest .
```

### Method 4: Complete Clean Rebuild / 完全清理重建

```bash
cd /docker/redmine-mcp-server

# 1. Stop and remove all containers
docker compose down --remove-orphans

# 2. Remove existing images
docker rmi redmine-mcp:latest 2>/dev/null || true
docker rmi $(docker images | grep redmine-mcp | awk '{print $3}') 2>/dev/null || true

# 3. Clean build cache
docker builder prune -a -f

# 4. Force rebuild
docker compose build --pull --no-cache --force-rm redmine-mcp-server

# 5. Deploy
docker compose up -d

# 6. Verify deployment
docker compose ps
curl http://localhost:8000/health
```

---

## 🧪 Testing Deployment / 测试部署

### Automated Tests / 自动化测试

```bash
cd /docker/redmine-mcp-server

# Run automated endpoint tests
python3 scripts/test_endpoints_auto.py

# Run interactive test server
python3 scripts/test_health_endpoint.py
```

### Manual Tests / 手动测试

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"0.10.0","timestamp":"..."}

# Test root endpoint
curl http://localhost:8000/

# Expected response:
# {"name":"Redmine MCP Server","version":"0.10.0","status":"running",...}

# Test MCP endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## 📊 Verification / 验证

### Check Container Status / 检查容器状态

```bash
# Using docker compose
docker compose ps

# Expected output:
# NAME                       STATUS                              PORTS
# redmine-mcp-server         Up (healthy)                        0.0.0.0:8000->8000/tcp
# redmine-mcp-warehouse-db   Up (healthy)                        0.0.0.0:5432->5432/tcp
```

### Check Image Info / 检查镜像信息

```bash
# List images
docker images | grep redmine-mcp

# Check image creation time
docker inspect redmine-mcp:latest | grep Created

# Check image size
docker images redmine-mcp --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

### View Logs / 查看日志

```bash
# Last 20 lines
docker compose logs --tail=20 redmine-mcp-server

# Follow logs
docker compose logs -f redmine-mcp-server

# Since specific time
docker compose logs --since="2026-02-28T10:00:00" redmine-mcp-server
```

---

## 🔧 Troubleshooting / 故障排查

### Issue: Health check fails after deployment

**Solution**:
```bash
# Wait longer for server to start
sleep 15
curl http://localhost:8000/health

# Check logs for errors
docker compose logs redmine-mcp-server

# Restart container
docker compose restart redmine-mcp-server
```

### Issue: Port already in use

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Stop existing container
docker compose down

# Or change port in docker-compose.yml
```

### Issue: Build fails with cache error

**Solution**:
```bash
# Clean build cache
docker builder prune -a -f

# Force rebuild without cache
docker compose build --no-cache --force-rm redmine-mcp-server
```

### Issue: Container won't start

**Solution**:
```bash
# Check container logs
docker compose logs redmine-mcp-server

# Remove and recreate
docker compose down
docker compose rm -f
docker compose up -d

# Check environment file
cat .env.docker
```

---

## 📝 Configuration / 配置

### Environment File / 环境文件

```bash
# Copy example configuration
cp .env.example .env.docker

# Edit configuration
nano .env.docker

# Required variables:
# - REDMINE_URL
# - REDMINE_API_KEY
# - SERVER_PORT
# - WAREHOUSE_DB_HOST
```

### Docker Compose Configuration / Docker Compose 配置

```yaml
version: '3.8'

services:
  redmine-mcp-server:
    build: .
    container_name: redmine-mcp-server
    ports:
      - "8000:8000"
    env_file:
      - .env.docker
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      warehouse-db:
        condition: service_healthy
    networks:
      - mcp-network
    restart: unless-stopped

  warehouse-db:
    image: postgres:15-alpine
    container_name: redmine-mcp-warehouse-db
    environment:
      POSTGRES_USER: redmine_warehouse
      POSTGRES_PASSWORD: WarehouseP@ss2026
      POSTGRES_DB: redmine_warehouse
    volumes:
      - warehouse_db_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U redmine_warehouse -d redmine_warehouse"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  mcp-network:
    driver: bridge

volumes:
  warehouse_db_data:
    driver: local
```

---

## 🎯 Best Practices / 最佳实践

### 1. Regular Rebuilds / 定期重建

```bash
# Rebuild monthly to get latest security updates
./deploy.sh --force-rebuild
```

### 2. Clean Up Old Images / 清理旧镜像

```bash
# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a
```

### 3. Monitor Container Health / 监控容器健康

```bash
# Check health status
docker compose ps

# View resource usage
docker stats redmine-mcp-server

# Check logs for errors
docker compose logs --tail=100 redmine-mcp-server | grep -i error
```

### 4. Backup Data / 备份数据

```bash
# Backup database
docker compose exec warehouse-db pg_dump -U redmine_warehouse redmine_warehouse > backup.sql

# Backup logs and data
tar -czf backup-$(date +%Y%m%d).tar.gz logs/ data/
```

---

## 📚 Additional Resources / 其他资源

- [Development Testing Guide](DEVELOPMENT_TESTING.md) - Development environment testing
- [Developer Guide](DEVELOPER_GUIDE.md) - Development requirements and guidelines
- [Translation Status](TRANSLATION_100_PERCENT_COMPLETE.md) - Translation completion report

---

**Maintainer**: OpenJaw  
**Contact**: jingzheng.tan@gmail.com  
**Last Updated**: 2026-02-28
