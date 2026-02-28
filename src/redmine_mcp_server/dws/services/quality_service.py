#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data质量监控

监控数仓data质量，包括：
- 表行数statistics
- data新鲜度
- datacomprehensive性
- exception检测
- 告警通知
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# databaseconfiguration
WAREHOUSE_DB_HOST = os.getenv("WAREHOUSE_DB_HOST", "warehouse-db")
WAREHOUSE_DB_PORT = os.getenv("WAREHOUSE_DB_PORT", "5432")
WAREHOUSE_DB_NAME = os.getenv("WAREHOUSE_DB_NAME", "redmine_warehouse")
WAREHOUSE_DB_USER = os.getenv("WAREHOUSE_DB_USER", "redmine_warehouse")
WAREHOUSE_DB_PASSWORD = os.getenv("WAREHOUSE_DB_PASSWORD")

import psycopg2
from psycopg2.extras import RealDictCursor


class DataQualityMonitor:
    """data质量监控器"""

    def __init__(self):
        self.conn = None
        self.cursor = None

        # 监控阈valueconfiguration
        self.thresholds = {
            "max_data_age_hours": 24,  # data最大年龄（小时）
            "min_row_count": {
                "ods_projects": 1,
                "ods_issues": 10,
                "dws_project_daily_summary": 10,
            },
            "null_rate_threshold": 0.1,  # 空value率阈value 10%
        }

    def connect_db(self):
        """connectiondatabase"""
        try:
            self.conn = psycopg2.connect(
                host=WAREHOUSE_DB_HOST,
                port=WAREHOUSE_DB_PORT,
                dbname=WAREHOUSE_DB_NAME,
                user=WAREHOUSE_DB_USER,
                password=WAREHOUSE_DB_PASSWORD,
                cursor_factory=RealDictCursor,
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connected for quality monitoring")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close_db(self):
        """shutdowndatabaseconnection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def get_table_row_counts(self) -> Dict[str, int]:
        """get所有表行数"""
        counts = {}

        tables = [
            "ods_projects",
            "ods_issues",
            "ods_journals",
            "ods_users",
            "dwd_issue_daily_snapshot",
            "dws_project_daily_summary",
            "dws_issue_contributors",
            "ads_project_health_report",
        ]

        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) as count FROM warehouse.{table}")
                result = self.cursor.fetchone()
                counts[table] = result["count"] if result else 0
            except Exception as e:
                logger.error(f"Failed to count {table}: {e}")
                counts[table] = -1

        return counts

    def check_data_freshness(self) -> Dict[str, Any]:
        """checkdata新鲜度"""
        freshness = {}

        # check各表最新datatime
        checks = {
            "ods_issues": "updated_on",
            "dwd_issue_daily_snapshot": "snapshot_date",
            "dws_project_daily_summary": "snapshot_date",
            "ads_project_health_report": "snapshot_date",
        }

        for table, date_column in checks.items():
            try:
                self.cursor.execute(f"""
                    SELECT MAX({date_column}) as max_date 
                    FROM warehouse.{table}
                """)
                result = self.cursor.fetchone()

                if result and result["max_date"]:
                    max_date = result["max_date"]
                    if isinstance(max_date, datetime):
                        age_hours = (datetime.now() - max_date).total_seconds() / 3600
                    else:
                        age_hours = (datetime.now().date() - max_date).days * 24

                    freshness[table] = {
                        "max_date": str(max_date),
                        "age_hours": round(age_hours, 2),
                        "status": (
                            "OK"
                            if age_hours < self.thresholds["max_data_age_hours"]
                            else "STALE"
                        ),
                    }
                else:
                    freshness[table] = {
                        "max_date": None,
                        "age_hours": None,
                        "status": "EMPTY",
                    }

            except Exception as e:
                logger.error(f"Failed to check freshness for {table}: {e}")
                freshness[table] = {"status": "ERROR", "error": str(e)}

        return freshness

    def check_data_completeness(self) -> Dict[str, Any]:
        """checkdatacomprehensive性"""
        completeness = {}

        # check关key字段的空value率
        checks = [
            ("ods_issues", "subject", "issue_id"),
            ("ods_issues", "project_id", "issue_id"),
            ("dwd_issue_daily_snapshot", "status_name", "issue_id"),
        ]

        for table, column, id_column in checks:
            try:
                self.cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT({column}) as not_null,
                        COUNT(*) - COUNT({column}) as null_count
                    FROM warehouse.{table}
                """)
                result = self.cursor.fetchone()

                if result:
                    total = result["total"]
                    null_count = result["null_count"]
                    null_rate = null_count / total if total > 0 else 0

                    completeness[f"{table}.{column}"] = {
                        "total": total,
                        "null_count": null_count,
                        "null_rate": round(null_rate, 4),
                        "status": (
                            "OK"
                            if null_rate < self.thresholds["null_rate_threshold"]
                            else "HIGH_NULL_RATE"
                        ),
                    }

            except Exception as e:
                logger.error(f"Failed to check completeness for {table}.{column}: {e}")

        return completeness

    def check_data_consistency(self) -> Dict[str, Any]:
        """checkdata一致性"""
        consistency = {}

        try:
            # check Issue 是否都有对应的project
            self.cursor.execute("""
                SELECT COUNT(*) as orphan_issues
                FROM warehouse.ods_issues i
                LEFT JOIN warehouse.ods_projects p ON i.project_id = p.project_id
                WHERE p.project_id IS NULL
            """)
            result = self.cursor.fetchone()
            orphan_count = result["orphan_issues"] if result else 0

            consistency["orphan_issues"] = {
                "count": orphan_count,
                "status": "OK" if orphan_count == 0 else "ISSUE",
            }

            # check快照date是否连续
            self.cursor.execute("""
                SELECT COUNT(DISTINCT snapshot_date) as unique_dates
                FROM warehouse.dws_project_daily_summary
                WHERE snapshot_date >= CURRENT_DATE - INTERVAL '30 days'
            """)
            result = self.cursor.fetchone()
            unique_dates = result["unique_dates"] if result else 0

            # 30 天内应该有接近 30 个不同的date
            consistency["snapshot_continuity"] = {
                "unique_dates_30d": unique_dates,
                "expected": 30,
                "status": "OK" if unique_dates >= 25 else "GAPS",
            }

        except Exception as e:
            logger.error(f"Failed to check consistency: {e}")
            consistency["error"] = str(e)

        return consistency

    def run_all_checks(self) -> Dict[str, Any]:
        """running所有质量check"""
        logger.info("Starting data quality checks...")

        self.connect_db()

        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "row_counts": self.get_table_row_counts(),
                "freshness": self.check_data_freshness(),
                "completeness": self.check_data_completeness(),
                "consistency": self.check_data_consistency(),
                "overall_status": "OK",
            }

            # 计算总体status
            issues = []

            # check行数
            for table, min_count in self.thresholds["min_row_count"].items():
                if table in results["row_counts"]:
                    if results["row_counts"][table] < min_count:
                        issues.append(
                            f"Low row count in {table}: {results['row_counts'][table]} < {min_count}"
                        )

            # check新鲜度
            for table, info in results["freshness"].items():
                if info.get("status") == "STALE":
                    issues.append(f"Stale data in {table}: {info.get('age_hours')}h")
                elif info.get("status") == "EMPTY":
                    issues.append(f"Empty table: {table}")

            # checkcomprehensive性
            for field, info in results["completeness"].items():
                if info.get("status") == "HIGH_NULL_RATE":
                    issues.append(f"High null rate in {field}: {info.get('null_rate')}")

            # check一致性
            for check, info in results["consistency"].items():
                if info.get("status") == "ISSUE" or info.get("status") == "GAPS":
                    issues.append(f"Consistency issue in {check}")

            if issues:
                results["overall_status"] = "ISSUES_FOUND"
                results["issues"] = issues
                logger.warning(f"Data quality issues found: {issues}")
            else:
                logger.info("All data quality checks passed")

            return results

        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "ERROR",
                "error": str(e),
            }
        finally:
            self.close_db()

    def save_quality_report(self, results: Dict[str, Any]):
        """save质量report到database"""
        self.connect_db()

        try:
            with self.cursor as cur:
                cur.execute(
                    """
                    INSERT INTO warehouse.data_quality_report (
                        report_timestamp, overall_status,
                        row_counts_json, freshness_json,
                        completeness_json, consistency_json,
                        issues_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        results["timestamp"],
                        results["overall_status"],
                        json.dumps(results.get("row_counts", {})),
                        json.dumps(results.get("freshness", {})),
                        json.dumps(results.get("completeness", {})),
                        json.dumps(results.get("consistency", {})),
                        json.dumps(results.get("issues", [])),
                    ),
                )

            self.conn.commit()
            logger.info("Quality report saved")

        except Exception as e:
            logger.error(f"Failed to save quality report: {e}")
            self.conn.rollback()
        finally:
            self.close_db()


# 质量report表（需要先create）
CREATE_QUALITY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS warehouse.data_quality_report (
    id BIGSERIAL PRIMARY KEY,
    report_timestamp TIMESTAMP NOT NULL,
    overall_status VARCHAR(20) NOT NULL,
    row_counts_json JSONB,
    freshness_json JSONB,
    completeness_json JSONB,
    consistency_json JSONB,
    issues_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_report_timestamp ON warehouse.data_quality_report(report_timestamp);
"""


def init_quality_monitor(db_pool):
    """initializedata质量监控"""
    from apscheduler.schedulers.background import BackgroundScheduler

    monitor = DataQualityMonitor()

    # create质量report表
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(CREATE_QUALITY_TABLE_SQL)
        conn.commit()
        db_pool.putconn(conn)
        logger.info("Quality report table created")
    except Exception as e:
        logger.error(f"Failed to create quality table: {e}")

    # createscheduler
    global quality_scheduler
    quality_scheduler = BackgroundScheduler()

    # 每日 8:00 running质量check
    quality_scheduler.add_job(
        func=lambda: monitor.save_quality_report(monitor.run_all_checks()),
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_quality_check",
        replace_existing=True,
    )

    quality_scheduler.start()
    logger.info("Data quality monitor initialized")

    return monitor


def shutdown_quality_monitor():
    """shutdown质量监控"""
    global quality_scheduler
    if quality_scheduler:
        quality_scheduler.shutdown()
        logger.info("Data quality monitor shutdown")


if __name__ == "__main__":
    # 手动runningtest
    monitor = DataQualityMonitor()
    results = monitor.run_all_checks()

    import json

    print(json.dumps(results, indent=2, ensure_ascii=False))
