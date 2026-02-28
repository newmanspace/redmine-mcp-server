#!/usr/bin/env python3
"""
Unit tests for warehouse read operations.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from redmine_mcp_server.dws.repository import DataWarehouse


class TestWarehouseReadOperations(unittest.TestCase):
    """Test warehouse read operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.warehouse = DataWarehouse()

    @patch('redmine_mcp_server.dws.repository.psycopg2')
    def test_get_project_daily_stats_basic(self, mock_psycopg2):
        """Test basic project stats retrieval."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchone.return_value = {
            'total_issues': 144,
            'new_issues': 3,
            'closed_issues': 4,
            'status_new': 10,
            'status_in_progress': 50,
            'status_resolved': 20,
            'status_closed': 60,
            'status_feedback': 4,
            'priority_immediate': 2,
            'priority_urgent': 3,
            'priority_high': 15,
            'priority_normal': 120,
            'priority_low': 4
        }
        
        # Call method
        result = self.warehouse.get_project_daily_stats(341)
        
        # Verify results
        self.assertEqual(result['project_id'], 341)
        self.assertEqual(result['total'], 144)
        self.assertEqual(result['today_new'], 3)
        self.assertEqual(result['today_closed'], 4)
        self.assertEqual(result['by_status']['新建'], 10)
        self.assertEqual(result['by_status']['进行中'], 50)
        self.assertEqual(result['by_priority']['立刻'], 2)
        self.assertEqual(result['by_priority']['紧急'], 3)

    @patch('redmine_mcp_server.dws.repository.psycopg2')
    def test_get_high_priority_issues(self, mock_psycopg2):
        """Test high priority issues retrieval."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            {'issue_id': 77684, 'subject': '出中间库——请联系管理员', 'priority_name': '立刻', 'status_name': '新建', 'assigned_to_name': '白 如峰'},
            {'issue_id': 77607, 'subject': '取消搜索框权限校验', 'priority_name': '紧急', 'status_name': '已关闭', 'assigned_to_name': '游 源'}
        ]
        
        # Call method
        result = self.warehouse.get_high_priority_issues(341, limit=10)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['issue_id'], 77684)
        self.assertEqual(result[0]['priority_name'], '立刻')
        self.assertEqual(result[1]['issue_id'], 77607)
        self.assertEqual(result[1]['priority_name'], '紧急')

    @patch('redmine_mcp_server.dws.repository.psycopg2')
    def test_get_top_assignees(self, mock_psycopg2):
        """Test top assignees retrieval."""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            {'assigned_to_name': '游 源', 'total': 25, 'in_progress': 10, 'high_priority': 5},
            {'assigned_to_name': '汪 晓娟', 'total': 20, 'in_progress': 8, 'high_priority': 3}
        ]
        
        # Call method
        result = self.warehouse.get_top_assignees(341, '2026-02-25', limit=5)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['assigned_to_name'], '游 源')
        self.assertEqual(result[0]['total'], 25)
        self.assertEqual(result[1]['assigned_to_name'], '汪 晓娟')
        self.assertEqual(result[1]['total'], 20)


if __name__ == '__main__':
    unittest.main()