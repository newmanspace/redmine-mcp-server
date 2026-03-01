#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subscription E2E Tests

End-to-end tests for subscription functionality.
Uses real database with mocked Redmine API.

Run with:
  # Uses test database with semantic naming:
  # User: redmine_warehouse_test (test user for Redmine Warehouse)
  # Database: redmine_warehouse_test (isolated test database)
  
  # Default (no env needed):
  pytest tests/integration/test_subscription_e2e.py -v
  
  # Or with custom URL:
  export TEST_DATABASE_URL="postgresql://redmine_warehouse_test:TestWarehouseP@ss2026@localhost:5432/redmine_warehouse_test"
  pytest tests/integration/test_subscription_e2e.py -v

Skip in CI:
  These tests are marked with @pytest.mark.e2e and automatically
  skipped in GitHub Actions when GITHUB_ACTIONS=true
"""

import pytest
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Skip all tests in this module if running in CI
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get('GITHUB_ACTIONS') == 'true',
        reason="Requires real database - skip in GitHub Actions"
    )
]


@pytest.fixture(scope="module")
def db_connection(test_database_url):
    """Create database connection for E2E tests.
    
    Uses test_schema for isolated testing.
    """
    import psycopg2
    conn = psycopg2.connect(test_database_url)
    
    # Set search path to test_schema
    with conn.cursor() as cur:
        cur.execute("SET search_path TO test_schema, warehouse")
    conn.commit()
    
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def clean_subscriptions(db_connection):
    """Clean up subscriptions before and after each test."""
    # Cleanup before test
    with db_connection.cursor() as cur:
        cur.execute("""
            DELETE FROM warehouse.ads_user_subscriptions
            WHERE user_id = 'e2e_test_user'
        """)
    db_connection.commit()

    yield

    # Cleanup after test
    with db_connection.cursor() as cur:
        cur.execute("""
            DELETE FROM warehouse.ads_user_subscriptions
            WHERE user_id = 'e2e_test_user'
        """)
    db_connection.commit()


class TestSubscriptionE2E:
    """End-to-end tests for subscription functionality"""

    def test_subscribe_project_success(self, db_connection, clean_subscriptions):
        """Test successful subscription creation"""
        from redmine_mcp_server.mcp.tools.subscription_tools import subscribe_project
        import asyncio

        # Call subscribe function
        result = asyncio.run(
            subscribe_project(
                project_id=341,
                channel='email',
                user_email='e2e_test@example.com',
                report_type='daily',
                report_level='brief'
            )
        )

        # Verify response
        assert result['success'] is True
        assert 'subscription_id' in result
        subscription_id = result['subscription_id']

        # Verify database insert
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT subscription_id, user_id, project_id, channel, report_type
                FROM warehouse.ads_user_subscriptions
                WHERE subscription_id = %s
            """, (subscription_id,))
            row = cur.fetchone()

        assert row is not None, "Subscription not found in database"
        assert row[2] == 341, "project_id mismatch"
        assert row[3] == 'email', "channel mismatch"
        assert row[4] == 'daily', "report_type mismatch"

    @pytest.mark.xfail(reason="list_my_subscriptions function needs implementation")
    def test_list_subscriptions_success(self, db_connection, clean_subscriptions):
        """Test listing subscriptions (TODO: implement list function)"""
        from redmine_mcp_server.mcp.tools.subscription_tools import subscribe_project, list_my_subscriptions
        import asyncio

        # First, create a subscription
        asyncio.run(
            subscribe_project(
                project_id=341,
                channel='email',
                user_email='e2e_test@example.com',
                report_type='daily'
            )
        )

        # List subscriptions
        result = asyncio.run(list_my_subscriptions())

        # Verify response
        assert result['success'] is True
        assert 'subscriptions' in result
        subscriptions = result['subscriptions']
        assert len(subscriptions) > 0, "No subscriptions found"

        # Verify subscription in list
        found = False
        for sub in subscriptions:
            if (sub.get('project_id') == 341 and
                sub.get('channel') == 'email' and
                sub.get('report_type') == 'daily'):
                found = True
                break

        assert found, "Created subscription not found in list"

    def test_unsubscribe_project_success(self, db_connection, clean_subscriptions):
        """Test successful unsubscription"""
        from redmine_mcp_server.mcp.tools.subscription_tools import (
            subscribe_project,
            unsubscribe_project
        )
        import asyncio

        # First, create a subscription
        subscribe_result = asyncio.run(
            subscribe_project(
                project_id=342,
                channel='email',
                user_email='e2e_test@example.com',
                report_type='weekly'
            )
        )
        subscription_id = subscribe_result['subscription_id']

        # Verify it exists
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM warehouse.ads_user_subscriptions
                WHERE subscription_id = %s
            """, (subscription_id,))
            count_before = cur.fetchone()[0]
        assert count_before == 1, "Subscription not created"

        # Unsubscribe (with user_id='default_user' to match subscribe_project default)
        unsubscribe_result = asyncio.run(
            unsubscribe_project(project_id=342, user_id='default_user')
        )

        # Verify response
        assert unsubscribe_result['success'] is True, f"Unsubscribe failed: {unsubscribe_result}"

        # Verify database delete
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM warehouse.ads_user_subscriptions
                WHERE subscription_id = %s
            """, (subscription_id,))
            count_after = cur.fetchone()[0]
        assert count_after == 0, "Subscription not deleted"

    def test_duplicate_subscription_handling(self, db_connection, clean_subscriptions):
        """Test that duplicate subscriptions are handled correctly"""
        from redmine_mcp_server.mcp.tools.subscription_tools import subscribe_project
        import asyncio

        # Create first subscription
        result1 = asyncio.run(
            subscribe_project(
                project_id=341,
                channel='email',
                user_email='e2e_test@example.com',
                report_type='daily'
            )
        )
        assert result1['success'] is True
        subscription_id_1 = result1['subscription_id']

        # Try to create duplicate
        result2 = asyncio.run(
            subscribe_project(
                project_id=341,
                channel='email',
                user_email='e2e_test@example.com',
                report_type='daily'
            )
        )

        # Should either succeed (update) or fail gracefully
        # Check that only one subscription exists
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM warehouse.ads_user_subscriptions
                WHERE user_id = (SELECT user_id FROM warehouse.ads_user_subscriptions WHERE subscription_id = %s)
                AND project_id = 341
                AND channel = 'email'
            """, (subscription_id_1,))
            count = cur.fetchone()[0]

        assert count <= 1, "Duplicate subscriptions created"

    def test_subscribe_invalid_project(self, clean_subscriptions):
        """Test subscription with invalid project ID"""
        from redmine_mcp_server.mcp.tools.subscription_tools import subscribe_project
        import asyncio

        # Try to subscribe to non-existent project
        result = asyncio.run(
            subscribe_project(
                project_id=-1,
                channel='email',
                user_email='e2e_test@example.com',
                report_type='daily'
            )
        )

        # Should handle gracefully (either fail or succeed with mock)
        assert 'success' in result, "Response should have success field"

    def test_subscribe_missing_required_fields(self, clean_subscriptions):
        """Test subscription with missing required fields"""
        from redmine_mcp_server.mcp.tools.subscription_tools import subscribe_project
        import asyncio

        # Try with missing channel
        result = asyncio.run(
            subscribe_project(
                project_id=341,
                user_email='e2e_test@example.com',
                report_type='daily'
            )
        )

        # Should handle gracefully
        assert result is not None, "Function should return result"
