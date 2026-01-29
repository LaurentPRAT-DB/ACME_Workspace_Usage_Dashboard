-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Lakeview Dashboard Queries - Complete Set
-- MAGIC
-- MAGIC All 15 queries for the Account Monitor dashboard with Contract Burndown.
-- MAGIC These queries match the datasets defined in `lakeview_dashboard_config.json`.
-- MAGIC
-- MAGIC **Version:** 1.5.5 (Build: 2026-01-29-002)
-- MAGIC
-- MAGIC **Data Sources:**
-- MAGIC - `system.billing.usage` - Usage data and costs
-- MAGIC - `main.account_monitoring_dev.dashboard_data` - Pre-aggregated dashboard data
-- MAGIC - `main.account_monitoring_dev.contract_burndown` - Contract consumption tracking
-- MAGIC - `main.account_monitoring_dev.contract_burndown_summary` - Latest contract status
-- MAGIC
-- MAGIC **Schema Fields Used:**
-- MAGIC - `actual_cost` - Cost at list price
-- MAGIC - `list_cost` - Total cost at list price (aggregated)
-- MAGIC - `discounted_cost` - Total cost at discounted price (aggregated)
-- MAGIC - `usage_quantity` - DBU/units consumed
-- MAGIC - `product_category` - Derived product category
-- MAGIC
-- MAGIC **Dashboard Pages:**
-- MAGIC 1. Contract Burndown (8 visualizations)
-- MAGIC 2. Account Overview (5 visualizations)
-- MAGIC 3. Usage Analytics (3 visualizations)
-- MAGIC
-- MAGIC **Last Updated:** 2026-01-29 - Fixed field names, added version tracking

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## CONTRACT BURNDOWN PAGE QUERIES

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 1: Contract Burndown Line Chart
-- MAGIC **Dataset:** contract_burndown_chart
-- MAGIC **Visualization:** Line Chart
-- MAGIC **Configuration:**
-- MAGIC - X-Axis: date
-- MAGIC - Y-Axis: actual_consumption, ideal_consumption, contract_value
-- MAGIC - Group By: contract_label
-- MAGIC - Legend: Yes

-- COMMAND ----------

SELECT
  contract_id,
  CONCAT(contract_id, ' (USD ', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
  usage_date as date,
  ROUND(cumulative_cost, 2) as actual_consumption,
  ROUND(projected_linear_burn, 2) as ideal_consumption,
  ROUND(commitment, 2) as contract_value,
  ROUND(budget_pct_consumed, 1) as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
ORDER BY contract_id, usage_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 2: Contract Summary Table
-- MAGIC **Dataset:** contract_summary_table
-- MAGIC **Visualization:** Table
-- MAGIC **Features:** Sortable, Searchable

-- COMMAND ----------

SELECT
  contract_id as 'Contract ID',
  cloud_provider as 'Cloud',
  start_date as 'Start Date',
  end_date as 'End Date',
  CONCAT('USD ', FORMAT_NUMBER(commitment, 0)) as 'Total Value',
  CONCAT('USD ', FORMAT_NUMBER(total_consumed, 2)) as 'Consumed',
  CONCAT('USD ', FORMAT_NUMBER(budget_remaining, 2)) as 'Remaining',
  CONCAT(ROUND(consumed_pct, 1), '%') as '% Consumed',
  pace_status as 'Pace Status',
  days_remaining as 'Days Left',
  projected_end_date as 'Projected End'
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY consumed_pct DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 3: Daily Consumption Counter
-- MAGIC **Dataset:** daily_consumption_counter
-- MAGIC **Visualization:** Counter
-- MAGIC **Field:** daily_cost

-- COMMAND ----------

SELECT
  CONCAT('USD ', FORMAT_NUMBER(SUM(daily_cost), 2)) as daily_cost,
  COUNT(DISTINCT contract_id) as active_contracts,
  usage_date as date
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date = CURRENT_DATE() - 1
GROUP BY usage_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 4: Pace Distribution Pie Chart
-- MAGIC **Dataset:** pace_distribution_pie
-- MAGIC **Visualization:** Pie Chart
-- MAGIC **Value:** contract_count
-- MAGIC **Label:** pace_status

-- COMMAND ----------

SELECT
  pace_status,
  COUNT(*) as contract_count
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
-- MAGIC ### Query 5: Monthly Consumption Bar Chart
-- MAGIC **Dataset:** contract_monthly_trend
-- MAGIC **Visualization:** Stacked Bar Chart
-- MAGIC **X-Axis:** month
-- MAGIC **Y-Axis:** monthly_cost
-- MAGIC **Stack By:** contract_id

-- COMMAND ----------

SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  contract_id,
  SUM(daily_cost) as monthly_cost,
  COUNT(*) as days_active
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), contract_id
ORDER BY month, contract_id;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 6: Top Workspaces Table
-- MAGIC **Dataset:** top_workspaces_detailed
-- MAGIC **Visualization:** Table
-- MAGIC **Timeframe:** Last 30 days

-- COMMAND ----------

SELECT
  workspace_id as 'Workspace ID',
  cloud_provider as 'Cloud',
  CONCAT('USD ', FORMAT_NUMBER(SUM(actual_cost), 2)) as 'Total Cost',
  ROUND(SUM(usage_quantity), 2) as 'Total DBU',
  COUNT(DISTINCT sku_name) as 'Unique SKUs',
  COUNT(DISTINCT usage_date) as 'Active Days'
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id, cloud_provider
ORDER BY SUM(actual_cost) DESC
LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 7: Contract Detailed Analysis
-- MAGIC **Dataset:** contract_detailed_analysis
-- MAGIC **Visualization:** Table
-- MAGIC **Features:** Budget health indicators

-- COMMAND ----------

SELECT
  contract_id as 'Contract',
  CONCAT('USD ', FORMAT_NUMBER(commitment, 0)) as 'Value',
  CONCAT('USD ', FORMAT_NUMBER(total_consumed, 2)) as 'Spent',
  CONCAT(ROUND(consumed_pct, 1), '%') as '% Used',
  pace_status as 'Status',
  days_remaining as 'Days Left',
  DATEDIFF(projected_end_date, end_date) as 'Days Variance',
  CASE
    WHEN projected_end_date < end_date THEN '⚠️ Will deplete early'
    WHEN projected_end_date > end_date THEN '✅ Under budget'
    ELSE '✅ On track'
  END as 'Budget Health',
  projected_end_date as 'Est. Depletion Date',
  end_date as 'Contract End Date'
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY days_remaining;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ACCOUNT OVERVIEW PAGE QUERIES

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 8: Account Overview Counters
-- MAGIC **Dataset:** account_overview
-- MAGIC **Visualization:** Counters (2 counters)
-- MAGIC **Fields:** top_sku_count, top_workspace_count

-- COMMAND ----------

SELECT
  COUNT(DISTINCT sku_name) as top_sku_count,
  COUNT(DISTINCT workspace_id) as top_workspace_count,
  MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 9: Data Freshness
-- MAGIC **Dataset:** data_freshness
-- MAGIC **Visualization:** Table

-- COMMAND ----------

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
-- MAGIC ### Query 10: Total Spend by Cloud
-- MAGIC **Dataset:** total_spend
-- MAGIC **Visualization:** Table

-- COMMAND ----------

SELECT
  customer_name,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 3) as dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 11: Monthly Cost Trend
-- MAGIC **Dataset:** monthly_trend
-- MAGIC **Visualization:** Bar Chart
-- MAGIC **Series:** cloud_provider

-- COMMAND ----------

SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  ROUND(SUM(usage_quantity), 2) as monthly_dbu,
  ROUND(SUM(actual_cost), 2) as monthly_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), cloud_provider
ORDER BY month;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## USAGE ANALYTICS PAGE QUERIES

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 12: Top Consuming Workspaces
-- MAGIC **Dataset:** top_workspaces
-- MAGIC **Visualization:** Table
-- MAGIC **Timeframe:** Last 90 days

-- COMMAND ----------

SELECT
  workspace_id,
  cloud_provider,
  COUNT(DISTINCT sku_name) as sku_count,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY workspace_id, cloud_provider
ORDER BY total_cost DESC
LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 13: Top Consuming SKUs
-- MAGIC **Dataset:** top_skus
-- MAGIC **Visualization:** Table

-- COMMAND ----------

SELECT
  sku_name,
  cloud_provider,
  usage_unit,
  ROUND(SUM(usage_quantity), 2) as total_usage,
  ROUND(SUM(actual_cost), 2) as total_cost,
  COUNT(DISTINCT workspace_id) as workspace_count
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY sku_name, cloud_provider, usage_unit
ORDER BY total_cost DESC
LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 14: Cost by Product Category
-- MAGIC **Dataset:** product_category
-- MAGIC **Visualization:** Stacked Area Chart

-- COMMAND ----------

SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  product_category as category,
  cloud_provider,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), product_category, cloud_provider
ORDER BY month;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 15: Dashboard Data (Base Query)
-- MAGIC **Dataset:** dashboard_data
-- MAGIC **Usage:** Base data for filters and other queries

-- COMMAND ----------

SELECT *
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
LIMIT 100;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query Index
-- MAGIC
-- MAGIC | # | Query Name | Dataset | Visualization | Page |
-- MAGIC |---|------------|---------|---------------|------|
-- MAGIC | 1 | Contract Burndown Chart | contract_burndown_chart | Line Chart | Contract Burndown |
-- MAGIC | 2 | Contract Summary | contract_summary_table | Table | Contract Burndown |
-- MAGIC | 3 | Daily Consumption | daily_consumption_counter | Counter | Contract Burndown |
-- MAGIC | 4 | Pace Distribution | pace_distribution_pie | Pie Chart | Contract Burndown |
-- MAGIC | 5 | Monthly Trend | contract_monthly_trend | Bar Chart | Contract Burndown |
-- MAGIC | 6 | Top Workspaces | top_workspaces_detailed | Table | Contract Burndown |
-- MAGIC | 7 | Detailed Analysis | contract_detailed_analysis | Table | Contract Burndown |
-- MAGIC | 8 | Account Overview | account_overview | Counters | Account Overview |
-- MAGIC | 9 | Data Freshness | data_freshness | Table | Account Overview |
-- MAGIC | 10 | Total Spend | total_spend | Table | Account Overview |
-- MAGIC | 11 | Monthly Cost Trend | monthly_trend | Bar Chart | Account Overview |
-- MAGIC | 12 | Top Workspaces (General) | top_workspaces | Table | Usage Analytics |
-- MAGIC | 13 | Top SKUs | top_skus | Table | Usage Analytics |
-- MAGIC | 14 | Product Category | product_category | Area Chart | Usage Analytics |
-- MAGIC | 15 | Dashboard Data | dashboard_data | Base Data | All Pages |
-- MAGIC
-- MAGIC ## Usage Instructions
-- MAGIC
-- MAGIC 1. **Run this notebook** to verify all queries work
-- MAGIC 2. **Copy queries** directly into Lakeview when creating visualizations
-- MAGIC 3. **Reference** the query index above for dataset mappings
-- MAGIC 4. **See** `lakeview_dashboard_config.json` for complete configuration
-- MAGIC 5. **Follow** `CREATE_LAKEVIEW_DASHBOARD.md` for step-by-step instructions
