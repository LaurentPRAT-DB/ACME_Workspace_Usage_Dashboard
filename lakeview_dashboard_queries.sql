-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Lakeview Dashboard Queries for Account Monitor
-- MAGIC
-- MAGIC Copy these queries directly into your Lakeview dashboard.
-- MAGIC Each query is optimized for specific visualizations.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 1: Contract Burndown Line Chart
-- MAGIC **Visualization Type:** Line Chart
-- MAGIC **Purpose:** Shows actual vs ideal consumption over time
-- MAGIC
-- MAGIC **Chart Configuration:**
-- MAGIC - **X-Axis:** date
-- MAGIC - **Y-Axis:** Multiple lines:
-- MAGIC   - actual_consumption (Label: "Actual Spend")
-- MAGIC   - ideal_consumption (Label: "Ideal Linear Burn")
-- MAGIC   - contract_value (Label: "Contract Limit")
-- MAGIC - **Group By:** contract_label
-- MAGIC - **Legend:** Show
-- MAGIC - **Title:** "Contract Burndown - Actual vs Ideal"

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
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)  -- Last 6 months for better visibility
ORDER BY contract_id, usage_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 2: Contract Summary Table
-- MAGIC **Visualization Type:** Table
-- MAGIC **Purpose:** Shows current status of all active contracts
-- MAGIC
-- MAGIC **Table Configuration:**
-- MAGIC - **Title:** "Active Contracts - Status Summary"
-- MAGIC - **Sortable:** Yes
-- MAGIC - **Default Sort:** consumed_pct DESC

-- COMMAND ----------

SELECT
  contract_id as "Contract ID",
  cloud_provider as "Cloud",
  start_date as "Start Date",
  end_date as "End Date",
  CONCAT('$', FORMAT_NUMBER(commitment, 0)) as "Total Value",
  CONCAT('$', FORMAT_NUMBER(total_consumed, 2)) as "Consumed",
  CONCAT('$', FORMAT_NUMBER(budget_remaining, 2)) as "Remaining",
  CONCAT(ROUND(consumed_pct, 1), '%') as "% Consumed",
  pace_status as "Pace Status",
  days_remaining as "Days Left",
  projected_end_date as "Projected End"
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY consumed_pct DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 3: Daily Consumption Counter
-- MAGIC **Visualization Type:** Counter
-- MAGIC **Purpose:** Shows today's total consumption across all contracts
-- MAGIC
-- MAGIC **Counter Configuration:**
-- MAGIC - **Title:** "Today's Consumption"
-- MAGIC - **Value Field:** daily_cost
-- MAGIC - **Format:** Currency (USD)

-- COMMAND ----------

SELECT
  CONCAT('$', FORMAT_NUMBER(SUM(daily_cost), 2)) as daily_cost,
  COUNT(DISTINCT contract_id) as active_contracts,
  usage_date as date
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date = CURRENT_DATE() - 1  -- Yesterday (most recent complete day)
GROUP BY usage_date;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 4: Contract Pace Distribution (Pie Chart)
-- MAGIC **Visualization Type:** Pie Chart
-- MAGIC **Purpose:** Shows how many contracts are on/over/under pace
-- MAGIC
-- MAGIC **Pie Chart Configuration:**
-- MAGIC - **Title:** "Contract Pace Distribution"
-- MAGIC - **Values:** contract_count
-- MAGIC - **Labels:** pace_status

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
-- MAGIC ## Query 5: Monthly Cost Trend (Bar Chart)
-- MAGIC **Visualization Type:** Stacked Bar Chart
-- MAGIC **Purpose:** Shows monthly consumption by contract
-- MAGIC
-- MAGIC **Bar Chart Configuration:**
-- MAGIC - **Title:** "Monthly Consumption by Contract"
-- MAGIC - **X-Axis:** month
-- MAGIC - **Y-Axis:** monthly_cost
-- MAGIC - **Stack By:** contract_id

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
-- MAGIC ## Query 6: Top Consuming Workspaces (Table)
-- MAGIC **Visualization Type:** Table
-- MAGIC **Purpose:** Shows which workspaces are consuming the most
-- MAGIC
-- MAGIC **Table Configuration:**
-- MAGIC - **Title:** "Top 10 Consuming Workspaces (Last 30 Days)"
-- MAGIC - **Limit:** 10 rows

-- COMMAND ----------

SELECT
  workspace_id as "Workspace ID",
  cloud_provider as "Cloud",
  CONCAT('$', FORMAT_NUMBER(SUM(actual_cost), 2)) as "Total Cost",
  ROUND(SUM(usage_quantity), 2) as "Total DBU",
  COUNT(DISTINCT sku_name) as "Unique SKUs",
  COUNT(DISTINCT usage_date) as "Active Days"
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id, cloud_provider
ORDER BY SUM(actual_cost) DESC
LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Query 7: Contract Details with Projections
-- MAGIC **Visualization Type:** Table with Rich Formatting
-- MAGIC **Purpose:** Detailed view with calculations and warnings
-- MAGIC
-- MAGIC **Table Configuration:**
-- MAGIC - **Title:** "Contract Analysis - Detailed View"
-- MAGIC - **Conditional Formatting:** Highlight rows where pace_status contains "OVER" in red

-- COMMAND ----------

SELECT
  contract_id as "Contract",
  CONCAT('$', FORMAT_NUMBER(commitment, 0)) as "Value",
  CONCAT('$', FORMAT_NUMBER(total_consumed, 2)) as "Spent",
  CONCAT(ROUND(consumed_pct, 1), '%') as "% Used",
  pace_status as "Status",
  days_remaining as "Days Left",
  DATEDIFF(projected_end_date, end_date) as "Days Variance",
  CASE
    WHEN projected_end_date < end_date THEN '⚠️ Will deplete early'
    WHEN projected_end_date > end_date THEN '✅ Under budget'
    ELSE '✅ On track'
  END as "Budget Health",
  projected_end_date as "Est. Depletion Date",
  end_date as "Contract End Date"
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY days_remaining;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Quick Copy Guide
-- MAGIC
-- MAGIC 1. **Line Chart (Main Burndown)** - Use Query 1
-- MAGIC 2. **Summary Table** - Use Query 2
-- MAGIC 3. **Today's Consumption Counter** - Use Query 3
-- MAGIC 4. **Pace Distribution Pie Chart** - Use Query 4
-- MAGIC 5. **Monthly Trend Bar Chart** - Use Query 5
-- MAGIC 6. **Top Workspaces Table** - Use Query 6
-- MAGIC 7. **Detailed Analysis Table** - Use Query 7
