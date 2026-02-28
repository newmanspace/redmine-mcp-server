#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Development Test Script for Redmine MCP Server

This script is for development and testing purposes only.
It runs the server on a different port (8080) for testing.

Usage:
    python scripts/test_health_endpoint.py
"""

import os
import sys
import time
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set test environment
os.environ["SERVER_PORT"] = "8080"
os.environ["REDMINE_URL"] = "http://test-redmine.com"
os.environ["REDMINE_API_KEY"] = "test_api_key"

print("=" * 70)
print("Redmine MCP Server - Development Test")
print("=" * 70)
print()

# Test 1: Import and start server
print("Test 1: Starting server on port 8080...")
try:
    import uvicorn
    from redmine_mcp_server.main import app
    
    print("✅ Server imported successfully")
    print()
    
    # Start server in background
    import threading
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning"),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    print("✅ Server started")
    print()
    
except Exception as e:
    print(f"❌ Failed to start server: {e}")
    sys.exit(1)

# Test 2: Health endpoint
print("Test 2: Testing /health endpoint...")
try:
    response = requests.get("http://127.0.0.1:8080/health", timeout=5)
    assert response.status_code == 200, f"Status code: {response.status_code}"
    
    data = response.json()
    assert data["status"] == "healthy", f"Status: {data['status']}"
    assert "version" in data, "Missing version"
    assert "timestamp" in data, "Missing timestamp"
    
    print(f"✅ Health check passed!")
    print(f"   Status: {data['status']}")
    print(f"   Version: {data['version']}")
    print(f"   Timestamp: {data['timestamp']}")
    print()
    
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)

# Test 3: Root endpoint
print("Test 3: Testing / endpoint...")
try:
    response = requests.get("http://127.0.0.1:8080/", timeout=5)
    assert response.status_code == 200, f"Status code: {response.status_code}"
    
    data = response.json()
    assert data["name"] == "Redmine MCP Server", f"Name: {data['name']}"
    assert "version" in data, "Missing version"
    assert data["status"] == "running", f"Status: {data['status']}"
    
    print(f"✅ Root endpoint passed!")
    print(f"   Name: {data['name']}")
    print(f"   Version: {data['version']}")
    print(f"   Status: {data['status']}")
    print()
    
except Exception as e:
    print(f"❌ Root endpoint failed: {e}")
    sys.exit(1)

# Test 4: MCP endpoint exists
print("Test 4: Testing /mcp endpoint exists...")
try:
    # MCP endpoint requires specific headers, just check it exists
    response = requests.get("http://127.0.0.1:8080/mcp", timeout=5)
    # Should return 400 or 405 (method not allowed) but not 404
    assert response.status_code != 404, "MCP endpoint not found"
    
    print(f"✅ MCP endpoint exists (status: {response.status_code})")
    print()
    
except Exception as e:
    print(f"❌ MCP endpoint check failed: {e}")
    sys.exit(1)

# Summary
print("=" * 70)
print("✅ All tests passed!")
print("=" * 70)
print()
print("Development server is running on: http://127.0.0.1:8080")
print("Health check: http://127.0.0.1:8080/health")
print("Root endpoint: http://127.0.0.1:8080/")
print("MCP endpoint: http://127.0.0.1:8080/mcp")
print()
print("Press Ctrl+C to stop the test server")
print()

# Keep server running for manual testing
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nTest server stopped")
    sys.exit(0)
