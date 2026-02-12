# Account Monitor - Quick Reference Guide

> **Note**: Cost calculation requires joining `system.billing.usage` with `system.billing.list_prices`. There is no `usage_metadata.total_price` column.

## Cost Calculation Pattern

All cost queries must use this JOIN pattern:

```sql
SELECT
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.record_type = 'ORIGINAL'
```

---

## Quick Start Commands

### Check Data Availability
```sql
SELECT
  MIN(usage_date) as first_date,
  MAX(usage_date) as last_date,
  DATEDIFF(MAX(usage_date), MIN(usage_date)) as total_days
FROM system.billing.usage;
```

### Yesterday's Spending
```sql
SELECT
  u.cloud,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as cost,
  ROUND(SUM(u.usage_quantity), 2) as dbu
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL'
GROUP BY u.cloud;
```

### Month-to-Date Spending
```sql
SELECT
  u.cloud,
  COUNT(DISTINCT u.workspace_id) as workspaces,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as mtd_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
  AND u.record_type = 'ORIGINAL'
GROUP BY u.cloud;
```

---

## Common Queries

### Find Expensive Workspaces
```sql
SELECT
  u.workspace_id,
  COUNT(DISTINCT u.usage_date) as active_days,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.workspace_id
ORDER BY total_cost DESC
LIMIT 10;
```

### Find Expensive SKUs
```sql
SELECT
  u.sku_name,
  u.cloud,
  ROUND(SUM(u.usage_quantity), 2) as total_dbu,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as total_cost,
  COUNT(DISTINCT u.workspace_id) as used_in_workspaces
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.sku_name, u.cloud
ORDER BY total_cost DESC
LIMIT 10;
```

### Weekend vs Weekday Usage
```sql
WITH daily_costs AS (
  SELECT
    u.usage_date,
    SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
    AND u.record_type = 'ORIGINAL'
  GROUP BY u.usage_date
)
SELECT
  CASE DAYOFWEEK(usage_date)
    WHEN 1 THEN 'Sunday'
    WHEN 7 THEN 'Saturday'
    ELSE 'Weekday'
  END as day_type,
  ROUND(AVG(daily_cost), 2) as avg_cost
FROM daily_costs
GROUP BY day_type;
```

### Compute vs. Other Costs
```sql
WITH categorized AS (
  SELECT
    CASE
      WHEN u.sku_name LIKE '%ALL_PURPOSE%' OR u.sku_name LIKE '%JOBS%' THEN 'Compute'
      WHEN u.sku_name LIKE '%SQL%' THEN 'SQL'
      WHEN u.sku_name LIKE '%DLT%' THEN 'DLT'
      ELSE 'Other'
    END as category,
    u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)) as cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
    AND u.record_type = 'ORIGINAL'
)
SELECT
  category,
  ROUND(SUM(cost), 2) as cost,
  ROUND(SUM(cost) * 100.0 / SUM(SUM(cost)) OVER (), 1) as pct
FROM categorized
GROUP BY category
ORDER BY cost DESC;
```

---

## Contract Management

### Check Contract Status
```sql
SELECT
  contract_id,
  cloud_provider,
  total_value,
  start_date,
  end_date,
  DATEDIFF(end_date, CURRENT_DATE()) as days_remaining
FROM main.account_monitoring.contracts
WHERE status = 'ACTIVE'
  AND end_date > CURRENT_DATE()
ORDER BY days_remaining;
```

### Contract Consumption Rate
```sql
WITH contract_spend AS (
  SELECT
    c.contract_id,
    c.total_value,
    c.start_date,
    c.end_date,
    DATEDIFF(c.end_date, c.start_date) as total_days,
    DATEDIFF(CURRENT_DATE(), c.start_date) as elapsed_days,
    SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as spent
  FROM main.account_monitoring.contracts c
  LEFT JOIN system.billing.usage u
    ON c.account_id = u.account_id
    AND c.cloud_provider = u.cloud
    AND u.usage_date BETWEEN c.start_date AND CURRENT_DATE()
    AND u.record_type = 'ORIGINAL'
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE c.status = 'ACTIVE'
  GROUP BY c.contract_id, c.total_value, c.start_date, c.end_date
)
SELECT
  contract_id,
  total_value,
  ROUND(spent, 2) as spent,
  ROUND(spent * 100.0 / total_value, 1) as pct_consumed,
  ROUND(elapsed_days * 100.0 / total_days, 1) as pct_elapsed,
  CASE
    WHEN spent / total_value > elapsed_days / total_days THEN 'OVER PACE'
    WHEN spent / total_value < elapsed_days / total_days * 0.8 THEN 'UNDER PACE'
    ELSE 'ON PACE'
  END as consumption_status
FROM contract_spend;
```

---

## Anomaly Detection

### Sudden Spikes (Day-over-Day)
```sql
WITH daily_costs AS (
  SELECT
    u.usage_date,
    u.workspace_id,
    SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
    AND u.record_type = 'ORIGINAL'
  GROUP BY u.usage_date, u.workspace_id
),
with_lag AS (
  SELECT
    usage_date,
    workspace_id,
    daily_cost,
    LAG(daily_cost) OVER (PARTITION BY workspace_id ORDER BY usage_date) as prev_day_cost
  FROM daily_costs
)
SELECT
  usage_date,
  workspace_id,
  ROUND(daily_cost, 2) as today_cost,
  ROUND(prev_day_cost, 2) as yesterday_cost,
  ROUND((daily_cost - prev_day_cost) / prev_day_cost * 100, 1) as pct_change
FROM with_lag
WHERE prev_day_cost > 0
  AND (daily_cost - prev_day_cost) / prev_day_cost > 0.5  -- 50% increase
ORDER BY pct_change DESC
LIMIT 10;
```

### New Workspaces (First-Time Usage)
```sql
WITH first_usage AS (
  SELECT
    workspace_id,
    MIN(usage_date) as first_seen
  FROM system.billing.usage
  GROUP BY workspace_id
),
workspace_costs AS (
  SELECT
    u.workspace_id,
    f.first_seen,
    SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost,
    COUNT(DISTINCT u.usage_date) as active_days
  FROM system.billing.usage u
  JOIN first_usage f ON u.workspace_id = f.workspace_id
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE f.first_seen >= DATE_SUB(CURRENT_DATE(), 30)
    AND u.record_type = 'ORIGINAL'
  GROUP BY u.workspace_id, f.first_seen
)
SELECT
  workspace_id,
  first_seen,
  ROUND(total_cost, 2) as total_cost_since_creation,
  active_days
FROM workspace_costs
ORDER BY first_seen DESC;
```

---

## Forecasting

### Linear Projection (Next 30 Days)
```sql
WITH daily_costs AS (
  SELECT
    u.usage_date,
    SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
    AND u.record_type = 'ORIGINAL'
  GROUP BY u.usage_date
),
avg_cost AS (
  SELECT AVG(daily_cost) as avg_daily_cost FROM daily_costs
)
SELECT
  ROUND(avg_daily_cost, 2) as avg_daily_cost,
  ROUND(avg_daily_cost * 30, 2) as projected_30_day_cost,
  ROUND(avg_daily_cost * 365, 2) as projected_annual_cost
FROM avg_cost;
```

### Monthly Trend Analysis
```sql
WITH monthly_costs AS (
  SELECT
    DATE_TRUNC('MONTH', u.usage_date) as month,
    SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as monthly_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 180)
    AND u.record_type = 'ORIGINAL'
  GROUP BY DATE_TRUNC('MONTH', u.usage_date)
),
lagged AS (
  SELECT
    month,
    monthly_cost,
    LAG(monthly_cost) OVER (ORDER BY month) as prev_month_cost
  FROM monthly_costs
)
SELECT
  month,
  ROUND(monthly_cost, 2) as cost,
  ROUND(prev_month_cost, 2) as prev_cost,
  ROUND((monthly_cost - prev_month_cost) / prev_month_cost * 100, 1) as month_over_month_pct
FROM lagged
WHERE prev_month_cost IS NOT NULL
ORDER BY month DESC;
```

---

## Data Quality Checks

### Check for Missing Days
```sql
WITH date_range AS (
  SELECT EXPLODE(SEQUENCE(
    DATE_SUB(CURRENT_DATE(), 30),
    CURRENT_DATE() - 1,
    INTERVAL 1 DAY
  )) as expected_date
),
actual_dates AS (
  SELECT DISTINCT usage_date
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
)
SELECT dr.expected_date as missing_date
FROM date_range dr
LEFT JOIN actual_dates ad ON dr.expected_date = ad.usage_date
WHERE ad.usage_date IS NULL
ORDER BY missing_date;
```

### Data Freshness
```sql
SELECT
  MAX(usage_date) as latest_date,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind
FROM system.billing.usage;
```

---

## Performance Tips

1. **Always filter by date**: Use `usage_date >= DATE_SUB(CURRENT_DATE(), X)` in WHERE clause
2. **Filter by record_type**: Use `record_type = 'ORIGINAL'` to exclude corrections
3. **Use CTEs**: Aggregate usage data first, then join with list_prices
4. **Limit large scans**: Use LIMIT when exploring data
5. **Cache results**: Create views for frequently used queries

---

## Common Patterns

### Cost Aggregation Template
```sql
SELECT
  <dimension_columns>,
  COUNT(DISTINCT u.usage_date) as active_days,
  ROUND(SUM(u.usage_quantity), 2) as total_dbu,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), <days>)
  AND u.record_type = 'ORIGINAL'
  AND <additional_filters>
GROUP BY <dimension_columns>
ORDER BY total_cost DESC;
```

### Time Series Template
```sql
SELECT
  DATE_TRUNC('<DAY|WEEK|MONTH>', u.usage_date) as period,
  <dimension>,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), <days>)
  AND u.record_type = 'ORIGINAL'
GROUP BY period, <dimension>
ORDER BY period DESC, cost DESC;
```

---

**Version**: 2.0 (Schema Corrected)
**Last Updated**: 2026-02-12
