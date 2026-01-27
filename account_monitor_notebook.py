# Databricks notebook source
# MAGIC %md
# MAGIC # Account Monitor Dashboard
# MAGIC ## Cost and Usage Tracking using Databricks System Tables
# MAGIC
# MAGIC This notebook recreates the IBM Account Monitor functionality using Databricks system tables.
# MAGIC
# MAGIC **Data Sources:**
# MAGIC - `system.billing.usage` - Usage data and costs
# MAGIC - `system.billing.list_prices` - Pricing information
# MAGIC - Custom tables for contracts and organizational data

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup and Configuration

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration
LOOKBACK_DAYS = 365  # Last 12 months
CATALOG = "system"
SCHEMA = "billing"

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

print(f"Configuration loaded - Analyzing last {LOOKBACK_DAYS} days")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create Contract Management Table
# MAGIC
# MAGIC Since contracts aren't in system tables, create a custom table to track them.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create database for custom tracking tables
# MAGIC CREATE DATABASE IF NOT EXISTS account_monitoring;
# MAGIC
# MAGIC -- Create contracts table
# MAGIC CREATE TABLE IF NOT EXISTS account_monitoring.contracts (
# MAGIC   contract_id STRING,
# MAGIC   account_id STRING,
# MAGIC   cloud_provider STRING,
# MAGIC   start_date DATE,
# MAGIC   end_date DATE,
# MAGIC   total_value DECIMAL(18,2),
# MAGIC   currency STRING DEFAULT 'USD',
# MAGIC   commitment_type STRING,  -- 'DBU' or 'SPEND'
# MAGIC   status STRING,  -- 'ACTIVE', 'EXPIRED', 'PENDING'
# MAGIC   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
# MAGIC   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
# MAGIC   CONSTRAINT pk_contracts PRIMARY KEY (contract_id)
# MAGIC );
# MAGIC
# MAGIC -- Create account metadata table
# MAGIC CREATE TABLE IF NOT EXISTS account_monitoring.account_metadata (
# MAGIC   account_id STRING,
# MAGIC   customer_name STRING,
# MAGIC   salesforce_id STRING,
# MAGIC   business_unit_l0 STRING,
# MAGIC   business_unit_l1 STRING,
# MAGIC   business_unit_l2 STRING,
# MAGIC   business_unit_l3 STRING,
# MAGIC   account_executive STRING,
# MAGIC   solutions_architect STRING,
# MAGIC   delivery_solutions_architect STRING,
# MAGIC   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
# MAGIC   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
# MAGIC   CONSTRAINT pk_account_metadata PRIMARY KEY (account_id)
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Insert Sample Contract Data
# MAGIC
# MAGIC Replace this with your actual contract data.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Sample contract data (replace with actual data)
# MAGIC INSERT INTO account_monitoring.contracts VALUES
# MAGIC   ('1694992', 'account-001', 'aws', '2024-11-10', '2026-01-29', 300000.00, 'USD', 'SPEND', 'ACTIVE', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
# MAGIC   ('2209701', 'account-001', 'aws', '2026-01-30', '2029-01-29', 1000000.00, 'USD', 'SPEND', 'ACTIVE', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
# MAGIC
# MAGIC -- Sample account metadata (replace with actual data)
# MAGIC INSERT INTO account_monitoring.account_metadata VALUES
# MAGIC   ('account-001', 'Mercuria Energy Group Holding SA', '0014N00001HEcQAG', 'EMEA', 'Central', 'Switzerland', 'Switzerland Enterprise',
# MAGIC    'Claudio Crivelli', 'Laurent Prat', 'Unassigned_CSE_EMEA_Central', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Account Overview Metrics

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT sku_name) as top_sku_count,
# MAGIC   COUNT(DISTINCT workspace_id) as top_workspace_count,
# MAGIC   MAX(usage_date) as latest_usage_date,
# MAGIC   MIN(usage_date) as earliest_usage_date,
# MAGIC   DATEDIFF(MAX(usage_date), MIN(usage_date)) as days_of_data
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Latest Data Dates - Data Freshness Check

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   'Consumption' as source,
# MAGIC   MAX(usage_date) as latest_date,
# MAGIC   DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind,
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
# MAGIC     ELSE 'False'
# MAGIC   END as verified
# MAGIC FROM system.billing.usage
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Metrics' as source,
# MAGIC   MAX(usage_date) as latest_date,
# MAGIC   DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind,
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
# MAGIC     ELSE 'False'
# MAGIC   END as verified
# MAGIC FROM system.billing.usage;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Account Information with Metadata

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   am.customer_name,
# MAGIC   am.salesforce_id,
# MAGIC   am.business_unit_l0,
# MAGIC   am.business_unit_l1,
# MAGIC   am.business_unit_l2,
# MAGIC   am.business_unit_l3,
# MAGIC   am.account_executive,
# MAGIC   am.solutions_architect,
# MAGIC   am.delivery_solutions_architect,
# MAGIC   COUNT(DISTINCT u.workspace_id) as total_workspaces,
# MAGIC   COUNT(DISTINCT u.sku_name) as total_skus
# MAGIC FROM account_monitoring.account_metadata am
# MAGIC LEFT JOIN system.billing.usage u
# MAGIC   ON am.account_id = u.account_id
# MAGIC   AND u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC GROUP BY ALL;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Total Spend in Timeframe

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW total_spend_by_cloud AS
# MAGIC SELECT
# MAGIC   am.customer_name,
# MAGIC   u.cloud_provider as cloud,
# MAGIC   DATE_FORMAT(MIN(u.usage_date), 'yyyyMMddHHmm') as start_date,
# MAGIC   DATE_FORMAT(MAX(u.usage_date), 'yyyyMMddHHmm') as end_date,
# MAGIC   ROUND(SUM(u.usage_quantity), 3) as dbu,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default_price_per_unit, 0)), 2) as list_price,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default_price_per_unit, 0) * 0.85), 2) as discounted_price,
# MAGIC   ROUND(SUM(COALESCE(u.usage_metadata.total_price, 0)), 2) as revenue
# MAGIC FROM system.billing.usage u
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud_provider = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC LEFT JOIN account_monitoring.account_metadata am
# MAGIC   ON u.account_id = am.account_id
# MAGIC WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC GROUP BY am.customer_name, u.cloud_provider
# MAGIC ORDER BY u.cloud_provider;
# MAGIC
# MAGIC SELECT * FROM total_spend_by_cloud;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Contracts Overview

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW contracts_with_consumption AS
# MAGIC SELECT
# MAGIC   c.cloud_provider as platform,
# MAGIC   c.contract_id,
# MAGIC   c.start_date,
# MAGIC   c.end_date,
# MAGIC   c.total_value,
# MAGIC   COALESCE(SUM(u.usage_metadata.total_price), 0) as consumed,
# MAGIC   ROUND(COALESCE(SUM(u.usage_metadata.total_price), 0) / c.total_value * 100, 1) as consumed_pct
# MAGIC FROM account_monitoring.contracts c
# MAGIC LEFT JOIN system.billing.usage u
# MAGIC   ON c.account_id = u.account_id
# MAGIC   AND c.cloud_provider = u.cloud_provider
# MAGIC   AND u.usage_date BETWEEN c.start_date AND c.end_date
# MAGIC WHERE c.status = 'ACTIVE'
# MAGIC GROUP BY
# MAGIC   c.cloud_provider,
# MAGIC   c.contract_id,
# MAGIC   c.start_date,
# MAGIC   c.end_date,
# MAGIC   c.total_value
# MAGIC ORDER BY c.start_date;
# MAGIC
# MAGIC SELECT * FROM contracts_with_consumption;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Contract Burndown Chart

# COMMAND ----------

# Get daily cumulative spending for burndown chart
daily_spend = spark.sql("""
SELECT
  c.contract_id,
  c.start_date,
  c.end_date,
  c.total_value as commitment,
  u.usage_date,
  u.cloud_provider,
  SUM(COALESCE(u.usage_metadata.total_price, 0)) as daily_cost,
  SUM(SUM(COALESCE(u.usage_metadata.total_price, 0))) OVER (
    PARTITION BY c.contract_id
    ORDER BY u.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost
FROM account_monitoring.contracts c
LEFT JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND c.cloud_provider = u.cloud_provider
  AND u.usage_date BETWEEN c.start_date AND c.end_date
WHERE c.status = 'ACTIVE'
GROUP BY
  c.contract_id,
  c.start_date,
  c.end_date,
  c.total_value,
  u.usage_date,
  u.cloud_provider
ORDER BY u.usage_date
""").toPandas()

# Create burndown visualization
if not daily_spend.empty:
    fig = go.Figure()

    # Group by contract
    for contract_id in daily_spend['contract_id'].unique():
        contract_data = daily_spend[daily_spend['contract_id'] == contract_id]

        # Add consumption line
        fig.add_trace(go.Scatter(
            x=contract_data['usage_date'],
            y=contract_data['cumulative_cost'],
            mode='lines',
            name=f'Contract {contract_id} - Consumption',
            line=dict(width=2)
        ))

        # Add commitment line
        commitment = contract_data['commitment'].iloc[0]
        fig.add_trace(go.Scatter(
            x=[contract_data['start_date'].iloc[0], contract_data['end_date'].iloc[0]],
            y=[0, commitment],
            mode='lines',
            name=f'Contract {contract_id} - Commitment',
            line=dict(dash='dash', width=2)
        ))

    fig.update_layout(
        title='Contract Burndown',
        xaxis_title='Date',
        yaxis_title='DBU',
        hovermode='x unified',
        height=500
    )

    fig.show()
else:
    print("No contract data available for burndown chart")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Top Consuming Workspaces

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   workspace_id,
# MAGIC   cloud_provider,
# MAGIC   COUNT(DISTINCT sku_name) as sku_count,
# MAGIC   ROUND(SUM(usage_quantity), 2) as total_dbu,
# MAGIC   ROUND(SUM(COALESCE(usage_metadata.total_price, 0)), 2) as total_cost,
# MAGIC   COUNT(DISTINCT usage_date) as active_days,
# MAGIC   ROUND(AVG(COALESCE(usage_metadata.total_price, 0)), 2) as avg_daily_cost
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC GROUP BY workspace_id, cloud_provider
# MAGIC ORDER BY total_cost DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Top Consuming SKUs

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   sku_name,
# MAGIC   cloud_provider,
# MAGIC   usage_unit,
# MAGIC   ROUND(SUM(usage_quantity), 2) as total_usage,
# MAGIC   ROUND(SUM(COALESCE(usage_metadata.total_price, 0)), 2) as total_cost,
# MAGIC   COUNT(DISTINCT workspace_id) as workspace_count,
# MAGIC   COUNT(DISTINCT usage_date) as active_days
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC GROUP BY sku_name, cloud_provider, usage_unit
# MAGIC ORDER BY total_cost DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Monthly Spend Trend

# COMMAND ----------

monthly_df = spark.sql("""
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  ROUND(SUM(usage_quantity), 2) as monthly_dbu,
  ROUND(SUM(COALESCE(usage_metadata.total_price, 0)), 2) as monthly_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces,
  COUNT(DISTINCT sku_name) as unique_skus
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), cloud_provider
ORDER BY month DESC, cloud_provider
""").toPandas()

# Create monthly trend chart
if not monthly_df.empty:
    fig = px.bar(
        monthly_df,
        x='month',
        y='monthly_cost',
        color='cloud_provider',
        title='Monthly Cost Trend by Cloud Provider',
        labels={'monthly_cost': 'Cost ($)', 'month': 'Month'},
        barmode='group'
    )
    fig.update_layout(height=400)
    fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Cost by Product Category

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   DATE_TRUNC('MONTH', usage_date) as month,
# MAGIC   CASE
# MAGIC     WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
# MAGIC     WHEN sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
# MAGIC     WHEN sku_name LIKE '%DLT%' OR sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
# MAGIC     WHEN sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
# MAGIC     WHEN sku_name LIKE '%INFERENCE%' OR sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
# MAGIC     WHEN sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
# MAGIC     WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
# MAGIC     ELSE 'Other'
# MAGIC   END as category,
# MAGIC   cloud_provider,
# MAGIC   ROUND(SUM(usage_quantity), 2) as total_dbu,
# MAGIC   ROUND(SUM(COALESCE(usage_metadata.total_price, 0)), 2) as total_cost
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC GROUP BY DATE_TRUNC('MONTH', usage_date), category, cloud_provider
# MAGIC ORDER BY month DESC, total_cost DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. Export Data for External Dashboard

# COMMAND ----------

# Export to Delta table for Lakeview dashboard
spark.sql("""
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
    WHEN u.sku_name LIKE '%DLT%' OR u.sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
    WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
    WHEN u.sku_name LIKE '%INFERENCE%' OR u.sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
    WHEN u.sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
    WHEN u.sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
    ELSE 'Other'
  END as product_category
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud_provider = lp.cloud
  AND u.usage_date >= lp.price_start_time
  AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
LEFT JOIN account_monitoring.account_metadata am
  ON u.account_id = am.account_id
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
""")

print("Dashboard data exported to: account_monitoring.dashboard_data")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 15. Summary Statistics

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Summary across all dimensions
# MAGIC SELECT
# MAGIC   'Total Spend (Last 365 days)' as metric,
# MAGIC   CONCAT('$', FORMAT_NUMBER(SUM(COALESCE(usage_metadata.total_price, 0)), 2)) as value
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Total DBUs Consumed' as metric,
# MAGIC   FORMAT_NUMBER(SUM(usage_quantity), 2) as value
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Active Workspaces' as metric,
# MAGIC   CAST(COUNT(DISTINCT workspace_id) AS STRING) as value
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Unique SKUs Used' as metric,
# MAGIC   CAST(COUNT(DISTINCT sku_name) AS STRING) as value
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Average Daily Spend' as metric,
# MAGIC   CONCAT('$', FORMAT_NUMBER(AVG(daily_cost), 2)) as value
# MAGIC FROM (
# MAGIC   SELECT
# MAGIC     usage_date,
# MAGIC     SUM(COALESCE(usage_metadata.total_price, 0)) as daily_cost
# MAGIC   FROM system.billing.usage
# MAGIC   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC   GROUP BY usage_date
# MAGIC );
