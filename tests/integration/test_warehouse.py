"""
Warehouse 模块单元测试
"""

import os
import sys
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from redmine_mcp_server.dws.repository import DataWarehouse


class TestDataWarehouse:
    """DataWarehouse 测试类"""
    
    @pytest.fixture
    def mock_env(self):
        """模拟环境变量"""
        with patch.dict(os.environ, {
            'WAREHOUSE_DB_HOST': 'localhost',
            'WAREHOUSE_DB_PORT': '5432',
            'WAREHOUSE_DB_NAME': 'redmine_warehouse_test',
            'WAREHOUSE_DB_USER': 'redmine_warehouse',
            'WAREHOUSE_DB_PASSWORD': 'test_password'
        }):
            yield
    
    def test_init(self, mock_env):
        """测试初始化"""
        with patch('redmine_mcp_server.dws.repository.pool.SimpleConnectionPool') as mock_pool:
            warehouse = DataWarehouse()
            
            assert warehouse.db_host == 'localhost'
            assert warehouse.db_port == '5432'
            assert warehouse.db_name == 'redmine_warehouse_test'
            assert warehouse.db_user == 'redmine_warehouse'
            mock_pool.assert_called_once()
    
    def test_get_connection(self, mock_env):
        """测试获取数据库连接"""
        with patch('redmine_mcp_server.dws.repository.pool.SimpleConnectionPool') as mock_pool:
            mock_conn = MagicMock()
            mock_pool.return_value.getconn.return_value = mock_conn
            
            warehouse = DataWarehouse()
            
            with warehouse.get_connection() as conn:
                assert conn == mock_conn
                mock_pool.return_value.getconn.assert_called_once()
                mock_pool.return_value.putconn.assert_called_once_with(mock_conn)
    
    def test_sync_issues(self, mock_env):
        """测试 Issue 同步"""
        with patch('redmine_mcp_server.dws.repository.pool.SimpleConnectionPool') as mock_pool:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_pool.return_value.getconn.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
            
            warehouse = DataWarehouse()
            
            # 模拟测试数据
            issues = [
                {
                    'id': 1,
                    'subject': 'Test Issue',
                    'status': {'id': 1, 'name': '新建'},
                    'priority': {'id': 2, 'name': '普通'},
                    'assigned_to': {'id': 1, 'name': 'Test User'},
                    'created_on': '2026-02-25T10:00:00Z',
                    'updated_on': '2026-02-25T10:00:00Z'
                }
            ]
            
            warehouse.sync_issues(341, issues, date.today())
            
            # 验证 execute 被调用
            assert mock_cursor.execute.called
    
    def test_get_project_daily_stats(self, mock_env):
        """测试获取项目统计"""
        with patch('redmine_mcp_server.dws.repository.pool.SimpleConnectionPool') as mock_pool:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_pool.return_value.getconn.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
            
            # 模拟返回数据
            mock_cursor.fetchone.return_value = {
                'total_issues': 100,
                'new_issues': 5,
                'closed_issues': 3,
                'status_new': 10,
                'status_in_progress': 20,
                'status_resolved': 5,
                'status_closed': 65,
                'priority_immediate': 2,
                'priority_urgent': 3,
                'priority_high': 10,
                'priority_normal': 80,
                'priority_low': 5
            }
            
            warehouse = DataWarehouse()
            stats = warehouse.get_project_daily_stats(341, date.today())
            
            assert stats['total'] == 100
            assert stats['today_new'] == 5
            assert stats['today_closed'] == 3
            assert 'by_status' in stats
            assert 'by_priority' in stats


class TestScheduler:
    """Scheduler 测试类"""
    
    @pytest.fixture
    def mock_env(self):
        """模拟环境变量"""
        with patch.dict(os.environ, {
            'WAREHOUSE_PROJECT_IDS': '341,372',
            'WAREHOUSE_SYNC_INTERVAL_MINUTES': '10',
            'WAREHOUSE_DB_HOST': 'localhost',
            'WAREHOUSE_DB_PORT': '5432',
            'WAREHOUSE_DB_NAME': 'redmine_warehouse_test',
            'WAREHOUSE_DB_USER': 'redmine_warehouse',
            'WAREHOUSE_DB_PASSWORD': 'test_password'
        }):
            yield
    
    def test_scheduler_init(self, mock_env):
        """测试调度器初始化"""
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        
        scheduler = RedmineSyncScheduler()
        
        assert scheduler.project_ids == [341, 372]
        assert scheduler.sync_interval_minutes == 10
    
    def test_scheduler_custom_interval(self, mock_env):
        """测试自定义同步间隔"""
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        
        scheduler = RedmineSyncScheduler(sync_interval_minutes=5)
        
        assert scheduler.sync_interval_minutes == 5
    
    def test_get_sync_status(self, mock_env):
        """测试获取同步状态"""
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        
        with patch('redmine_mcp_server.scheduler.DataWarehouse'):
            with patch('redmine_mcp_server.scheduler.BlockingScheduler') as mock_sched:
                mock_sched.return_value.running = True
                mock_sched.return_value.get_job.return_value = MagicMock(
                    next_run_time=datetime.now() + timedelta(minutes=10)
                )
                
                scheduler = RedmineSyncScheduler()
                scheduler.scheduler = mock_sched.return_value
                scheduler.warehouse = MagicMock()
                
                status = scheduler.get_sync_status()
                
                assert status['running'] is True
                assert status['projects'] == [341, 372]
                assert status['interval_minutes'] == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
