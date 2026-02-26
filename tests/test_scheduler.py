#!/usr/bin/env python3
"""
Unit tests for the RedmineSyncScheduler module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler


class TestRedmineSyncScheduler(unittest.TestCase):
    """Test cases for the RedmineSyncScheduler class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'WAREHOUSE_SYNC_ENABLED': 'true',
            'WAREHOUSE_SYNC_INTERVAL_MINUTES': '10',
            'REDMINE_URL': 'http://redmine.test',
            'REDMIME_API_KEY': 'test-key'
        })
        self.env_patcher.start()
        
        # Mock warehouse
        self.warehouse_patcher = patch('redmine_mcp_server.scheduler.DataWarehouse')
        self.mock_warehouse = self.warehouse_patcher.start()
        
        # Mock requests
        self.requests_patcher = patch('redmine_mcp_server.scheduler.requests')
        self.mock_requests = self.requests_patcher.start()
        
    def tearDown(self):
        """Clean up after each test method."""
        self.env_patcher.stop()
        self.warehouse_patcher.stop()
        self.requests_patcher.stop()

    def test_scheduler_initialization(self):
        """Test that the scheduler initializes correctly."""
        scheduler = RedmineSyncScheduler(project_ids=[1, 2])
        
        # Verify initialization
        self.assertEqual(scheduler.project_ids, [1, 2])
        self.assertEqual(scheduler.sync_interval_minutes, 10)
        self.mock_warehouse.assert_called_once()

    def test_sync_project_success(self):
        """Test successful project sync."""
        # Setup mock responses
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'issues': [
                {
                    'id': 1,
                    'project': {'id': 1},
                    'subject': 'Test Issue',
                    'status': {'id': 1, 'name': 'New'},
                    'priority': {'id': 2, 'name': 'Normal'},
                    'created_on': '2026-02-26T10:00:00Z',
                    'updated_on': '2026-02-26T10:00:00Z'
                }
            ],
            'total_count': 1
        }
        self.mock_requests.get.return_value = mock_response
        
        # Create scheduler and sync
        scheduler = RedmineSyncScheduler(project_ids=[1])
        scheduler.sync_project(1)
        
        # Verify API call
        self.mock_requests.get.assert_called_once()
        args, kwargs = self.mock_requests.get.call_args
        self.assertIn('project_id=1', str(kwargs['params']))
        
        # Verify warehouse call
        self.mock_warehouse.return_value.sync_issues.assert_called_once()

    def test_sync_project_incremental(self):
        """Test incremental project sync."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'issues': [
                {
                    'id': 1,
                    'project': {'id': 1},
                    'subject': 'Test Issue',
                    'status': {'id': 1, 'name': 'New'},
                    'priority': {'id': 2, 'name': 'Normal'},
                    'created_on': '2026-02-26T10:00:00Z',
                    'updated_on': '2026-02-26T10:00:00Z'
                }
            ],
            'total_count': 1
        }
        self.mock_requests.get.return_value = mock_response
        
        # Create scheduler and sync incrementally
        scheduler = RedmineSyncScheduler(project_ids=[1])
        scheduler.sync_project(1, incremental=True)
        
        # Verify API call includes updated_on filter
        self.mock_requests.get.assert_called_once()
        args, kwargs = self.mock_requests.get.call_args
        params = kwargs['params']
        self.assertIn('project_id', params)
        self.assertIn('updated_on', params)

    def test_sync_all_projects(self):
        """Test syncing all projects."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'issues': [{'id': 1, 'project': {'id': 1}, 'subject': 'Test'}],
            'total_count': 1
        }
        self.mock_requests.get.return_value = mock_response
        
        # Create scheduler and sync all
        scheduler = RedmineSyncScheduler(project_ids=[1, 2])
        scheduler.sync_all_projects()
        
        # Verify both projects were synced
        self.assertEqual(self.mock_requests.get.call_count, 2)
        self.assertEqual(self.mock_warehouse.return_value.sync_issues.call_count, 2)

    def test_full_sync_all_projects(self):
        """Test full sync of all projects."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'issues': [{'id': 1, 'project': {'id': 1}, 'subject': 'Test'}],
            'total_count': 1
        }
        self.mock_requests.get.return_value = mock_response
        
        # Create scheduler and do full sync
        scheduler = RedmineSyncScheduler(project_ids=[1, 2])
        scheduler.full_sync_all_projects()
        
        # Verify both projects were fully synced
        self.assertEqual(self.mock_requests.get.call_count, 2)
        self.assertEqual(self.mock_warehouse.return_value.sync_issues.call_count, 2)


if __name__ == '__main__':
    unittest.main()