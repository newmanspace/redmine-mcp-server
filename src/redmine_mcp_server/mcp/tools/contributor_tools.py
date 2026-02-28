#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP Tools
"""

from ..server import mcp, redmine, logger
from typing import Dict, Any, List, Optional, Union


@mcp.tool()
async def get_project_role_distribution(
    project_id: int, date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get project role distribution

    Args:
        project_id: project_id
        date: 日期（YYYY-MM-DD），默认今天

    Returns:
        各角色report for人员数量
    """
    from datetime import date as date_class
    from .redmine_warehouse import DataWarehouse
    from .dev_test_analyzer import DevTestAnalyzer

    try:
        warehouse = DataWarehouse()
        query_date = (
            datetime.strptime(date, "%Y-%m-%d").date() if date else date_class.today()
        )

        # 查询数仓
        distribution = warehouse.get_project_role_distribution(project_id, query_date)

        if not distribution:
            # 如果没有，触发计算
            logger.info(
                f"No role distribution for {project_id} on {query_date}, calculating..."
            )

            if redmine:
                analyzer = DevTestAnalyzer()
                try:
                    # Get project members and their roles
                    roles_data = analyzer.get_project_member_roles(project_id)

                    if roles_data:
                        # Save to warehouse
                        warehouse.upsert_user_project_roles(project_id, roles_data)
                        warehouse.refresh_project_role_distribution(
                            project_id, query_date
                        )
                        distribution = warehouse.get_project_role_distribution(
                            project_id, query_date
                        )
                except Exception as e:
                    logger.error(f"Failed to calculate from Redmine: {e}")

            if not distribution:
                warehouse.close()
                return {
                    "project_id": project_id,
                    "date": query_date.isoformat(),
                    "message": "Role distribution not yet calculated. Trigger a sync to populate data.",
                }

        warehouse.close()
        return dict(distribution)

    except Exception as e:
        logger.error(f"Failed to get role distribution: {e}")
        return {"error": f"Failed to get role distribution: {str(e)}"}


@mcp.tool()
async def get_user_workload(
    user_id: int, year_month: Optional[str] = None, project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get user workload statistics

    Args:
        user_id: user_id
        year_month: 年月（YYYY-MM），默认本月
        project_id: project_id(optional)

    Returns:
        工作量统计信息
    """
    from datetime import datetime
    from .redmine_warehouse import DataWarehouse

    if not year_month:
        year_month = datetime.now().strftime("%Y-%m")

    try:
        warehouse = DataWarehouse()

        # 查询数仓
        workload_data = warehouse.get_user_workload(user_id, year_month, project_id)

        warehouse.close()

        if workload_data:
            if project_id:
                return {
                    "user_id": user_id,
                    "year_month": year_month,
                    "project_id": project_id,
                    "workload": workload_data[0] if workload_data else None,
                }
            else:
                return {
                    "user_id": user_id,
                    "year_month": year_month,
                    "projects": workload_data,
                }

        return {
            "user_id": user_id,
            "year_month": year_month,
            "message": "No workload data yet. Contributor analysis needs to be run first.",
        }

    except Exception as e:
        logger.error(f"Failed to get workload: {e}")
        return {"error": f"Failed to get workload: {str(e)}"}
