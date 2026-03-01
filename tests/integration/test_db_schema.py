#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Schema Tests

Tests that verify database table structure, constraints, and indexes.
These tests require a real database connection.

Run with:
  # Uses test database with semantic naming:
  # User: redmine_warehouse_test (test user for Redmine Warehouse)
  # Database: redmine_warehouse_test (isolated test database)
  
  # Default (no env needed):
  pytest tests/integration/test_db_schema.py -v
  
  # Or with custom URL:
  export TEST_DATABASE_URL="postgresql://redmine_warehouse_test:TestWarehouseP@ss2026@localhost:5432/redmine_warehouse_test"
  pytest tests/integration/test_db_schema.py -v

Skip in CI:
  These tests are marked with @pytest.mark.db_schema and automatically
  skipped in GitHub Actions when GITHUB_ACTIONS=true
"""

import pytest
import os
from typing import List, Dict, Any

# Skip all tests in this module if running in CI
pytestmark = [
    pytest.mark.db_schema,
    pytest.mark.skipif(
        os.environ.get('GITHUB_ACTIONS') == 'true',
        reason="Requires real database - skip in GitHub Actions"
    )
]


@pytest.fixture(scope="module")
def db_connection(test_database_url):
    """Create database connection for schema tests.
    
    Connects to test database and queries warehouse schema.
    """
    import psycopg2
    conn = psycopg2.connect(test_database_url)
    
    # Set search path to warehouse schema (where production tables exist)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO warehouse")
    conn.commit()
    
    yield conn
    conn.close()


class TestAdsUserSubscriptionsTable:
    """Test ads_user_subscriptions table structure"""

    def test_table_exists(self, db_connection):
        """Verify ads_user_subscriptions table exists"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'warehouse' 
                    AND table_name = 'ads_user_subscriptions'
                )
            """)
            exists = cur.fetchone()[0]
            assert exists, "Table ads_user_subscriptions does not exist"

    def test_required_columns_exist(self, db_connection):
        """Verify all required columns exist"""
        required_columns = [
            'subscription_id', 'user_id', 'project_id', 'channel',
            'channel_id', 'report_type', 'report_level',
            'created_at', 'updated_at'
        ]

        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'warehouse'
                AND table_name = 'ads_user_subscriptions'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cur.fetchall()]

        for col in required_columns:
            assert col in columns, f"Required column '{col}' missing"

    def test_primary_key_exists(self, db_connection):
        """Verify primary key constraint exists"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_schema = 'warehouse'
                AND table_name = 'ads_user_subscriptions'
                AND constraint_type = 'PRIMARY KEY'
            """)
            pk = cur.fetchone()
            assert pk is not None, "Primary key constraint missing"

    def test_subscription_id_is_primary_key(self, db_connection):
        """Verify subscription_id is the primary key"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'warehouse'
                AND tc.table_name = 'ads_user_subscriptions'
                AND tc.constraint_type = 'PRIMARY KEY'
            """)
            pk_column = cur.fetchone()[0]
            assert pk_column == 'subscription_id', \
                f"Primary key should be subscription_id, got {pk_column}"


class TestDwdIssueDailySnapshotTable:
    """Test dwd_issue_daily_snapshot table structure"""

    def test_table_exists(self, db_connection):
        """Verify dwd_issue_daily_snapshot table exists"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'warehouse'
                    AND table_name = 'dwd_issue_daily_snapshot'
                )
            """)
            exists = cur.fetchone()[0]
            assert exists, "Table dwd_issue_daily_snapshot does not exist"

    def test_composite_unique_constraint(self, db_connection):
        """Verify unique constraint on (issue_id, snapshot_date)"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'warehouse'
                AND tc.table_name = 'dwd_issue_daily_snapshot'
                AND tc.constraint_type = 'UNIQUE'
                ORDER BY kcu.ordinal_position
            """)
            unique_columns = [row[0] for row in cur.fetchall()]

        assert 'issue_id' in unique_columns, \
            "issue_id should be in unique constraint"
        assert 'snapshot_date' in unique_columns, \
            "snapshot_date should be in unique constraint"


class TestDwsProjectDailySummaryTable:
    """Test dws_project_daily_summary table structure"""

    def test_table_exists(self, db_connection):
        """Verify dws_project_daily_summary table exists"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'warehouse'
                    AND table_name = 'dws_project_daily_summary'
                )
            """)
            exists = cur.fetchone()[0]
            assert exists, "Table dws_project_daily_summary does not exist"

    def test_composite_unique_constraint(self, db_connection):
        """Verify unique constraint on (project_id, snapshot_date)"""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'warehouse'
                AND tc.table_name = 'dws_project_daily_summary'
                AND tc.constraint_type = 'UNIQUE'
                ORDER BY kcu.ordinal_position
            """)
            unique_columns = [row[0] for row in cur.fetchall()]

        assert 'project_id' in unique_columns, \
            "project_id should be in unique constraint"
        assert 'snapshot_date' in unique_columns, \
            "snapshot_date should be in unique constraint"


class TestTableIndexes:
    """Test that required indexes exist"""

    def test_subscription_indexes_exist(self, db_connection):
        """Verify indexes on ads_user_subscriptions"""
        expected_indexes = [
            'idx_ads_user_subscriptions_user',
            'idx_ads_user_subscriptions_project',
            'idx_ads_user_subscriptions_channel',
            'idx_ads_user_subscriptions_enabled'
        ]

        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE schemaname = 'warehouse'
                AND tablename = 'ads_user_subscriptions'
            """)
            indexes = [row[0] for row in cur.fetchall()]

        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} missing"

    def test_dwd_snapshot_indexes_exist(self, db_connection):
        """Verify indexes on dwd_issue_daily_snapshot"""
        expected_indexes = [
            'idx_issue_snapshot_date',
            'idx_issue_project_date'
        ]

        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE schemaname = 'warehouse'
                AND tablename = 'dwd_issue_daily_snapshot'
            """)
            indexes = [row[0] for row in cur.fetchall()]

        for idx in expected_indexes:
            assert idx in indexes, f"Index {idx} missing"


class TestInsertSelectOperations:
    """Test that INSERT and SELECT operations work correctly"""

    def test_insert_and_select_subscription(self, db_connection):
        """Verify INSERT and SELECT work on ads_user_subscriptions"""
        import uuid
        from datetime import datetime

        test_id = f"test:{uuid.uuid4().hex[:8]}:email"

        try:
            # INSERT
            with db_connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO warehouse.ads_user_subscriptions (
                        subscription_id, user_id, project_id,
                        channel, channel_id, report_type,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    test_id, 'test_user', 341,
                    'email', 'test@example.com', 'daily',
                    datetime.now(), datetime.now()
                ))
            db_connection.commit()

            # SELECT
            with db_connection.cursor() as cur:
                cur.execute("""
                    SELECT subscription_id, user_id, project_id, channel
                    FROM warehouse.ads_user_subscriptions
                    WHERE subscription_id = %s
                """, (test_id,))
                row = cur.fetchone()

            assert row is not None, "INSERT failed - no row found"
            assert row[0] == test_id, "subscription_id mismatch"
            assert row[1] == 'test_user', "user_id mismatch"
            assert row[2] == 341, "project_id mismatch"
            assert row[3] == 'email', "channel mismatch"

        finally:
            # Cleanup
            with db_connection.cursor() as cur:
                cur.execute("""
                    DELETE FROM warehouse.ads_user_subscriptions
                    WHERE subscription_id = %s
                """, (test_id,))
            db_connection.commit()
