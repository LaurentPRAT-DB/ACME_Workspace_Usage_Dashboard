-- Build Forecast Features
-- Prepares daily cost data in format needed by Prophet forecasting
-- This SQL can be run as part of the daily refresh to ensure data is ready for inference

-- Create or replace view with daily aggregated costs per contract
-- Prophet requires data in (ds, y) format where ds=date and y=value
CREATE OR REPLACE VIEW main.account_monitoring_dev.forecast_features AS
WITH daily_costs AS (
  SELECT
    c.contract_id,
    c.account_id,
    c.cloud_provider,
    c.start_date as contract_start,
    c.end_date as contract_end,
    c.total_value as contract_value,
    d.usage_date,
    -- Aggregate daily cost
    SUM(d.actual_cost) as daily_cost,
    -- Count of records for data quality check
    COUNT(*) as record_count
  FROM main.account_monitoring_dev.contracts c
  INNER JOIN main.account_monitoring_dev.dashboard_data d
    ON c.account_id = d.account_id
    AND c.cloud_provider = d.cloud_provider
    AND d.usage_date BETWEEN c.start_date AND CURRENT_DATE()
  WHERE c.status = 'ACTIVE'
  GROUP BY
    c.contract_id,
    c.account_id,
    c.cloud_provider,
    c.start_date,
    c.end_date,
    c.total_value,
    d.usage_date
),
-- Fill gaps in date series with zeros for consistent time series
date_spine AS (
  SELECT
    contract_id,
    account_id,
    cloud_provider,
    contract_start,
    contract_end,
    contract_value,
    date_series as usage_date
  FROM (
    SELECT DISTINCT
      contract_id,
      account_id,
      cloud_provider,
      contract_start,
      contract_end,
      contract_value,
      MIN(usage_date) as min_date,
      MAX(usage_date) as max_date
    FROM daily_costs
    GROUP BY ALL
  ) contracts
  LATERAL VIEW EXPLODE(
    SEQUENCE(min_date, max_date, INTERVAL 1 DAY)
  ) dates AS date_series
)
SELECT
  ds.contract_id,
  ds.account_id,
  ds.cloud_provider,
  ds.contract_start,
  ds.contract_end,
  ds.contract_value,
  ds.usage_date as ds,  -- Prophet date column
  COALESCE(dc.daily_cost, 0) as y,  -- Prophet value column
  -- Additional features for analysis
  DAYOFWEEK(ds.usage_date) as day_of_week,
  MONTH(ds.usage_date) as month,
  QUARTER(ds.usage_date) as quarter,
  -- Running totals
  SUM(COALESCE(dc.daily_cost, 0)) OVER (
    PARTITION BY ds.contract_id
    ORDER BY ds.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost,
  -- Days into contract
  DATEDIFF(ds.usage_date, ds.contract_start) as days_elapsed,
  -- Remaining budget
  ds.contract_value - SUM(COALESCE(dc.daily_cost, 0)) OVER (
    PARTITION BY ds.contract_id
    ORDER BY ds.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as remaining_budget,
  -- Data quality flag
  CASE WHEN dc.daily_cost IS NOT NULL THEN 1 ELSE 0 END as has_actual_data
FROM date_spine ds
LEFT JOIN daily_costs dc
  ON ds.contract_id = dc.contract_id
  AND ds.usage_date = dc.usage_date
ORDER BY ds.contract_id, ds.usage_date;

-- Create summary stats for each contract (useful for model selection)
CREATE OR REPLACE VIEW main.account_monitoring_dev.forecast_feature_summary AS
SELECT
  contract_id,
  cloud_provider,
  contract_start,
  contract_end,
  contract_value,
  -- Data availability
  COUNT(*) as total_days,
  SUM(has_actual_data) as days_with_data,
  ROUND(SUM(has_actual_data) * 100.0 / COUNT(*), 2) as data_coverage_pct,
  -- Cost statistics
  MIN(ds) as first_data_date,
  MAX(ds) as last_data_date,
  ROUND(SUM(y), 2) as total_spent,
  ROUND(AVG(y), 2) as avg_daily_cost,
  ROUND(STDDEV(y), 2) as stddev_daily_cost,
  ROUND(MAX(y), 2) as max_daily_cost,
  -- Consumption metrics
  ROUND(MAX(cumulative_cost), 2) as current_cumulative,
  ROUND(MAX(cumulative_cost) * 100.0 / contract_value, 2) as pct_consumed,
  MAX(remaining_budget) as budget_remaining,
  -- Prophet readiness check
  CASE
    WHEN SUM(has_actual_data) >= 30 THEN 'READY'
    WHEN SUM(has_actual_data) >= 14 THEN 'LIMITED'
    ELSE 'INSUFFICIENT'
  END as prophet_readiness
FROM main.account_monitoring_dev.forecast_features
GROUP BY
  contract_id,
  cloud_provider,
  contract_start,
  contract_end,
  contract_value
ORDER BY contract_id;

-- Display summary
SELECT
  'Forecast features built successfully' as status,
  COUNT(DISTINCT contract_id) as contracts_prepared,
  SUM(CASE WHEN prophet_readiness = 'READY' THEN 1 ELSE 0 END) as ready_for_prophet,
  SUM(CASE WHEN prophet_readiness = 'LIMITED' THEN 1 ELSE 0 END) as limited_data,
  SUM(CASE WHEN prophet_readiness = 'INSUFFICIENT' THEN 1 ELSE 0 END) as insufficient_data
FROM main.account_monitoring_dev.forecast_feature_summary;
