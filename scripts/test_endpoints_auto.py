#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Test for Health and Root Endpoints

Run this script to test the health and root endpoints.
This is for development/testing purposes only.

Usage:
    python scripts/test_endpoints_auto.py
"""

import os
import sys
import time
import requests
from pathlib import Path
import multiprocessing
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set test environment
os.environ["SERVER_PORT"] = "8081"
os.environ["REDMINE_URL"] = "http://test-redmine.com"
os.environ["REDMINE_API_KEY"] = "test_api_key"

def run_server():
    """Run server in separate process"""
    from redmine_mcp_server.main import app
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="error")

def test_endpoints():
    """Test all endpoints"""
    print("=" * 70)
    print("Redmine MCP Server - Automated Endpoint Tests")
    print("=" * 70)
    print()
    
    # Start server in background process
    print("🚀 Starting test server on port 8081...")
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test 1: Health endpoint
        print("Test 1: GET /health")
        response = requests.get("http://127.0.0.1:8081/health", timeout=5)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        
        print(f"  ✅ Status: {response.status_code}")
        print(f"  ✅ Response: {data}")
        print()
        
        # Test 2: Root endpoint
        print("Test 2: GET /")
        response = requests.get("http://127.0.0.1:8081/", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Redmine MCP Server"
        assert data["status"] == "running"
        
        print(f"  ✅ Status: {response.status_code}")
        print(f"  ✅ Response: {data}")
        print()
        
        # Test 3: MCP endpoint exists
        print("Test 3: GET /mcp (should exist)")
        response = requests.get("http://127.0.0.1:8081/mcp", timeout=5)
        
        # Should not be 404
        assert response.status_code != 404, "MCP endpoint not found"
        
        print(f"  ✅ MCP endpoint exists (status: {response.status_code})")
        print()
        
        # Summary
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        
        return True
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    finally:
        # Stop server
        print("🛑 Stopping test server...")
        server_process.terminate()
        server_process.join(timeout=5)
        print("✅ Server stopped")
        print()

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1)
