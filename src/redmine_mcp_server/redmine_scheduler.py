# /docker/redmine-mcp-server/src/redmine_mcp_server/scheduler.py
"""
定时同步调度器 - 只负责增量同步
不包含统计查询逻辑
"""

import os
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests

from .redmine_warehouse import DataWarehouse
from .redmine_handler import REDMINE_URL, REDMINE_API_KEY, logger


class RedmineSyncScheduler:
    """Redmine 增量同步调度器"""
    
    def __init__(self, project_ids: Optional[List[int]] = None, 
                 sync_interval_minutes: int = 10):
        """
        初始化调度器
        
        Args:
            project_ids: 要同步的项目 ID 列表
            sync_interval_minutes: 同步间隔（分钟）
        """
        env_projects = os.getenv("WAREHOUSE_PROJECT_IDS", "341,372")
        self.project_ids = project_ids or [int(p.strip()) for p in env_projects.split(',')]
        self.sync_interval_minutes = sync_interval_minutes
        self.warehouse: Optional[DataWarehouse] = None
        self.scheduler = BlockingScheduler()
        self._sync_count = 0
        
        logger.info(f"RedmineSyncScheduler initialized")
        logger.info(f"Projects: {self.project_ids}")
        logger.info(f"Sync interval: {self.sync_interval_minutes} minutes")
    
    def _init_warehouse(self):
        """延迟初始化数仓连接"""
        if self.warehouse is None:
            self.warehouse = DataWarehouse()
            logger.info("Warehouse connection initialized")
    
    def start(self):
        """启动调度器（在后台线程中运行）"""
        import threading
        
        try:
            self._init_warehouse()
            
            # 立即执行一次全量同步（在主线程中）
            logger.info("Running initial full sync...")
            self._sync_all_projects(full=True)
            
            # 添加定时任务
            self.scheduler.add_job(
                self._sync_all_projects,
                IntervalTrigger(minutes=self.sync_interval_minutes),
                id='incremental_sync',
                name=f'Incremental Redmine Sync (every {self.sync_interval_minutes} min)',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=60
            )
            
            # 在后台线程中启动调度器
            def run_scheduler():
                self.scheduler.run_forever()
            
            thread = threading.Thread(target=run_scheduler, daemon=True)
            thread.start()
            
            logger.info(f"Scheduler started in background thread")
            logger.info(f"Next sync in {self.sync_interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
        
        if self.warehouse:
            self.warehouse.close()
            logger.info("Warehouse connection closed")
    
    def _sync_all_projects(self, full: bool = False):
        """
        同步所有项目
        
        Args:
            full: 是否全量同步
        """
        logger.info(f"Starting {'full' if full else 'incremental'} sync for {len(self.project_ids)} projects...")
        
        sync_results = {}
        for project_id in self.project_ids:
            try:
                count = self._sync_project(project_id, incremental=not full)
                sync_results[project_id] = {'status': 'success', 'count': count}
            except Exception as e:
                logger.error(f"Failed to sync project {project_id}: {e}")
                sync_results[project_id] = {'status': 'error', 'error': str(e)}
        
        self._sync_count += 1
        logger.info(f"Sync completed (run #{self._sync_count})")
        logger.info(f"Results: {sync_results}")
    
    def _sync_project(self, project_id: int, incremental: bool = True) -> int:
        """
        同步单个项目
        
        Args:
            project_id: 项目 ID
            incremental: 是否增量同步
        
        Returns:
            同步的 Issue 数量
        """
        if not self.warehouse:
            self._init_warehouse()
        
        api_url = f"{REDMINE_URL}/issues.json"
        headers = {"X-Redmine-API-Key": REDMINE_API_KEY}
        
        all_issues: List[Dict[str, Any]] = []
        offset = 0
        limit = 100
        
        # 构建查询参数
        params = {'project_id': project_id, 'limit': limit, 'offset': offset}
        
        if incremental:
            # 增量同步：只获取最近更新的 Issue
            since = datetime.now() - timedelta(minutes=self.sync_interval_minutes + 5)
            params['updated_on'] = f'>={since.strftime("%Y-%m-%d %H:%M:%S")}'
            logger.info(f"Incremental sync for project {project_id} since {since}")
        
        # 分页获取
        while True:
            try:
                resp = requests.get(api_url, headers=headers, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                issues = data.get('issues', [])
                all_issues.extend(issues)
                
                if len(issues) < limit:
                    break
                
                offset += limit
                logger.debug(f"Fetched {len(all_issues)} issues for project {project_id}...")
                
            except Exception as e:
                logger.error(f"Failed to fetch issues: {e}")
                break
        
        if all_issues:
            # 获取昨天的快照用于对比
            yesterday = datetime.now().date() - timedelta(days=1)
            previous_issues = self.warehouse.get_issues_snapshot(project_id, yesterday)
            previous_map = {i['issue_id']: i for i in previous_issues}
            
            # 批量同步到数仓
            self.warehouse.upsert_issues_batch(project_id, all_issues, 
                                               datetime.now().date(), 
                                               previous_map)
            
            logger.info(f"Synced {len(all_issues)} issues for project {project_id}")
            return len(all_issues)
        else:
            logger.info(f"No issues to sync for project {project_id}")
            return 0
    
    def get_sync_status(self) -> dict:
        """获取同步状态"""
        next_run = None
        if self.scheduler.running:
            job = self.scheduler.get_job('incremental_sync')
            if job:
                next_run = job.next_run_time.isoformat() if job.next_run_time else None
        
        return {
            'running': self.scheduler.running,
            'projects': self.project_ids,
            'interval_minutes': self.sync_interval_minutes,
            'next_run': next_run,
            'sync_count': self._sync_count,
            'warehouse_connected': self.warehouse is not None
        }


# ========== 全局调度器实例 ==========

_scheduler: Optional[RedmineSyncScheduler] = None

def get_scheduler() -> Optional[RedmineSyncScheduler]:
    """获取全局调度器实例"""
    return _scheduler

def init_scheduler(project_ids: Optional[List[int]] = None, 
                   sync_interval_minutes: int = 10) -> RedmineSyncScheduler:
    """初始化并启动调度器"""
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already initialized")
        return _scheduler
    
    sync_interval_minutes = int(os.getenv(
        "WAREHOUSE_SYNC_INTERVAL_MINUTES", 
        str(sync_interval_minutes)
    ))
    
    _scheduler = RedmineSyncScheduler(
        project_ids=project_ids, 
        sync_interval_minutes=sync_interval_minutes
    )
    _scheduler.start()
    
    return _scheduler

def shutdown_scheduler():
    """关闭调度器"""
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
        logger.info("Scheduler shutdown complete")
