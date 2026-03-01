#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest Configuration and Fixtures
"""

import pytest
import os


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark tests as integration tests (require Redmine)",
    )
    config.addinivalue_line(
        "markers",
        "unit: mark tests as unit tests (use mocks, no external dependencies)",
    )
    config.addinivalue_line(
        "markers",
        "db_schema: mark test as requiring real database (skip in CI)"
    )
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test requiring real database (skip in CI)"
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    import os
    import sys

    # Add src to Python path if not already there
    src_path = os.path.join(os.path.dirname(__file__), "..", "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Set test environment variable
    os.environ["TESTING"] = "true"

    yield

    # Cleanup after tests
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to mock environment variables for testing."""
    monkeypatch.setenv("REDMINE_URL", "https://test-redmine.example.com")
    monkeypatch.setenv("REDMINE_USERNAME", "test_user")
    monkeypatch.setenv("REDMINE_PASSWORD", "test_password")
    monkeypatch.setenv("SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("SERVER_PORT", "8000")


@pytest.fixture
def mock_api_key_env(monkeypatch):
    """Fixture to mock API key authentication environment."""
    monkeypatch.setenv("REDMINE_URL", "https://test-redmine.example.com")
    monkeypatch.setenv("REDMINE_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("SERVER_PORT", "8000")
    # Remove username/password if they exist
    monkeypatch.delenv("REDMINE_USERNAME", raising=False)
    monkeypatch.delenv("REDMINE_PASSWORD", raising=False)


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL from environment.
    
    Default: PostgreSQL test database for Redmine Warehouse
    - User: redmine_warehouse_test (semantic name for testing)
    - Database: redmine_warehouse_test (isolated test database)
    
    Skip tests if TEST_DATABASE_URL is not set.
    This is used for DB schema and E2E tests.
    """
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        # Default to test database configuration with semantic naming
        # Note: Password is URL-encoded to handle special characters
        url = "postgresql://redmine_warehouse_test:TestWarehouseP%40ss2026@localhost:5432/redmine_warehouse_test"
    return url


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables for E2E tests.
    
    Configures database connection to use test database instead of Docker network.
    """
    # Set warehouse database connection for E2E tests
    monkeypatch.setenv('WAREHOUSE_DB_HOST', 'localhost')
    monkeypatch.setenv('WAREHOUSE_DB_PORT', '5432')
    monkeypatch.setenv('WAREHOUSE_DB_NAME', 'redmine_warehouse_test')
    monkeypatch.setenv('WAREHOUSE_DB_USER', 'redmine_warehouse_test')
    monkeypatch.setenv('WAREHOUSE_DB_PASSWORD', 'TestWarehouseP@ss2026')
