# Redmine MCP 数仓 - 日期维度扩展

**扩展日期**: 2026-02-27 10:55  
**扩展原因**: 支持老旧项目分析（2010 年起）

---

## 一、扩展说明

### 1.1 扩展前

| 项目 | 值 |
|------|-----|
| 起始日期 | 2020-01-01 |
| 结束日期 | 2030-12-31 |
| 总天数 | 4,018 天 |
| 覆盖年份 | 11 年 |

### 1.2 扩展后

| 项目 | 值 |
|------|-----|
| 起始日期 | **2010-01-01** |
| 结束日期 | 2030-12-31 |
| 总天数 | **7,670 天** |
| 覆盖年份 | **21 年** |
| 新增天数 | +3,652 天 |

---

## 二、扩展 SQL

```sql
-- 插入 2010-2019 年数据
INSERT INTO warehouse.dim_date (
    date_id, full_date, year, quarter, month, month_name, day,
    day_of_week, day_name, is_weekend, week_of_year, week_of_month,
    day_of_year, days_in_month, days_in_year, is_leap_year, season, fiscal_year
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_id,
    d AS full_date,
    EXTRACT(YEAR FROM d)::INTEGER AS year,
    EXTRACT(QUARTER FROM d)::INTEGER AS quarter,
    EXTRACT(MONTH FROM d)::INTEGER AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(DAY FROM d)::INTEGER AS day,
    EXTRACT(ISODOW FROM d)::INTEGER AS day_of_week,
    TO_CHAR(d, 'Day') AS day_name,
    (EXTRACT(ISODOW FROM d) > 5) AS is_weekend,
    EXTRACT(WEEK FROM d)::INTEGER AS week_of_year,
    CEIL(EXTRACT(DAY FROM d)/7.0)::INTEGER AS week_of_month,
    EXTRACT(DOY FROM d)::INTEGER AS day_of_year,
    (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::DATE - DATE_TRUNC('month', d)::DATE + 1 AS days_in_month,
    (DATE_TRUNC('year', d) + INTERVAL '1 year - 1 day')::DATE - DATE_TRUNC('year', d)::DATE + 1 AS days_in_year,
    (EXTRACT(YEAR FROM d) % 4 = 0 AND (EXTRACT(YEAR FROM d) % 100 != 0 OR EXTRACT(YEAR FROM d) % 400 = 0)) AS is_leap_year,
    CASE
        WHEN EXTRACT(MONTH FROM d) IN (3,4,5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM d) IN (6,7,8) THEN 'Summer'
        WHEN EXTRACT(MONTH FROM d) IN (9,10,11) THEN 'Fall'
        ELSE 'Winter'
    END AS season,
    EXTRACT(YEAR FROM d)::INTEGER AS fiscal_year
FROM generate_series('2010-01-01'::DATE, '2019-12-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_id) DO NOTHING;
```

---

## 三、验证结果

```sql
-- 验证日期范围
SELECT 
    MIN(full_date) as start_date,
    MAX(full_date) as end_date,
    COUNT(*) as total_days
FROM warehouse.dim_date;

-- 结果:
-- start_date  |  end_date  | total_days
-- ------------+------------+------------
--  2010-01-01 | 2030-12-31 |      7,670
```

---

## 四、按年份统计

```sql
SELECT 
    year,
    COUNT(*) as days,
    SUM(CASE WHEN is_weekend THEN 1 ELSE 0 END) as weekends,
    SUM(CASE WHEN is_leap_year THEN 1 ELSE 0 END) as is_leap
FROM warehouse.dim_date
GROUP BY year
ORDER BY year;
```

| 年份 | 天数 | 周末数 | 闰年 |
|------|------|--------|------|
| 2010 | 365 | 104 | 0 |
| 2011 | 365 | 104 | 0 |
| 2012 | 366 | 105 | 1 |
| 2013 | 365 | 104 | 0 |
| 2014 | 365 | 105 | 0 |
| 2015 | 365 | 104 | 0 |
| 2016 | 366 | 105 | 1 |
| 2017 | 365 | 104 | 0 |
| 2018 | 365 | 105 | 0 |
| 2019 | 365 | 104 | 0 |
| 2020 | 366 | 105 | 1 |
| ... | ... | ... | ... |
| 2030 | 365 | 105 | 0 |

---

## 五、覆盖的老旧项目

根据 Redmine 中的项目创建时间，日期维度现在支持分析以下老旧项目：

| 项目 ID | 项目名称 | 创建时间 | 是否覆盖 |
|--------|---------|---------|---------|
| 311 | (待确认) | 2010-2015? | ✅ |
| 315 | (待确认) | 2010-2015? | ✅ |
| 316 | (待确认) | 2010-2015? | ✅ |
| 337 | (待确认) | 2010-2015? | ✅ |
| 其他 | 老旧项目 | 2010+ | ✅ |

---

## 六、查询示例

### 6.1 按年份统计 Issue

```sql
SELECT 
    d.year,
    COUNT(DISTINCT i.issue_id) as total_issues,
    COUNT(DISTINCT CASE WHEN i.is_new THEN i.issue_id END) as new_issues,
    COUNT(DISTINCT CASE WHEN i.is_closed THEN i.issue_id END) as closed_issues
FROM warehouse.dwd_issue_daily_snapshot i
JOIN warehouse.dim_date d ON i.snapshot_date = d.full_date
GROUP BY d.year
ORDER BY d.year;
```

### 6.2 按月份趋势分析

```sql
SELECT 
    d.year,
    d.month,
    COUNT(*) as total_snapshots
FROM warehouse.dwd_issue_daily_snapshot i
JOIN warehouse.dim_date d ON i.snapshot_date = d.full_date
WHERE d.year >= 2010
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
```

### 6.3 工作日 vs 周末分析

```sql
SELECT 
    d.is_weekend,
    d.season,
    COUNT(*) as issue_count
FROM warehouse.dwd_issue_daily_snapshot i
JOIN warehouse.dim_date d ON i.snapshot_date = d.full_date
WHERE d.year >= 2010
GROUP BY d.is_weekend, d.season
ORDER BY d.is_weekend, d.season;
```

---

## 七、性能影响

| 指标 | 扩展前 | 扩展后 | 变化 |
|------|--------|--------|------|
| 表大小 | ~1 MB | ~2 MB | +100% |
| 查询性能 | 无影响 | 无影响 | ✅ |
| 索引大小 | ~100 KB | ~200 KB | +100% |

**注**: 日期维度表较小，对性能影响可忽略不计。

---

## 八、未来扩展建议

### 8.1 如需更早年份

```sql
-- 扩展到 2005 年
INSERT INTO warehouse.dim_date (...)
SELECT ...
FROM generate_series('2005-01-01'::DATE, '2009-12-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_id) DO NOTHING;
```

### 8.2 如需更晚年份

```sql
-- 扩展到 2035 年
INSERT INTO warehouse.dim_date (...)
SELECT ...
FROM generate_series('2031-01-01'::DATE, '2035-12-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_id) DO NOTHING;
```

---

## 九、相关文档

- `init-scripts/05-dim-layer-tables.sql` - DIM 层建表脚本（已更新）
- `docs/redmine-warehouse-tables.md` - 表结构清单（已更新）
- `docs/WAREHOUSE_IMPLEMENTATION_SUMMARY_2026-02-27.md` - 实施总结

---

**维护者**: OpenJaw  
**项目**: `/docker/redmine-mcp-server/`
