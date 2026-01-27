# Account Monitor - Operations Guide

## Daily Operations

### Morning Checklist

1. **Check Data Freshness**
```sql
SELECT
  'system.billing.usage' as table_name,
  MAX(usage_date) as latest_data,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN '✓ OK'
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 5 THEN '⚠ WARNING'
    ELSE '✗ CRITICAL'
  END as status
FROM system.billing.usage;
```

2. **Yesterday's Total Spend**
```sql
SELECT
  CURRENT_DATE() - 1 as date,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces,
  COUNT(DISTINCT sku_name) as unique_skus
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE() - 1;
```

3. **Check for Anomalies**
```sql
-- Large day-over-day increases
WITH daily AS (
  SELECT
    usage_date,
    SUM(usage_metadata.total_price) as daily_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
  GROUP BY usage_date
)
SELECT
  usage_date,
  ROUND(daily_cost, 2) as cost,
  ROUND(daily_cost - LAG(daily_cost) OVER (ORDER BY usage_date), 2) as change,
  ROUND((daily_cost - LAG(daily_cost) OVER (ORDER BY usage_date)) /
        LAG(daily_cost) OVER (ORDER BY usage_date) * 100, 1) as pct_change
FROM daily
ORDER BY usage_date DESC;
```

### Weekly Review

Run every Monday morning:

```sql
-- Last week's summary
SELECT
  'Last Week' as period,
  COUNT(DISTINCT usage_date) as days_with_data,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost,
  ROUND(AVG(daily_cost), 2) as avg_daily_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces
FROM (
  SELECT
    usage_date,
    workspace_id,
    SUM(usage_metadata.total_price) as daily_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
    AND usage_date < CURRENT_DATE()
  GROUP BY usage_date, workspace_id
);

-- Top 5 workspaces last week
SELECT
  workspace_id,
  ROUND(SUM(usage_metadata.total_price), 2) as weekly_cost,
  COUNT(DISTINCT usage_date) as active_days
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
  AND usage_date < CURRENT_DATE()
GROUP BY workspace_id
ORDER BY weekly_cost DESC
LIMIT 5;

-- New workspaces this week
SELECT
  workspace_id,
  MIN(usage_date) as first_seen
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
GROUP BY workspace_id
HAVING MIN(usage_date) >= DATE_SUB(CURRENT_DATE(), 7);
```

### Monthly Review

Run on the 1st of each month:

```sql
-- Previous month summary
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  COUNT(DISTINCT usage_date) as days_with_data,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost,
  ROUND(AVG(daily_cost), 2) as avg_daily_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces,
  COUNT(DISTINCT sku_name) as unique_skus
FROM (
  SELECT
    usage_date,
    workspace_id,
    SUM(usage_metadata.total_price) as daily_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_TRUNC('MONTH', DATE_SUB(CURRENT_DATE(), 30))
    AND usage_date < DATE_TRUNC('MONTH', CURRENT_DATE())
  GROUP BY usage_date, workspace_id
)
GROUP BY DATE_TRUNC('MONTH', usage_date);

-- Month-over-month comparison
WITH monthly AS (
  SELECT
    DATE_TRUNC('MONTH', usage_date) as month,
    SUM(usage_metadata.total_price) as monthly_cost
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
  GROUP BY DATE_TRUNC('MONTH', usage_date)
)
SELECT
  month,
  ROUND(monthly_cost, 2) as cost,
  ROUND(LAG(monthly_cost) OVER (ORDER BY month), 2) as prev_month_cost,
  ROUND((monthly_cost - LAG(monthly_cost) OVER (ORDER BY month)) /
        LAG(monthly_cost) OVER (ORDER BY month) * 100, 1) as mom_pct_change
FROM monthly
ORDER BY month DESC
LIMIT 3;
```

## Maintenance Tasks

### Weekly Maintenance

#### 1. Update Contract Information
```sql
-- Check for contracts expiring soon
SELECT
  contract_id,
  end_date,
  DATEDIFF(end_date, CURRENT_DATE()) as days_until_expiration
FROM account_monitoring.contracts
WHERE status = 'ACTIVE'
  AND DATEDIFF(end_date, CURRENT_DATE()) <= 90
ORDER BY end_date;

-- Update contract status for expired contracts
UPDATE account_monitoring.contracts
SET
  status = 'EXPIRED',
  updated_at = CURRENT_TIMESTAMP()
WHERE end_date < CURRENT_DATE()
  AND status = 'ACTIVE';
```

#### 2. Refresh Dashboard Data
```sql
-- Run this weekly or set up as a scheduled job
CREATE OR REPLACE TABLE account_monitoring.dashboard_data AS
SELECT
  u.usage_date,
  u.account_id,
  am.customer_name,
  am.salesforce_id,
  am.business_unit_l0,
  am.business_unit_l1,
  am.business_unit_l2,
  am.business_unit_l3,
  am.account_executive,
  am.solutions_architect,
  u.workspace_id,
  u.cloud_provider,
  u.sku_name,
  u.usage_unit,
  u.usage_quantity,
  COALESCE(u.usage_metadata.total_price, 0) as actual_cost,
  u.list_price_per_unit,
  lp.pricing.default_price_per_unit as discounted_price_per_unit,
  u.usage_quantity * u.list_price_per_unit as list_cost,
  u.usage_quantity * COALESCE(lp.pricing.default_price_per_unit, 0) as discounted_cost,
  CASE
    WHEN u.sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
    WHEN u.sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
    WHEN u.sku_name LIKE '%DLT%' THEN 'Delta Live Tables'
    WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
    WHEN u.sku_name LIKE '%INFERENCE%' OR u.sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
    ELSE 'Other'
  END as product_category,
  CURRENT_TIMESTAMP() as updated_at
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud_provider = lp.cloud
  AND u.usage_date >= lp.price_start_time
  AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
LEFT JOIN account_monitoring.account_metadata am
  ON u.account_id = am.account_id
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365);

-- Optimize table
OPTIMIZE account_monitoring.dashboard_data
ZORDER BY (usage_date, workspace_id);
```

#### 3. Validate Data Integrity
```sql
-- Check for missing data
WITH date_range AS (
  SELECT EXPLODE(SEQUENCE(
    DATE_SUB(CURRENT_DATE(), 30),
    CURRENT_DATE() - 1,
    INTERVAL 1 DAY
  )) as expected_date
)
SELECT
  dr.expected_date as missing_date,
  'No usage data' as issue
FROM date_range dr
LEFT JOIN (
  SELECT DISTINCT usage_date
  FROM system.billing.usage
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
) u ON dr.expected_date = u.usage_date
WHERE u.usage_date IS NULL;

-- Check for suspicious data
SELECT
  usage_date,
  workspace_id,
  sku_name,
  usage_quantity,
  usage_metadata.total_price,
  'Negative or zero cost' as issue
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND (usage_metadata.total_price <= 0 OR usage_quantity <= 0);
```

### Monthly Maintenance

#### 1. Archive Old Data
```sql
-- Create archive table if it doesn't exist
CREATE TABLE IF NOT EXISTS account_monitoring.dashboard_data_archive
LIKE account_monitoring.dashboard_data;

-- Archive data older than 2 years
INSERT INTO account_monitoring.dashboard_data_archive
SELECT * FROM account_monitoring.dashboard_data
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- Delete archived data from main table
DELETE FROM account_monitoring.dashboard_data
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- Vacuum to reclaim space
VACUUM account_monitoring.dashboard_data RETAIN 168 HOURS;
```

#### 2. Update Account Metadata
```sql
-- Review and update team assignments
SELECT
  account_id,
  customer_name,
  account_executive,
  solutions_architect,
  updated_at
FROM account_monitoring.account_metadata
WHERE updated_at < DATE_SUB(CURRENT_DATE(), 90)
ORDER BY updated_at;

-- Update metadata (example)
UPDATE account_monitoring.account_metadata
SET
  account_executive = 'New AE Name',
  updated_at = CURRENT_TIMESTAMP()
WHERE account_id = 'account-001';
```

#### 3. Review Contract Consumption
```sql
-- Contracts at risk of overrun
WITH contract_pace AS (
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
  ROUND(spent, 2) as spent,
  ROUND(total_value, 2) as total_value,
  ROUND(spent * 100.0 / total_value, 1) as pct_consumed,
  ROUND(elapsed_days * 100.0 / total_days, 1) as pct_elapsed,
  CASE
    WHEN spent / total_value > elapsed_days / total_days * 1.2 THEN '🔴 OVERRUN RISK'
    WHEN spent / total_value > elapsed_days / total_days * 1.1 THEN '🟡 MONITOR'
    ELSE '🟢 ON TRACK'
  END as status
FROM contract_pace
ORDER BY (spent / total_value) / (elapsed_days / total_days) DESC;
```

## Alerting

### Set Up Alerts

#### High Daily Spend Alert
```sql
-- Alert if daily spend exceeds threshold
WITH yesterday_spend AS (
  SELECT SUM(usage_metadata.total_price) as total_spend
  FROM system.billing.usage
  WHERE usage_date = CURRENT_DATE() - 1
),
avg_spend AS (
  SELECT AVG(daily_spend) as avg_daily_spend
  FROM (
    SELECT
      usage_date,
      SUM(usage_metadata.total_price) as daily_spend
    FROM system.billing.usage
    WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
      AND usage_date < CURRENT_DATE() - 1
    GROUP BY usage_date
  )
)
SELECT
  CASE
    WHEN y.total_spend > a.avg_daily_spend * 1.5 THEN
      CONCAT('⚠️ HIGH SPEND ALERT: Yesterday spend $',
             ROUND(y.total_spend, 2),
             ' is 50% above 30-day average of $',
             ROUND(a.avg_daily_spend, 2))
    ELSE 'No alert'
  END as alert_message
FROM yesterday_spend y, avg_spend a;
```

#### Contract Overrun Alert
```sql
-- Alert if contract consumption is ahead of schedule
SELECT
  c.contract_id,
  CONCAT('⚠️ CONTRACT ALERT: ',
         c.contract_id,
         ' is consuming faster than expected. ',
         ROUND(spent * 100.0 / total_value, 1),
         '% spent with ',
         ROUND(elapsed_days * 100.0 / total_days, 1),
         '% time elapsed') as alert_message
FROM (
  SELECT
    c.contract_id,
    c.total_value,
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
) c
WHERE (spent / total_value) > (elapsed_days / total_days) * 1.1;
```

#### Data Freshness Alert
```sql
-- Alert if data is more than 3 days old
SELECT
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) > 3 THEN
      CONCAT('⚠️ DATA FRESHNESS ALERT: System tables data is ',
             DATEDIFF(CURRENT_DATE(), MAX(usage_date)),
             ' days old. Latest data: ',
             MAX(usage_date))
    ELSE 'No alert'
  END as alert_message
FROM system.billing.usage;
```

## Troubleshooting

### Issue: No Data in Dashboard

**Symptoms**: Dashboard shows no data or zero values

**Check**:
```sql
-- 1. Verify system tables access
SELECT COUNT(*) FROM system.billing.usage LIMIT 1;

-- 2. Check date range
SELECT MIN(usage_date), MAX(usage_date)
FROM system.billing.usage;

-- 3. Check if dashboard_data table is populated
SELECT COUNT(*), MIN(usage_date), MAX(usage_date)
FROM account_monitoring.dashboard_data;
```

**Resolution**:
1. Verify system tables are enabled for your account
2. Check if you have correct permissions
3. Run the dashboard refresh job
4. Verify date filters in dashboard queries

### Issue: Contract Consumption Not Matching

**Symptoms**: Contract consumption percentage doesn't match expected

**Check**:
```sql
-- Verify contract dates and account IDs
SELECT
  c.contract_id,
  c.account_id,
  c.cloud_provider,
  c.start_date,
  c.end_date,
  COUNT(DISTINCT u.usage_date) as days_with_usage,
  SUM(u.usage_metadata.total_price) as total_spent
FROM account_monitoring.contracts c
LEFT JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND c.cloud_provider = u.cloud_provider
  AND u.usage_date BETWEEN c.start_date AND c.end_date
WHERE c.contract_id = '<contract_id>'
GROUP BY ALL;
```

**Resolution**:
1. Verify account_id matches exactly
2. Check cloud_provider spelling (lowercase: 'aws', 'azure', 'gcp')
3. Verify date range is correct
4. Check for data gaps in system tables

### Issue: Slow Dashboard Performance

**Symptoms**: Dashboard takes long time to load

**Check**:
```sql
-- Check table statistics
DESCRIBE DETAIL account_monitoring.dashboard_data;

-- Check if table needs optimization
SELECT
  COUNT(*) as total_rows,
  COUNT(DISTINCT usage_date) as distinct_dates,
  MAX(updated_at) as last_updated
FROM account_monitoring.dashboard_data;
```

**Resolution**:
```sql
-- 1. Optimize table
OPTIMIZE account_monitoring.dashboard_data
ZORDER BY (usage_date, workspace_id);

-- 2. Update statistics
ANALYZE TABLE account_monitoring.dashboard_data
COMPUTE STATISTICS FOR ALL COLUMNS;

-- 3. Consider adding date filter to dashboard queries
-- All queries should include:
-- WHERE usage_date >= DATE_SUB(CURRENT_DATE(), <appropriate_days>)
```

## Backup and Recovery

### Backup Critical Tables

```sql
-- Backup contracts
CREATE TABLE account_monitoring.contracts_backup_<YYYYMMDD> AS
SELECT * FROM account_monitoring.contracts;

-- Backup account metadata
CREATE TABLE account_monitoring.account_metadata_backup_<YYYYMMDD> AS
SELECT * FROM account_monitoring.account_metadata;

-- Backup dashboard data (optional - can regenerate)
CREATE TABLE account_monitoring.dashboard_data_backup_<YYYYMMDD> AS
SELECT * FROM account_monitoring.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90);
```

### Recovery

```sql
-- Restore from backup
INSERT OVERWRITE TABLE account_monitoring.contracts
SELECT * FROM account_monitoring.contracts_backup_<YYYYMMDD>;

-- Or create new table from backup
CREATE TABLE account_monitoring.contracts_restored AS
SELECT * FROM account_monitoring.contracts_backup_<YYYYMMDD>;
```

## Performance Optimization

### Query Optimization Tips

1. **Always use date filters**: Reduces data scanned
2. **Use appropriate aggregation level**: Daily vs. weekly vs. monthly
3. **Leverage partitioning**: Filter on usage_date first
4. **Use ZORDER**: Optimize for common query patterns
5. **Cache results**: For frequently accessed data

### Recommended ZORDER

```sql
-- For dashboard_data table
OPTIMIZE account_monitoring.dashboard_data
ZORDER BY (usage_date, workspace_id, cloud_provider);

-- For contracts table
OPTIMIZE account_monitoring.contracts
ZORDER BY (end_date, status);
```

### Create Summary Tables

```sql
-- Daily summary for faster queries
CREATE TABLE IF NOT EXISTS account_monitoring.daily_summary AS
SELECT
  usage_date,
  cloud_provider,
  COUNT(DISTINCT workspace_id) as workspace_count,
  COUNT(DISTINCT sku_name) as sku_count,
  SUM(usage_quantity) as total_dbu,
  SUM(usage_metadata.total_price) as total_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 730)
GROUP BY usage_date, cloud_provider;

-- Refresh daily
INSERT OVERWRITE account_monitoring.daily_summary
SELECT ... -- same query as above
```

## Best Practices

1. **Regular Reviews**: Schedule weekly and monthly reviews
2. **Data Validation**: Check data freshness daily
3. **Contract Management**: Review contract pace monthly
4. **Alerting**: Set up proactive alerts for anomalies
5. **Optimization**: Optimize tables monthly
6. **Backups**: Backup metadata tables weekly
7. **Documentation**: Keep metadata up-to-date
8. **Access Control**: Review permissions quarterly
