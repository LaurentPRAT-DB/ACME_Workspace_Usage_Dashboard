# Account Monitor - Quick Reference Guide

## Quick Start Commands

### Check Data Availability
```sql
-- How many days of data do we have?
SELECT
  MIN(usage_date) as first_date,
  MAX(usage_date) as last_date,
  DATEDIFF(MAX(usage_date), MIN(usage_date)) as total_days
FROM system.billing.usage;
```

### Today's Spending
```sql
SELECT
  cloud_provider,
  ROUND(SUM(usage_metadata.total_price), 2) as today_cost,
  ROUND(SUM(usage_quantity), 2) as today_dbu
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE() - 1  -- Yesterday (most recent complete day)
GROUP BY cloud_provider;
```

### This Month's Spending
```sql
SELECT
  cloud_provider,
  COUNT(DISTINCT workspace_id) as workspaces,
  ROUND(SUM(usage_metadata.total_price), 2) as month_to_date_cost
FROM system.billing.usage
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
GROUP BY cloud_provider;
```

## Common Queries

### Find Expensive Workspaces
```sql
SELECT
  workspace_id,
  COUNT(DISTINCT usage_date) as active_days,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost,
  ROUND(AVG(usage_metadata.total_price), 2) as avg_daily_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id
ORDER BY total_cost DESC
LIMIT 10;
```

### Find Expensive SKUs
```sql
SELECT
  sku_name,
  cloud_provider,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost,
  COUNT(DISTINCT workspace_id) as used_in_workspaces
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY sku_name, cloud_provider
ORDER BY total_cost DESC
LIMIT 10;
```

### Weekend vs Weekday Usage
```sql
SELECT
  CASE DAYOFWEEK(usage_date)
    WHEN 1 THEN 'Sunday'
    WHEN 7 THEN 'Saturday'
    ELSE 'Weekday'
  END as day_type,
  ROUND(AVG(daily_cost), 2) as avg_cost
FROM (
  SELECT
    usage_date,
    SUM(usage_metadata.total_price) as daily_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
  GROUP BY usage_date
)
GROUP BY day_type;
```

### Compute vs. Other Costs
```sql
SELECT
  CASE
    WHEN sku_name LIKE '%ALL_PURPOSE%' OR sku_name LIKE '%JOBS%' THEN 'Compute'
    WHEN sku_name LIKE '%SQL%' THEN 'SQL'
    WHEN sku_name LIKE '%DLT%' THEN 'DLT'
    ELSE 'Other'
  END as category,
  ROUND(SUM(usage_metadata.total_price), 2) as cost,
  ROUND(SUM(usage_metadata.total_price) * 100.0 / SUM(SUM(usage_metadata.total_price)) OVER (), 1) as pct
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY category
ORDER BY cost DESC;
```

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
FROM account_monitoring.contracts
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
    SUM(u.usage_metadata.total_price) as spent
  FROM account_monitoring.contracts c
  LEFT JOIN system.billing.usage u
    ON c.account_id = u.account_id
    AND c.cloud_provider = u.cloud_provider
    AND u.usage_date BETWEEN c.start_date AND CURRENT_DATE()
  WHERE c.status = 'ACTIVE'
  GROUP BY c.contract_id, c.total_value, c.start_date, c.end_date
)
SELECT
  contract_id,
  total_value,
  spent,
  ROUND(spent * 100.0 / total_value, 1) as pct_consumed,
  ROUND(elapsed_days * 100.0 / total_days, 1) as pct_elapsed,
  CASE
    WHEN spent / total_value > elapsed_days / total_days THEN 'OVER PACE'
    WHEN spent / total_value < elapsed_days / total_days * 0.8 THEN 'UNDER PACE'
    ELSE 'ON PACE'
  END as consumption_status
FROM contract_spend;
```

### Project End Date Based on Current Rate
```sql
WITH daily_rate AS (
  SELECT
    c.contract_id,
    c.total_value,
    SUM(u.usage_metadata.total_price) / DATEDIFF(CURRENT_DATE(), c.start_date) as avg_daily_spend,
    SUM(u.usage_metadata.total_price) as spent_to_date
  FROM account_monitoring.contracts c
  LEFT JOIN system.billing.usage u
    ON c.account_id = u.account_id
    AND c.cloud_provider = u.cloud_provider
    AND u.usage_date BETWEEN c.start_date AND CURRENT_DATE()
  WHERE c.status = 'ACTIVE'
  GROUP BY c.contract_id, c.total_value, c.start_date
)
SELECT
  contract_id,
  total_value,
  spent_to_date,
  avg_daily_spend,
  DATE_ADD(CURRENT_DATE(),
    CAST((total_value - spent_to_date) / avg_daily_spend AS INT)
  ) as projected_end_date
FROM daily_rate;
```

## Cost Allocation

### By Custom Tag
```sql
SELECT
  custom_tags['team'] as team,
  custom_tags['project'] as project,
  ROUND(SUM(usage_metadata.total_price), 2) as cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND custom_tags IS NOT NULL
GROUP BY custom_tags['team'], custom_tags['project']
ORDER BY cost DESC;
```

### By Job ID
```sql
SELECT
  usage_metadata.job_id,
  COUNT(DISTINCT usage_date) as run_days,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND usage_metadata.job_id IS NOT NULL
GROUP BY usage_metadata.job_id
ORDER BY total_cost DESC
LIMIT 20;
```

### By SQL Warehouse
```sql
SELECT
  usage_metadata.warehouse_id,
  COUNT(DISTINCT usage_date) as active_days,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND usage_metadata.warehouse_id IS NOT NULL
GROUP BY usage_metadata.warehouse_id
ORDER BY total_cost DESC;
```

## Anomaly Detection

### Sudden Spikes (Day-over-Day)
```sql
WITH daily_costs AS (
  SELECT
    usage_date,
    workspace_id,
    SUM(usage_metadata.total_price) as daily_cost,
    LAG(SUM(usage_metadata.total_price)) OVER (
      PARTITION BY workspace_id
      ORDER BY usage_date
    ) as prev_day_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  GROUP BY usage_date, workspace_id
)
SELECT
  usage_date,
  workspace_id,
  ROUND(daily_cost, 2) as today_cost,
  ROUND(prev_day_cost, 2) as yesterday_cost,
  ROUND((daily_cost - prev_day_cost) / prev_day_cost * 100, 1) as pct_change
FROM daily_costs
WHERE prev_day_cost > 0
  AND (daily_cost - prev_day_cost) / prev_day_cost > 0.5  -- 50% increase
ORDER BY pct_change DESC
LIMIT 10;
```

### Unusual Weekend Activity
```sql
SELECT
  usage_date,
  workspace_id,
  DAYOFWEEK(usage_date) as day_of_week,
  ROUND(SUM(usage_metadata.total_price), 2) as cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND DAYOFWEEK(usage_date) IN (1, 7)  -- Saturday or Sunday
  AND usage_metadata.total_price > 100  -- Threshold
GROUP BY usage_date, workspace_id
ORDER BY cost DESC;
```

### New Workspaces (First-Time Usage)
```sql
WITH first_usage AS (
  SELECT
    workspace_id,
    MIN(usage_date) as first_seen
  FROM system.billing.usage
  GROUP BY workspace_id
)
SELECT
  u.workspace_id,
  f.first_seen,
  ROUND(SUM(u.usage_metadata.total_price), 2) as total_cost_since_creation,
  COUNT(DISTINCT u.usage_date) as active_days
FROM system.billing.usage u
JOIN first_usage f ON u.workspace_id = f.workspace_id
WHERE f.first_seen >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY u.workspace_id, f.first_seen
ORDER BY f.first_seen DESC;
```

## Forecasting

### Linear Projection (Next 30 Days)
```sql
WITH recent_avg AS (
  SELECT
    AVG(daily_cost) as avg_daily_cost
  FROM (
    SELECT
      usage_date,
      SUM(usage_metadata.total_price) as daily_cost
    FROM system.billing.usage
    WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
    GROUP BY usage_date
  )
)
SELECT
  ROUND(avg_daily_cost, 2) as avg_daily_cost,
  ROUND(avg_daily_cost * 30, 2) as projected_30_day_cost,
  ROUND(avg_daily_cost * 365, 2) as projected_annual_cost
FROM recent_avg;
```

### Trend Analysis (Growing or Shrinking)
```sql
WITH monthly_costs AS (
  SELECT
    DATE_TRUNC('MONTH', usage_date) as month,
    SUM(usage_metadata.total_price) as monthly_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
  GROUP BY DATE_TRUNC('MONTH', usage_date)
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

## Data Quality Checks

### Check for Missing Days
```sql
WITH date_range AS (
  SELECT
    EXPLODE(SEQUENCE(
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
SELECT
  dr.expected_date as missing_date
FROM date_range dr
LEFT JOIN actual_dates ad ON dr.expected_date = ad.usage_date
WHERE ad.usage_date IS NULL
ORDER BY missing_date;
```

### Check for Negative or Zero Costs
```sql
SELECT
  usage_date,
  workspace_id,
  sku_name,
  usage_quantity,
  usage_metadata.total_price
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND (usage_metadata.total_price <= 0 OR usage_quantity <= 0)
ORDER BY usage_date DESC;
```

## Performance Tips

1. **Always filter by date**: Use `usage_date >= DATE_SUB(CURRENT_DATE(), X)` in WHERE clause
2. **Use partitioning**: The usage table is partitioned by usage_date
3. **Aggregate first**: Use CTEs to aggregate before joining
4. **Limit large scans**: Use LIMIT when exploring data
5. **Cache frequently used data**: Create materialized views or cache results

## Common Patterns

### Aggregation Template
```sql
SELECT
  <dimension_columns>,
  COUNT(DISTINCT usage_date) as active_days,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost,
  ROUND(AVG(usage_metadata.total_price), 2) as avg_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), <days>)
  AND <additional_filters>
GROUP BY <dimension_columns>
ORDER BY total_cost DESC;
```

### Time Series Template
```sql
SELECT
  DATE_TRUNC('<DAY|WEEK|MONTH>', usage_date) as period,
  <dimension>,
  ROUND(SUM(usage_metadata.total_price), 2) as cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), <days>)
GROUP BY period, <dimension>
ORDER BY period DESC, cost DESC;
```

### Window Function Template
```sql
SELECT
  usage_date,
  <dimensions>,
  daily_cost,
  SUM(daily_cost) OVER (
    PARTITION BY <dimension>
    ORDER BY usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost,
  AVG(daily_cost) OVER (
    PARTITION BY <dimension>
    ORDER BY usage_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as rolling_7_day_avg
FROM (
  SELECT
    usage_date,
    <dimensions>,
    SUM(usage_metadata.total_price) as daily_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), <days>)
  GROUP BY usage_date, <dimensions>
);
```
