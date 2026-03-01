#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subscription Push E2E Tests

Tests for subscription push functionality in subscription_push_tools.py
These tests were missing - added to catch ISSUE-005 import errors.

Run with:
  pytest tests/integration/test_subscription_push_e2e.py -v
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Skip all tests in this module if running in CI
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get('GITHUB_ACTIONS') == 'true',
        reason="Requires real database - skip in GitHub Actions"
    )
]


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables for E2E tests."""
    monkeypatch.setenv('WAREHOUSE_DB_HOST', 'localhost')
    monkeypatch.setenv('WAREHOUSE_DB_PORT', '5432')
    monkeypatch.setenv('WAREHOUSE_DB_NAME', 'redmine_warehouse_test')
    monkeypatch.setenv('WAREHOUSE_DB_USER', 'redmine_warehouse_test')
    monkeypatch.setenv('WAREHOUSE_DB_PASSWORD', 'TestWarehouseP@ss2026')


class TestSubscriptionPushE2E:
    """End-to-end tests for subscription push functionality"""

    def test_push_subscription_reports_import(self):
        """Test that push_subscription_reports can be imported (catches import errors)"""
        from redmine_mcp_server.mcp.tools.subscription_push_tools import push_subscription_reports
        import asyncio
        
        # Just verify it can be imported and called without import errors
        result = asyncio.run(push_subscription_reports(report_type='daily'))
        
        # Should return a result (may fail due to no subscriptions, but import should work)
        assert result is not None
        assert 'success' in result or 'error' in result

    def test_send_project_report_email_import(self):
        """Test that send_project_report_email can be imported (catches import errors)"""
        from redmine_mcp_server.mcp.tools.subscription_push_tools import send_project_report_email
        import asyncio
        
        # Just verify it can be imported
        assert send_project_report_email is not None
        
        # Try to call with minimal params (will fail but import should work)
        result = asyncio.run(
            send_project_report_email(
                project_id=341,
                report_type='daily',
                to_email='test@example.com'
            )
        )
        
        # Import worked, execution may fail
        assert result is not None

    def test_get_subscription_scheduler_status_import(self):
        """Test that get_subscription_scheduler_status can be imported (catches import errors)"""
        from redmine_mcp_server.mcp.tools.subscription_push_tools import get_subscription_scheduler_status
        import asyncio
        
        # Verify function exists and can be called
        result = asyncio.run(get_subscription_scheduler_status())
        
        # Should return scheduler status
        assert result is not None
        # May return error if scheduler not initialized, but import should work
        assert isinstance(result, dict)
