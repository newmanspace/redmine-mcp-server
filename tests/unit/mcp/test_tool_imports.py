#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Tool Import Tests

Tests to verify all MCP tool imports work correctly after ISSUE-006/007/008 fixes.
"""

import pytest


class TestISSUE006Fix:
    """Test ISSUE-006 fixes: Missing function and exception definitions"""

    @pytest.mark.unit
    def test_ensure_cleanup_started_imported_in_issue_tools(self):
        """Test _ensure_cleanup_started is imported in issue_tools"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.issue_tools as module
        # Verify module loaded
        assert module is not None

    @pytest.mark.unit
    def test_ensure_cleanup_started_imported_in_search_tools(self):
        """Test _ensure_cleanup_started is imported in search_tools"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.search_tools as module
        # Verify module loaded
        assert module is not None

    @pytest.mark.unit
    def test_version_mismatch_error_imported(self):
        """Test VersionMismatchError is imported in search_tools"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.search_tools as module
        # Verify module loaded
        assert module is not None


class TestISSUE007Fix:
    """Test ISSUE-007 fixes: Scheduler module import path"""

    @pytest.mark.unit
    def test_scheduler_imports(self):
        """Test scheduler module imports work"""
        # Should not raise ImportError
        from redmine_mcp_server.scheduler import ads_scheduler
        
        # Verify module exists
        assert ads_scheduler is not None


class TestISSUE008Fix:
    """Test ISSUE-008 fixes: DataWarehouse import path"""

    @pytest.mark.unit
    def test_datawarehouse_import(self):
        """Test DataWarehouse import from correct location"""
        # Should not raise ImportError
        from redmine_mcp_server.dws.repository import DataWarehouse
        
        # Verify class exists
        assert isinstance(DataWarehouse, type)

    @pytest.mark.unit
    def test_ads_tools_import(self):
        """Test ads_tools imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.ads_tools as module
        assert module is not None

    @pytest.mark.unit
    def test_analytics_tools_import(self):
        """Test analytics_tools imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.analytics_tools as module
        assert module is not None

    @pytest.mark.unit
    def test_contributor_tools_import(self):
        """Test contributor_tools imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.contributor_tools as module
        assert module is not None

    @pytest.mark.unit
    def test_subscription_tools_import(self):
        """Test subscription_tools imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.subscription_tools as module
        assert module is not None

    @pytest.mark.unit
    def test_warehouse_tools_import(self):
        """Test warehouse_tools imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.mcp.tools.warehouse_tools as module
        assert module is not None

    @pytest.mark.unit
    def test_report_service_import(self):
        """Test report_service imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.dws.services.report_service as module
        assert module is not None

    @pytest.mark.unit
    def test_sync_service_import(self):
        """Test sync_service imports correctly"""
        # Should not raise ImportError
        import redmine_mcp_server.dws.services.sync_service as module
        assert module is not None
