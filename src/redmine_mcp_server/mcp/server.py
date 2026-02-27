#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Server - Main Entry Point
"""

import os
import logging
from dotenv import load_dotenv
from redminelib import Redmine
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Redmine client
redmine = None
REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")

if REDMINE_URL and REDMINE_API_KEY:
    try:
        redmine = Redmine(REDMINE_URL, api_key=REDMINE_API_KEY)
        logger.info("Redmine client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redmine client: {e}")
else:
    logger.warning("Redmine credentials not configured")

# Initialize MCP server
mcp = FastMCP("Redmine")
logger.info("MCP server initialized")

# Import all tool modules (auto-register tools with MCP)
from .tools import (
    issue_tools,
    project_tools,
    wiki_tools,
    attachment_tools,
    search_tools,
    subscription_tools,
    warehouse_tools,
    analytics_tools,
    contributor_tools,
    ads_tools,
    ods_sync_tools,
)

logger.info("All tool modules loaded")

if __name__ == "__main__":
    mcp.run(transport="stdio")
