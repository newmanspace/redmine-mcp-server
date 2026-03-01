#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Server - Main Entry Point

Run the server with:
    python -m redmine_mcp_server.main

Or with uvicorn:
    python -m uvicorn redmine_mcp_server.main:app --host 0.0.0.0 --port 8000
"""

import sys
import os

# Add src directory to Python path for development
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import and run main
from redmine_mcp_server.main import main

if __name__ == "__main__":
    main()
