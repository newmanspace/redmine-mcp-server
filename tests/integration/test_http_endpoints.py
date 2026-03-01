"""
Tests for HTTP endpoints in the MCP server.

Tests cover:
- /health endpoint
"""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.unit
class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.fixture
    def app(self):
        """Get the Starlette app for testing."""
        from redmine_mcp_server.main import app
        return app

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, app):
        """Test that /health returns 200 with status healthy."""
        from httpx import ASGITransport, AsyncClient
        
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with patch(
                "redmine_mcp_server.redmine_handler._ensure_cleanup_started",
                new_callable=AsyncMock,
            ):
                response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_has_required_fields(self, app):
        """Test that /health response has all required fields."""
        from httpx import ASGITransport, AsyncClient
        
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with patch(
                "redmine_mcp_server.redmine_handler._ensure_cleanup_started",
                new_callable=AsyncMock,
            ):
                response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
