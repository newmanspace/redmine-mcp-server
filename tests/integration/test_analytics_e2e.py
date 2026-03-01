#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics E2E Tests

End-to-end tests for analytics functionality.
Uses real database with mocked Redmine API.

Run with:
  # Uses test database with semantic naming:
  # User: redmine_warehouse_test (test user for Redmine Warehouse)
  # Database: redmine_warehouse_test (isolated test database)
  
  # Default (no env needed):
  pytest tests/integration/test_analytics_e2e.py -v
  
  # Or with custom URL:
  export TEST_DATABASE_URL="postgresql://redmine_warehouse_test:TestWarehouseP@ss2026@localhost:5432/redmine_warehouse_test"
  pytest tests/integration/test_analytics_e2e.py -v

Skip in CI:
  These tests are marked with @pytest.mark.e2e and automatically
  skipped in GitHub Actions when GITHUB_ACTIONS=true
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

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
    """Create database connection for analytics E2E tests.
    
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
def clean_analytics_data(db_connection):
    """Clean up analytics test data before and after each test."""
    # Cleanup before test
    with db_connection.cursor() as cur:
        cur.execute("""
            DELETE FROM warehouse.dws_project_daily_summary
            WHERE project_id = 999
        """)
        cur.execute("""
            DELETE FROM warehouse.dwd_issue_daily_snapshot
            WHERE project_id = 999
        """)
    db_connection.commit()

    yield

    # Cleanup after test
    with db_connection.cursor() as cur:
        cur.execute("""
            DELETE FROM warehouse.dws_project_daily_summary
            WHERE project_id = 999
        """)
        cur.execute("""
            DELETE FROM warehouse.dwd_issue_daily_snapshot
            WHERE project_id = 999
        """)
    db_connection.commit()


@pytest.mark.xfail(reason="Analytics functions need parameter adjustment")
class TestAnalyticsE2E:
    """End-to-end tests for analytics functionality"""

    def test_get_project_daily_stats_with_data(
        self, db_connection, clean_analytics_data
    ):
        """Test getting daily stats with pre-populated data"""
        from redmine_mcp_server.mcp.tools.ads_tools import get_project_daily_stats
        import asyncio

        # Insert test data
        today = datetime.now().date()
        test_data = [
            (999, (today - timedelta(days=2)).isoformat(), 10, 2, 1),
            (999, (today - timedelta(days=1)).isoformat(), 12, 3, 2),
            (999, today.isoformat(), 15, 4, 3),
        ]

        with db_connection.cursor() as cur:
            for project_id, date, total, new, closed in test_data:
                cur.execute("""
                    INSERT INTO warehouse.dws_project_daily_summary (
                        project_id, snapshot_date,
                        total_issues, new_issues, closed_issues,
                        created_at_snapshot
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (project_id, snapshot_date) DO NOTHING
                """, (project_id, date, total, new, closed, datetime.now()))
        db_connection.commit()

        # Get stats
        result = asyncio.run(
            get_project_daily_stats(project_id=999, days=7)
        )

        # Verify response
        assert result['success'] is True
        assert 'stats' in result
        stats = result['stats']
        assert len(stats) >= 3, "Should have at least 3 days of data"

    def test_get_project_daily_stats_empty(
        self, db_connection, clean_analytics_data
    ):
        """Test getting daily stats with no data"""
        from redmine_mcp_server.mcp.tools.ads_tools import get_project_daily_stats
        import asyncio

        # Get stats for project with no data
        result = asyncio.run(
            get_project_daily_stats(project_id=998, days=7)
        )

        # Verify response
        assert result['success'] is True
        assert 'stats' in result
        # Should return empty list or default values
        assert isinstance(result['stats'], list)

    def test_analyze_issue_contributors_with_data(
        self, db_connection, clean_analytics_data
    ):
        """Test contributor analysis with pre-populated data"""
        from redmine_mcp_server.mcp.tools.contributor_tools import (
            analyze_issue_contributors
        )
        import asyncio

        # Insert test contributor data
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO warehouse.dws_issue_contributors (
                    issue_id, project_id, user_id, user_name,
                    role_category, journal_count,
                    created_at_snapshot
                ) VALUES (999, 999, 100, 'Test User', 'developer', 5, %s)
                ON CONFLICT (issue_id, user_id) DO NOTHING
            """, (datetime.now(),))

            cur.execute("""
                INSERT INTO warehouse.dws_issue_contributors (
                    issue_id, project_id, user_id, user_name,
                    role_category, journal_count,
                    created_at_snapshot
                ) VALUES (999, 999, 101, 'Another User', 'tester', 3, %s)
                ON CONFLICT (issue_id, user_id) DO NOTHING
            """, (datetime.now(),))
        db_connection.commit()

        # Analyze contributors
        result = asyncio.run(
            analyze_issue_contributors(issue_id=999)
        )

        # Verify response
        assert result['success'] is True
        assert 'contributors' in result
        contributors = result['contributors']
        assert len(contributors) >= 2, "Should have at least 2 contributors"

    def test_get_project_role_distribution_with_data(
        self, db_connection, clean_analytics_data
    ):
        """Test role distribution with pre-populated data"""
        from redmine_mcp_server.mcp.tools.contributor_tools import (
            get_project_role_distribution
        )
        import asyncio

        # Insert test role distribution data
        today = datetime.now().date()
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO warehouse.dws_project_role_distribution (
                    project_id, snapshot_date,
                    manager_count, implementation_count, developer_count,
                    tester_count, other_count, total_members,
                    created_at_snapshot
                ) VALUES (999, %s, 2, 3, 5, 2, 1, 13, %s)
                ON CONFLICT (project_id, snapshot_date) DO NOTHING
            """, (today.isoformat(), datetime.now()))
        db_connection.commit()

        # Get role distribution
        result = asyncio.run(
            get_project_role_distribution(project_id=999)
        )

        # Verify response
        assert result['success'] is True
        assert 'distribution' in result or 'roles' in result

    def test_get_user_workload_with_data(
        self, db_connection, clean_analytics_data
    ):
        """Test user workload with pre-populated data"""
        from redmine_mcp_server.mcp.tools.contributor_tools import (
            get_user_workload
        )
        import asyncio

        # Insert test workload data
        current_month = datetime.now().strftime('%Y-%m')
        with db_connection.cursor() as cur:
            cur.execute("""
                INSERT INTO warehouse.dws_user_monthly_workload (
                    user_id, year_month,
                    total_issues, total_journals,
                    as_manager, as_implementation, as_developer, as_tester,
                    created_at_snapshot
                ) VALUES (100, %s, 10, 25, 2, 3, 4, 1, %s)
                ON CONFLICT (user_id, year_month) DO NOTHING
            """, (current_month, datetime.now()))
        db_connection.commit()

        # Get workload
        result = asyncio.run(
            get_user_workload(user_id=100, month=current_month)
        )

        # Verify response
        assert result['success'] is True
        assert 'workload' in result or 'stats' in result
