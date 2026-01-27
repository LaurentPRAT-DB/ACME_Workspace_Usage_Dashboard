-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Contract Burndown Verification
-- MAGIC
-- MAGIC Run this notebook to verify contract burndown data is properly configured and populated.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Check Active Contracts

-- COMMAND ----------

SELECT
  contract_id,
  cloud_provider,
  start_date,
  end_date,
  CONCAT('$', FORMAT_NUMBER(total_value, 2)) as contract_value,
  status,
  notes,
  DATEDIFF(CURRENT_DATE(), start_date) as days_elapsed,
  DATEDIFF(end_date, CURRENT_DATE()) as days_remaining
FROM main.account_monitoring_dev.contracts
WHERE status = 'ACTIVE'
ORDER BY start_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Contract Burndown Summary (Latest Status)

-- COMMAND ----------

SELECT
  contract_id,
  cloud_provider,
  CONCAT('$', FORMAT_NUMBER(commitment, 0)) as total_value,
  CONCAT('$', FORMAT_NUMBER(total_consumed, 2)) as consumed,
  CONCAT('$', FORMAT_NUMBER(budget_remaining, 2)) as remaining,
  CONCAT(ROUND(consumed_pct, 1), '%') as pct_consumed,
  pace_status,
  days_remaining,
  projected_end_date,
  last_usage_date
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY
  CASE
    WHEN pace_status LIKE '%OVER%' THEN 1
    WHEN pace_status LIKE '%ABOVE%' THEN 2
    ELSE 3
  END,
  consumed_pct DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Daily Burndown Data (Last 30 Days)

-- COMMAND ----------

SELECT
  contract_id,
  usage_date,
  ROUND(daily_cost, 2) as daily_cost,
  ROUND(cumulative_cost, 2) as cumulative_cost,
  ROUND(projected_linear_burn, 2) as projected_linear_burn,
  ROUND(remaining_budget, 2) as remaining_budget,
  ROUND(budget_pct_consumed, 1) as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
ORDER BY contract_id, usage_date DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Contract Burndown Chart Data
-- MAGIC
-- MAGIC This is the data used for the Lakeview dashboard line chart.

-- COMMAND ----------

SELECT
  contract_id,
  CONCAT(contract_id, ' ($', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
  usage_date as date,
  ROUND(cumulative_cost, 2) as actual_consumption,
  ROUND(projected_linear_burn, 2) as ideal_consumption,
  ROUND(commitment, 2) as contract_value,
  ROUND(budget_pct_consumed, 1) as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
ORDER BY contract_id, usage_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Data Quality Checks

-- COMMAND ----------

-- Check contract coverage
SELECT
  'Contract Coverage' as check_type,
  COUNT(DISTINCT contract_id) as contract_count,
  COUNT(*) as total_data_points,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date,
  DATEDIFF(MAX(usage_date), MIN(usage_date)) as days_of_data
FROM main.account_monitoring_dev.contract_burndown

UNION ALL

-- Check for contracts without burndown data
SELECT
  'Contracts Without Data' as check_type,
  COUNT(*) as contract_count,
  NULL as total_data_points,
  NULL as earliest_date,
  NULL as latest_date,
  NULL as days_of_data
FROM main.account_monitoring_dev.contracts c
WHERE c.status = 'ACTIVE'
  AND NOT EXISTS (
    SELECT 1
    FROM main.account_monitoring_dev.contract_burndown cb
    WHERE cb.contract_id = c.contract_id
  )

UNION ALL

-- Check dashboard data coverage
SELECT
  'Dashboard Data' as check_type,
  COUNT(DISTINCT account_id) as contract_count,
  COUNT(*) as total_data_points,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date,
  DATEDIFF(MAX(usage_date), MIN(usage_date)) as days_of_data
FROM main.account_monitoring_dev.dashboard_data;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Pace Analysis Distribution

-- COMMAND ----------

SELECT
  pace_status,
  COUNT(*) as contract_count,
  ROUND(AVG(consumed_pct), 1) as avg_consumed_pct,
  ROUND(AVG(days_remaining), 0) as avg_days_remaining
FROM main.account_monitoring_dev.contract_burndown_summary
GROUP BY pace_status
ORDER BY
  CASE
    WHEN pace_status LIKE '%OVER%' THEN 1
    WHEN pace_status LIKE '%ABOVE%' THEN 2
    WHEN pace_status LIKE '%ON%' THEN 3
    ELSE 4
  END;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Expected Results
-- MAGIC
-- MAGIC **If everything is working correctly, you should see:**
-- MAGIC
-- MAGIC 1. ✅ Two active contracts in query 1:
-- MAGIC    - CONTRACT-2026-001 ($2,000 - 1 year contract)
-- MAGIC    - CONTRACT-ENTERPRISE-001 ($500,000 - multi-year)
-- MAGIC
-- MAGIC 2. ✅ Summary showing pace status (🟢/🟡/🔴/🔵) in query 2
-- MAGIC
-- MAGIC 3. ✅ Daily data points with cumulative costs in query 3
-- MAGIC
-- MAGIC 4. ✅ Chart data with actual vs ideal consumption in query 4
-- MAGIC
-- MAGIC 5. ✅ Data quality checks showing:
-- MAGIC    - Contract coverage with data points
-- MAGIC    - No contracts without data (should be 0)
-- MAGIC    - Dashboard data covering the contract periods
-- MAGIC
-- MAGIC 6. ✅ Pace distribution showing contract statuses

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Next Steps
-- MAGIC
-- MAGIC 1. ✅ Data is populated - proceed to create Lakeview dashboard
-- MAGIC 2. Use queries from this notebook in dashboard visualizations
-- MAGIC 3. Create line chart for burndown (Query 4)
-- MAGIC 4. Create table for summary (Query 2)
-- MAGIC 5. See CONTRACT_BURNDOWN_GUIDE.md for detailed instructions
