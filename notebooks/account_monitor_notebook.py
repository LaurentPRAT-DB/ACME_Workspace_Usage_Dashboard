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
# MAGIC
# MAGIC **Version:** 1.7.0 (Build: 2026-02-05-001)
# MAGIC
# MAGIC **New in 1.7.0:**
# MAGIC - Prophet-based ML forecasting for consumption prediction
# MAGIC - Confidence bands (p10/p90) for exhaustion dates
# MAGIC - Enhanced burndown chart with forecast overlay

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
VERSION = "1.7.0"
BUILD = "2026-02-05-001"
LOOKBACK_DAYS = 365  # Last 12 months
CATALOG = "system"
SCHEMA = "billing"

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

print(f"Account Monitor Dashboard v{VERSION} (Build: {BUILD})")
print(f"Configuration loaded - Analyzing last {LOOKBACK_DAYS} days")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Verify Setup
# MAGIC
# MAGIC Tables are created by the setup job. If you see errors below, run:
# MAGIC ```
# MAGIC databricks bundle run account_monitor_setup --profile YOUR_PROFILE
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify tables exist
# MAGIC SELECT
# MAGIC   'contracts' as table_name,
# MAGIC   COUNT(*) as row_count
# MAGIC FROM main.account_monitoring_dev.contracts
# MAGIC UNION ALL
# MAGIC SELECT
# MAGIC   'account_metadata' as table_name,
# MAGIC   COUNT(*) as row_count
# MAGIC FROM main.account_monitoring_dev.account_metadata
# MAGIC UNION ALL
# MAGIC SELECT
# MAGIC   'contract_burndown' as table_name,
# MAGIC   COUNT(*) as row_count
# MAGIC FROM main.account_monitoring_dev.contract_burndown
# MAGIC UNION ALL
# MAGIC SELECT
# MAGIC   'contract_forecast' as table_name,
# MAGIC   COUNT(*) as row_count
# MAGIC FROM main.account_monitoring_dev.contract_forecast;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. View Contract Data
# MAGIC
# MAGIC Contract data is configured via `config/contracts.yml` and loaded during setup.
# MAGIC To modify contracts, edit the config file and re-run the setup job:
# MAGIC ```
# MAGIC databricks bundle run account_monitor_setup --profile YOUR_PROFILE
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Show current contracts (configured via config/contracts.yml)
# MAGIC SELECT
# MAGIC   c.contract_id,
# MAGIC   c.cloud_provider,
# MAGIC   c.start_date,
# MAGIC   c.end_date,
# MAGIC   c.total_value,
# MAGIC   c.currency,
# MAGIC   c.status,
# MAGIC   DATEDIFF(c.end_date, c.start_date) as contract_days,
# MAGIC   DATEDIFF(CURRENT_DATE(), c.start_date) as days_elapsed,
# MAGIC   c.notes
# MAGIC FROM main.account_monitoring_dev.contracts c
# MAGIC WHERE c.status = 'ACTIVE'
# MAGIC ORDER BY c.contract_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Show account metadata (configured via config/contracts.yml)
# MAGIC SELECT * FROM main.account_monitoring_dev.account_metadata;

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
# MAGIC   u.cloud as cloud,
# MAGIC   DATE_FORMAT(MIN(u.usage_date), 'yyyyMMddHHmm') as start_date,
# MAGIC   DATE_FORMAT(MAX(u.usage_date), 'yyyyMMddHHmm') as end_date,
# MAGIC   ROUND(SUM(u.usage_quantity), 3) as dbu,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as list_price,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0) * 0.85), 2) as discounted_price,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as revenue
# MAGIC FROM system.billing.usage u
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC LEFT JOIN account_monitoring.account_metadata am
# MAGIC   ON u.account_id = am.account_id
# MAGIC WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC GROUP BY am.customer_name, u.cloud
# MAGIC ORDER BY u.cloud;
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
# MAGIC   COALESCE(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 0) as consumed,
# MAGIC   ROUND(COALESCE(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 0) / c.total_value * 100, 1) as consumed_pct
# MAGIC FROM account_monitoring.contracts c
# MAGIC LEFT JOIN system.billing.usage u
# MAGIC   ON c.account_id = u.account_id
# MAGIC   AND c.cloud_provider = u.cloud
# MAGIC   AND u.usage_date BETWEEN c.start_date AND c.end_date
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
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
  u.cloud,
  SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)) as daily_cost,
  SUM(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0))) OVER (
    PARTITION BY c.contract_id
    ORDER BY u.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost
FROM account_monitoring.contracts c
INNER JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND c.cloud_provider = u.cloud
  AND u.usage_date BETWEEN c.start_date AND c.end_date
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_date >= lp.price_start_time
  AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
WHERE c.status = 'ACTIVE'
GROUP BY
  c.contract_id,
  c.start_date,
  c.end_date,
  c.total_value,
  u.usage_date,
  u.cloud
ORDER BY u.usage_date
""").toPandas()

# Debug output
print(f"Daily spend data shape: {daily_spend.shape}")
if not daily_spend.empty:
    print(f"Date range in data: {daily_spend['usage_date'].min()} to {daily_spend['usage_date'].max()}")
    print(f"Contracts: {daily_spend['contract_id'].unique()}")
    print(f"Total cumulative cost: ${daily_spend['cumulative_cost'].max():.2f}")
else:
    print("WARNING: No data returned from query!")

# Create burndown visualization
if not daily_spend.empty:
    # Convert date columns to datetime for proper plotting
    daily_spend['usage_date'] = pd.to_datetime(daily_spend['usage_date'])
    daily_spend['start_date'] = pd.to_datetime(daily_spend['start_date'])
    daily_spend['end_date'] = pd.to_datetime(daily_spend['end_date'])

    fig = go.Figure()

    # Group by contract
    for contract_id in daily_spend['contract_id'].unique():
        contract_data = daily_spend[daily_spend['contract_id'] == contract_id]

        start_date = contract_data['start_date'].iloc[0]
        end_date = contract_data['end_date'].iloc[0]
        commitment = float(contract_data['commitment'].iloc[0])

        # Add consumption line
        fig.add_trace(go.Scatter(
            x=contract_data['usage_date'],
            y=contract_data['cumulative_cost'],
            mode='lines+markers',
            name=f'Contract {contract_id} - Consumption',
            line=dict(width=3),
            marker=dict(size=4)
        ))

        # Add commitment line (horizontal line at contract value)
        # This shows when cumulative spending will cross the contract limit (burndown date)
        fig.add_trace(go.Scatter(
            x=[start_date, end_date],
            y=[commitment, commitment],
            mode='lines',
            name=f'Contract {contract_id} - Limit (${commitment:,.0f})',
            line=dict(dash='dash', width=3, color='red'),
            opacity=0.8
        ))

    # Calculate burndown percentage and projection
    max_cumulative = daily_spend['cumulative_cost'].max()
    contract_value = daily_spend['commitment'].iloc[0]
    burndown_pct = (float(max_cumulative) / float(contract_value) * 100) if contract_value > 0 else 0

    # Calculate projected burndown date
    first_date = daily_spend['usage_date'].min()
    last_date = daily_spend['usage_date'].max()
    days_elapsed = (last_date - first_date).days

    if days_elapsed > 0 and max_cumulative > 0:
        daily_avg_spend = float(max_cumulative) / days_elapsed
        remaining_budget = float(contract_value) - float(max_cumulative)
        days_to_burndown = remaining_budget / daily_avg_spend if daily_avg_spend > 0 else 0
        projected_burndown_date = last_date + pd.Timedelta(days=float(days_to_burndown))

        print(f"\nProjection Analysis:")
        print(f"  Average daily spend: ${daily_avg_spend:.2f}")
        print(f"  Remaining budget: ${remaining_budget:.2f}")
        print(f"  Days to exhaustion: {days_to_burndown:.0f} days")
        print(f"  Projected burndown date: {projected_burndown_date.strftime('%Y-%m-%d')}")

        if projected_burndown_date <= daily_spend['end_date'].iloc[0]:
            title_text = f'Contract Burndown - ${max_cumulative:.2f} of ${contract_value:.2f} spent ({burndown_pct:.1f}%) - Projected exhaustion: {projected_burndown_date.strftime("%Y-%m-%d")}'

            # Add vertical line at projected burndown date
            fig.add_vline(
                x=projected_burndown_date,
                line_dash="dot",
                line_color="orange",
                line_width=2,
                annotation_text=f"Projected<br>Burndown<br>{projected_burndown_date.strftime('%Y-%m-%d')}",
                annotation_position="top"
            )
        else:
            title_text = f'Contract Burndown - ${max_cumulative:.2f} of ${contract_value:.2f} spent ({burndown_pct:.1f}%) - On track, will not exhaust'
    else:
        title_text = f'Contract Burndown - ${max_cumulative:.2f} of ${contract_value:.2f} spent ({burndown_pct:.1f}%)'

    fig.update_layout(
        title=title_text,
        xaxis_title='Date',
        yaxis_title='Cumulative Cost ($)',
        hovermode='x unified',
        height=600,
        xaxis=dict(
            tickformat='%Y-%m-%d',
            tickangle=45
        ),
        yaxis=dict(
            tickformat='$,.0f',
            range=[0, float(contract_value) * 1.1]  # Set y-axis to show full contract value + 10%
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )

    fig.show()
else:
    print("No contract data available for burndown chart")
    print("\nTroubleshooting:")
    print("1. Run Cell 3 to create/update contract data")
    print("2. Verify you have usage data: SELECT COUNT(*) FROM system.billing.usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)")
    print("3. Check contract dates match usage dates")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9b. Contract Burndown with ML Forecast
# MAGIC
# MAGIC This chart shows historical consumption (yellow) and ML-predicted future consumption (red).
# MAGIC The dashed line represents the contract commitment - watch where the red forecast line crosses it!

# COMMAND ----------

# Load forecast data and create burndown chart with forecast overlay
try:
    # Check if forecast table has data
    forecast_count = spark.sql("""
        SELECT COUNT(*) as cnt FROM main.account_monitoring_dev.contract_forecast
    """).collect()[0]['cnt']
    forecast_exists = forecast_count > 0
except Exception:
    forecast_exists = False
    forecast_count = 0

print(f"Forecast data available: {forecast_exists} ({forecast_count} records)")

if forecast_exists and not daily_spend.empty:
    # Load forecast data
    forecast_df = spark.sql("""
        SELECT
          contract_id,
          forecast_date,
          predicted_cumulative,
          exhaustion_date_p50,
          model_version
        FROM main.account_monitoring_dev.contract_forecast
        ORDER BY contract_id, forecast_date
    """).toPandas()

    # Convert types for plotting
    forecast_df['forecast_date'] = pd.to_datetime(forecast_df['forecast_date'])
    forecast_df['predicted_cumulative'] = forecast_df['predicted_cumulative'].astype(float)

    # Get contract info
    contract_id = daily_spend['contract_id'].iloc[0]
    start_date = daily_spend['start_date'].iloc[0]
    end_date = daily_spend['end_date'].iloc[0]
    commitment = float(daily_spend['commitment'].iloc[0])

    # Get exhaustion date from forecast
    exhaustion_date = forecast_df['exhaustion_date_p50'].iloc[0] if not forecast_df.empty else None
    model_type = forecast_df['model_version'].iloc[0] if not forecast_df.empty else "unknown"

    # Create the figure
    fig_burndown = go.Figure()

    # 1. Historical consumption (YELLOW)
    fig_burndown.add_trace(go.Scatter(
        x=daily_spend['usage_date'],
        y=daily_spend['cumulative_cost'].astype(float),
        mode='lines+markers',
        name='Historical Consumption',
        line=dict(width=3, color='gold'),
        marker=dict(size=4, color='orange')
    ))

    # 2. Forecast consumption (RED) - only future dates
    last_actual_date = daily_spend['usage_date'].max()
    future_forecast = forecast_df[forecast_df['forecast_date'] > last_actual_date]

    if not future_forecast.empty:
        fig_burndown.add_trace(go.Scatter(
            x=future_forecast['forecast_date'],
            y=future_forecast['predicted_cumulative'],
            mode='lines',
            name='ML Forecast (Prophet)',
            line=dict(width=3, color='red')
        ))

    # 3. Contract Commitment Line (DASHED)
    # Use string dates to avoid timestamp arithmetic issues
    fig_burndown.add_trace(go.Scatter(
        x=[start_date, end_date],
        y=[commitment, commitment],
        mode='lines',
        name=f'Contract Commitment (${commitment:,.0f})',
        line=dict(dash='dash', width=3, color='darkblue'),
        opacity=0.8
    ))

    # Build title with exhaustion info
    if pd.notna(exhaustion_date):
        title = f'Contract Burndown - Forecast Exhaustion: {exhaustion_date} (Model: {model_type})'
    else:
        title = f'Contract Burndown with ML Forecast (Model: {model_type})'

    fig_burndown.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Cumulative Cost ($)',
        hovermode='x unified',
        height=600,
        xaxis=dict(tickformat='%Y-%m-%d', tickangle=45),
        yaxis=dict(tickformat='$,.0f', range=[0, commitment * 1.2]),
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="left", x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )

    fig_burndown.show()

    # Print summary
    print(f"\n{'='*60}")
    print("FORECAST SUMMARY")
    print(f"{'='*60}")
    print(f"Contract ID: {contract_id}")
    print(f"Contract Value: ${commitment:,.2f}")
    print(f"Current Spend: ${float(daily_spend['cumulative_cost'].max()):,.2f}")
    print(f"Model: {model_type}")
    if pd.notna(exhaustion_date):
        print(f"Predicted Exhaustion Date: {exhaustion_date}")
    else:
        print("Predicted Exhaustion Date: Contract will not be exhausted")
    print(f"{'='*60}")

else:
    print("No forecast data available or no consumption data.")
    print("Run: databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Top Consuming Workspaces

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   u.workspace_id,
# MAGIC   u.cloud,
# MAGIC   COUNT(DISTINCT u.sku_name) as sku_count,
# MAGIC   ROUND(SUM(u.usage_quantity), 2) as total_dbu,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as total_cost,
# MAGIC   COUNT(DISTINCT u.usage_date) as active_days,
# MAGIC   ROUND(AVG(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as avg_daily_cost
# MAGIC FROM system.billing.usage u
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC GROUP BY u.workspace_id, u.cloud
# MAGIC ORDER BY total_cost DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Top Consuming SKUs

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   u.sku_name,
# MAGIC   u.cloud,
# MAGIC   u.usage_unit,
# MAGIC   ROUND(SUM(u.usage_quantity), 2) as total_usage,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as total_cost,
# MAGIC   COUNT(DISTINCT u.workspace_id) as workspace_count,
# MAGIC   COUNT(DISTINCT u.usage_date) as active_days
# MAGIC FROM system.billing.usage u
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC GROUP BY u.sku_name, u.cloud, u.usage_unit
# MAGIC ORDER BY total_cost DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Monthly Spend Trend

# COMMAND ----------

monthly_df = spark.sql("""
SELECT
  DATE_TRUNC('MONTH', u.usage_date) as month,
  u.cloud,
  ROUND(SUM(u.usage_quantity), 2) as monthly_dbu,
  ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as monthly_cost,
  COUNT(DISTINCT u.workspace_id) as active_workspaces,
  COUNT(DISTINCT u.sku_name) as unique_skus
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_date >= lp.price_start_time
  AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', u.usage_date), u.cloud
ORDER BY month DESC, u.cloud
""").toPandas()

# Create monthly trend chart
if not monthly_df.empty:
    fig = px.bar(
        monthly_df,
        x='month',
        y='monthly_cost',
        color='cloud',
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
# MAGIC   DATE_TRUNC('MONTH', u.usage_date) as month,
# MAGIC   CASE
# MAGIC     WHEN u.sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
# MAGIC     WHEN u.sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
# MAGIC     WHEN u.sku_name LIKE '%DLT%' OR u.sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
# MAGIC     WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
# MAGIC     WHEN u.sku_name LIKE '%INFERENCE%' OR u.sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
# MAGIC     WHEN u.sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
# MAGIC     WHEN u.sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
# MAGIC     ELSE 'Other'
# MAGIC   END as category,
# MAGIC   u.cloud,
# MAGIC   ROUND(SUM(u.usage_quantity), 2) as total_dbu,
# MAGIC   ROUND(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2) as total_cost
# MAGIC FROM system.billing.usage u
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
# MAGIC GROUP BY DATE_TRUNC('MONTH', u.usage_date), category, u.cloud
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
  am.business_unit_l0,
  am.business_unit_l1,
  am.business_unit_l2,
  am.business_unit_l3,
  am.account_executive,
  am.solutions_architect,
  u.workspace_id,
  u.cloud as cloud_provider,
  u.sku_name,
  u.usage_unit,
  u.usage_quantity,
  u.usage_quantity * COALESCE(lp.pricing.default, 0) as actual_cost,
  lp.pricing.default as list_price_per_unit,
  lp.pricing.default as discounted_price_per_unit,
  u.usage_quantity * COALESCE(lp.pricing.default, 0) as list_cost,
  u.usage_quantity * COALESCE(lp.pricing.default, 0) as discounted_cost,
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
  AND u.cloud = lp.cloud
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
# MAGIC   CONCAT('USD ', FORMAT_NUMBER(SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)), 2)) as value
# MAGIC FROM system.billing.usage u
# MAGIC LEFT JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC   AND u.cloud = lp.cloud
# MAGIC   AND u.usage_date >= lp.price_start_time
# MAGIC   AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
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
# MAGIC   CONCAT('USD ', FORMAT_NUMBER(AVG(daily_cost), 2)) as value
# MAGIC FROM (
# MAGIC   SELECT
# MAGIC     u.usage_date,
# MAGIC     SUM(u.usage_quantity * COALESCE(lp.pricing.default, 0)) as daily_cost
# MAGIC   FROM system.billing.usage u
# MAGIC   LEFT JOIN system.billing.list_prices lp
# MAGIC     ON u.sku_name = lp.sku_name
# MAGIC     AND u.cloud = lp.cloud
# MAGIC     AND u.usage_date >= lp.price_start_time
# MAGIC     AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC   WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
# MAGIC   GROUP BY u.usage_date
# MAGIC );
