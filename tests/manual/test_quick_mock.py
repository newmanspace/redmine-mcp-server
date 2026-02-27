#!/usr/bin/env python3
"""
Redmine MCP Server 快速测试（Mock 版）
用于在不安装依赖的情况下验证代码语法和基本结构
"""

import sys
import os
import traceback

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock 所有外部依赖
MOCK_MODULES = [
    'psycopg2',
    'psycopg2.pool',
    'psycopg2.extras',
    'apscheduler',
    'apscheduler.schedulers.blocking',
    'apscheduler.schedulers.asyncio',
    'apscheduler.triggers.cron',
    'dotenv',
    'redminelib',
    'redminelib.exceptions',
    'requests',
    'requests.exceptions',
    'starlette',
    'starlette.middleware.trustedhost',
    'uvicorn',
    'mcp',
    'fastapi',
]

for mod_name in MOCK_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = __import__('types').SimpleNamespace()

print("=" * 60)
print("🧪 Redmine MCP Server 快速测试（Mock 版）")
print("=" * 60)

test_results = []

def test_warehouse_syntax():
    """测试 warehouse 模块语法"""
    try:
        with open('/docker/redmine-mcp-server/src/redmine_mcp_server/warehouse.py', 'r') as f:
            compile(f.read(), 'warehouse.py', 'exec')
        print("✅ warehouse.py 语法正确")
        test_results.append(True)
    except Exception as e:
        print(f"❌ warehouse.py 语法错误: {e}")
        test_results.append(False)

def test_scheduler_syntax():
    """测试 scheduler 模块语法"""
    try:
        with open('/docker/redmine-mcp-server/src/redmine_mcp_server/scheduler.py', 'r') as f:
            compile(f.read(), 'scheduler.py', 'exec')
        print("✅ scheduler.py 语法正确")
        test_results.append(True)
    except Exception as e:
        print(f"❌ scheduler.py 语法错误: {e}")
        test_results.append(False)

def test_main_syntax():
    """测试 main 模块语法"""
    try:
        with open('/docker/redmine-mcp-server/src/redmine_mcp_server/main.py', 'r') as f:
            compile(f.read(), 'main.py', 'exec')
        print("✅ main.py 语法正确")
        test_results.append(True)
    except Exception as e:
        print(f"❌ main.py 语法错误: {e}")
        test_results.append(False)

def test_warehouse_import():
    """测试 warehouse 模块导入"""
    try:
        from redmine_mcp_server.redmine_warehouse import DataWarehouse
        # 检查关键方法是否存在
        assert hasattr(DataWarehouse, '__init__')
        assert hasattr(DataWarehouse, 'get_project_daily_stats')
        assert hasattr(DataWarehouse, 'get_high_priority_issues')
        assert hasattr(DataWarehouse, 'get_top_assignees')
        print("✅ warehouse 模块导入成功")
        test_results.append(True)
    except Exception as e:
        print(f"❌ warehouse 模块导入失败: {e}")
        test_results.append(False)

def test_scheduler_import():
    """测试 scheduler 模块导入"""
    try:
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        # 检查关键方法是否存在
        assert hasattr(RedmineSyncScheduler, '__init__')
        assert hasattr(RedmineSyncScheduler, 'sync_all_projects')
        assert hasattr(RedmineSyncScheduler, 'sync_project')
        print("✅ scheduler 模块导入成功")
        test_results.append(True)
    except Exception as e:
        print(f"❌ scheduler 模块导入失败: {e}")
        test_results.append(False)

def test_warehouse_instantiation():
    """测试 warehouse 类实例化"""
    try:
        from redmine_mcp_server.redmine_warehouse import DataWarehouse
        # 创建实例（使用 mock 参数）
        warehouse = DataWarehouse()
        print("✅ warehouse 类实例化成功")
        test_results.append(True)
    except Exception as e:
        print(f"❌ warehouse 类实例化失败: {e}")
        test_results.append(False)

def test_scheduler_instantiation():
    """测试 scheduler 类实例化"""
    try:
        from redmine_mcp_server.redmine_scheduler import RedmineSyncScheduler
        # 创建实例（使用 mock 参数）
        scheduler = RedmineSyncScheduler(project_ids=[341])
        print("✅ scheduler 类实例化成功")
        test_results.append(True)
    except Exception as e:
        print(f"❌ scheduler 类实例化失败: {e}")
        test_results.append(False)

# 运行所有测试
test_warehouse_syntax()
test_scheduler_syntax()
test_main_syntax()
test_warehouse_import()
test_scheduler_import()
test_warehouse_instantiation()
test_scheduler_instantiation()

print("\n" + "=" * 60)
print("📊 测试结果汇总")
print("=" * 60)

test_names = [
    "warehouse 语法",
    "scheduler 语法", 
    "main 语法",
    "warehouse 导入",
    "scheduler 导入",
    "warehouse 实例化",
    "scheduler 实例化"
]

passed = 0
for i, (name, result) in enumerate(zip(test_names, test_results)):
    status = "✅ 通过" if result else "❌ 失败"
    print(f"{status} - {name}")
    if result:
        passed += 1

print(f"\n总计：{passed}/{len(test_results)} 通过")

if passed == len(test_results):
    print("\n🎉 所有测试通过！代码可以构建 Docker 镜像")
else:
    print(f"\n⚠️  {len(test_results) - passed} 个测试失败，请修复后再构建")
    sys.exit(1)