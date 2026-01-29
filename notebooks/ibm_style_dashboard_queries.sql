-- Databricks notebook source
-- MAGIC %md
-- MAGIC # IBM-Style Account Monitor Dashboard Queries
-- MAGIC
-- MAGIC Complete set of queries to recreate the IBM Account Monitor dashboard layout.
-- MAGIC This dashboard combines account overview, contract tracking, and burndown visualization.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Top Metrics (SKU and Workspace Counts)

-- COMMAND ----------

-- Query 1: Top Metrics
-- Dataset: top_metrics
-- Shows: SKU count, Workspace count, Latest date
SELECT
  COUNT(DISTINCT sku_name) as top_sku_count,
  COUNT(DISTINCT workspace_id) as top_workspace_count,
  MAX(usage_date) as date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Data Freshness

-- COMMAND ----------

-- Query 2: Latest Data Dates
-- Dataset: data_freshness
-- Shows: Source, Latest Date, Verification status
SELECT
  'Consumption' as source,
  MAX(usage_date) as latest_date,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
    ELSE 'False'
  END as verified
FROM system.billing.usage

UNION ALL

SELECT
  'Metrics' as source,
  MAX(usage_date) as latest_date,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
    ELSE 'False'
  END as verified
FROM system.billing.usage;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Account Information

-- COMMAND ----------

-- Query 3: Account Info
-- Dataset: account_info
-- Shows: Customer details, Salesforce ID, Business Units, Team members
SELECT
  customer_name,
  salesforce_id,
  business_unit_l0,
  business_unit_l1,
  business_unit_l2,
  business_unit_l3,
  account_executive,
  solutions_architect,
  delivery_solutions_architect
FROM main.account_monitoring_dev.account_metadata
LIMIT 1;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Total Spend by Cloud Provider

-- COMMAND ----------

-- Query 4: Total Spend in Timeframe
-- Dataset: total_spend_timeframe
-- Shows: Spending breakdown by cloud provider with DBU, prices, and revenue
SELECT
  customer_name,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 0) as dbu,
  ROUND(SUM(list_cost), 2) as list_price,
  ROUND(SUM(discounted_cost), 2) as discounted_price,
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider
ORDER BY cloud_provider;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Contracts Table

-- COMMAND ----------

-- Query 5: Contracts Table
-- Dataset: contracts_table
-- Shows: Platform, Contract ID, dates, value, consumption, and percentage
SELECT
  cloud_provider as platform,
  contract_id,
  start_date as start,
  end_date as end,
  CONCAT('$', FORMAT_NUMBER(commitment, 0)) as total_value,
  CASE
    WHEN total_consumed IS NULL THEN 'null'
    ELSE CONCAT('$', FORMAT_NUMBER(total_consumed, 2))
  END as consumed,
  CASE
    WHEN consumed_pct IS NULL THEN 'null'
    ELSE CONCAT(ROUND(consumed_pct, 1), '%')
  END as consumed_pct
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY start_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Contract Burndown Chart

-- COMMAND ----------

-- Query 6: Contract Burndown Chart Data
-- Dataset: contract_burndown_chart
-- Shows: Commitment line and Consumption curve over time
SELECT
  usage_date as date,
  contract_id,
  ROUND(commitment, 2) as commit,
  ROUND(cumulative_cost, 2) as consumption
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
ORDER BY usage_date, contract_id;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Alternative: Combined Burndown (All Contracts)

-- COMMAND ----------

-- Query 7: Combined Contract Burndown
-- Dataset: combined_burndown
-- Shows: Total commitment and consumption across all contracts
SELECT
  usage_date as date,
  SUM(commitment) as commit,
  SUM(cumulative_cost) as consumption
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY usage_date
ORDER BY usage_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Account Selection Filter

-- COMMAND ----------

-- Query 8: Available Accounts
-- Dataset: account_list
-- For account filter dropdown
SELECT DISTINCT
  customer_name as account_name,
  salesforce_id
FROM main.account_monitoring_dev.account_metadata
ORDER BY customer_name;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Verification Query - Check All Data

-- COMMAND ----------

-- Query 9: Data Check
-- Verify all tables have data
SELECT
  'dashboard_data' as table_name,
  COUNT(*) as row_count,
  MIN(usage_date) as min_date,
  MAX(usage_date) as max_date
FROM main.account_monitoring_dev.dashboard_data

UNION ALL

SELECT
  'contract_burndown' as table_name,
  COUNT(*) as row_count,
  MIN(usage_date) as min_date,
  MAX(usage_date) as max_date
FROM main.account_monitoring_dev.contract_burndown

UNION ALL

SELECT
  'contract_burndown_summary' as table_name,
  COUNT(*) as row_count,
  NULL as min_date,
  NULL as max_date
FROM main.account_monitoring_dev.contract_burndown_summary

UNION ALL

SELECT
  'account_metadata' as table_name,
  COUNT(*) as row_count,
  NULL as min_date,
  NULL as max_date
FROM main.account_monitoring_dev.account_metadata;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query Index
-- MAGIC
-- MAGIC | # | Query Name | Dataset | Purpose | Visualization |
-- MAGIC |---|------------|---------|---------|---------------|
-- MAGIC | 1 | Top Metrics | top_metrics | SKU/Workspace counts | Counters |
-- MAGIC | 2 | Latest Data Dates | data_freshness | Data quality check | Table |
-- MAGIC | 3 | Account Info | account_info | Customer details | Table/Text |
-- MAGIC | 4 | Total Spend | total_spend_timeframe | Cloud spend breakdown | Table |
-- MAGIC | 5 | Contracts | contracts_table | Contract list | Table |
-- MAGIC | 6 | Burndown Chart | contract_burndown_chart | Individual contracts | Line Chart |
-- MAGIC | 7 | Combined Burndown | combined_burndown | All contracts total | Line Chart |
-- MAGIC | 8 | Account List | account_list | Filter dropdown | Filter |
-- MAGIC | 9 | Data Check | data_verification | Data validation | Table |
