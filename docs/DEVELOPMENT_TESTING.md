# Development Testing Guide / 开发测试指南

**Version**: 1.0  
**Date**: 2026-02-28  
**Purpose**: Test health and root endpoints in development environment

---

## 🧪 Automated Test / 自动化测试

### Run Automated Tests

```bash
cd /docker/redmine-mcp-server

# Run automated endpoint tests
python3 scripts/test_endpoints_auto.py
```

**Expected Output**:
```
✅ ALL TESTS PASSED!

Test 1: GET /health
  ✅ Status: 200
  ✅ Response: {'status': 'healthy', 'version': '0.10.0', ...}

Test 2: GET /
  ✅ Status: 200
  ✅ Response: {'name': 'Redmine MCP Server', ...}

Test 3: GET /mcp
  ✅ MCP endpoint exists
```

---

## 🖥️ Interactive Test / 交互式测试

### Run Interactive Test Server

```bash
cd /docker/redmine-mcp-server

# Run interactive test server (port 8080)
python3 scripts/test_health_endpoint.py
```

**Then in another terminal**:
```bash
# Test health endpoint
curl http://127.0.0.1:8080/health

# Test root endpoint
curl http://127.0.0.1:8080/

# Test MCP endpoint
curl -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## 📝 Manual Test / 手动测试

### 1. Start Development Server

```bash
cd /docker/redmine-mcp-server

# Set environment
export SERVER_PORT=8080
export REDMINE_URL=http://test-redmine.com
export REDMINE_API_KEY=test_api_key

# Install dependencies
pip install -e .[dev]

# Run server
python -m uvicorn src.redmine_mcp_server.main:app --host 127.0.0.1 --port 8080
```

### 2. Test Endpoints

```bash
# Health check
curl http://127.0.0.1:8080/health

# Root endpoint
curl http://127.0.0.1:8080/

# MCP tools list
curl -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## ✅ Expected Responses / 预期响应

### GET /health

```json
{
  "status": "healthy",
  "version": "0.10.0",
  "timestamp": "2026-02-28T20:53:43.100703"
}
```

### GET /

```json
{
  "name": "Redmine MCP Server",
  "version": "0.10.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "mcp": "/mcp",
    "files": "/files/{file_id}"
  }
}
```

### GET /mcp

Returns `406 Not Acceptable` (expected - requires specific headers)

---

## 🐳 Docker Production Deployment

### Build and Deploy

```bash
cd /docker/redmine-mcp-server

# Build image
docker compose build

# Deploy
docker compose up -d

# Check logs
docker compose logs redmine-mcp-server

# Test health endpoint
curl http://localhost:8000/health
```

---

## 🔧 Troubleshooting / 故障排查

### Issue: Port already in use

**Solution**: Change port in test script
```python
os.environ["SERVER_PORT"] = "8082"  # Use different port
```

### Issue: Module not found

**Solution**: Install package in development mode
```bash
pip install -e .
```

### Issue: Import errors

**Solution**: Add src to Python path
```bash
export PYTHONPATH=src:$PYTHONPATH
```

---

## 📊 Test Coverage / 测试覆盖

| Endpoint | Method | Test Status | Coverage |
|----------|--------|-------------|----------|
| `/health` | GET | ✅ Automated | 100% |
| `/` | GET | ✅ Automated | 100% |
| `/mcp` | POST | ✅ Exists | Basic |
| `/files/{id}` | GET | ⏳ Pending | - |

---

**Maintainer**: OpenJaw  
**Last Updated**: 2026-02-28
