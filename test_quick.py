#!/usr/bin/env python3
"""
快速测试脚本 - 用于开发阶段快速验证代码
用法：python test_quick.py
"""

import os
import sys
from datetime import datetime, date

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置测试环境变量
os.environ['WAREHOUSE_DB_HOST'] = 'localhost'
os.environ['WAREHOUSE_DB_PORT'] = '5432'
os.environ['WAREHOUSE_DB_NAME'] = 'redmine_warehouse_test'
os.environ['WAREHOUSE_DB_USER'] = 'redmine_warehouse'
os.environ['WAREHOUSE_DB_PASSWORD'] = 'WarehouseP@ss2026'
os.environ['WAREHOUSE_PROJECT_IDS'] = '341,372'
os.environ['WAREHOUSE_SYNC_INTERVAL_MINUTES'] = '10'
os.environ['WAREHOUSE_SYNC_ENABLED'] = 'true'

def test_warehouse_import():
    """测试 warehouse 模块导入"""
    print("📦 测试 warehouse 模块导入...")
    try:
        from redmine_mcp_server.redmine_warehouse import DataWarehouse
        print("✅ warehouse 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ warehouse 模块导入失败：{e}")
        return False

def test_scheduler_import():
    """测试 scheduler 模块导入"""
    print("\n⏰ 测试 scheduler 模块导入...")
    try:
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        print("✅ scheduler 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ scheduler 模块导入失败：{e}")
        return False

def test_warehouse_init():
    """测试 warehouse 初始化"""
    print("\n🗄️  测试 warehouse 初始化...")
    try:
        from redmine_mcp_server.redmine_warehouse import DataWarehouse
        from unittest.mock import patch, MagicMock
        
        with patch('redmine_mcp_server.warehouse.pool.SimpleConnectionPool') as mock_pool:
            warehouse = DataWarehouse()
            
            assert warehouse.db_host == 'localhost'
            assert warehouse.db_port == '5432'
            assert warehouse.db_name == 'redmine_warehouse_test'
            
            print("✅ warehouse 初始化成功")
            return True
    except Exception as e:
        print(f"❌ warehouse 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler_init():
    """测试 scheduler 初始化"""
    print("\n🕐 测试 scheduler 初始化...")
    try:
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        from unittest.mock import patch
        
        with patch('redmine_mcp_server.scheduler.DataWarehouse'):
            with patch('redmine_mcp_server.scheduler.BlockingScheduler'):
                scheduler = RedmineSyncScheduler()
                
                assert scheduler.project_ids == [341, 372]
                assert scheduler.sync_interval_minutes == 10
                
                print("✅ scheduler 初始化成功")
                return True
    except Exception as e:
        print(f"❌ scheduler 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_integration():
    """测试 main 模块集成"""
    print("\n🚀 测试 main 模块集成...")
    try:
        from redmine_mcp_server import main
        print("✅ main 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ main 模块导入失败：{e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 Redmine MCP Server 快速测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_warehouse_import),
        ("Scheduler 导入", test_scheduler_import),
        ("Warehouse 初始化", test_warehouse_init),
        ("Scheduler 初始化", test_scheduler_init),
        ("Main 集成", test_main_integration),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
