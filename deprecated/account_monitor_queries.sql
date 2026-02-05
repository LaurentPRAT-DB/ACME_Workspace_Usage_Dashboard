-- ============================================================================
-- DATABRICKS ACCOUNT MONITOR - SQL QUERIES
-- Recreates IBM Account Monitor using Databricks System Tables
-- ============================================================================

-- ============================================================================
-- 1. ACCOUNT OVERVIEW METRICS
-- ============================================================================

-- Top SKU Count (distinct SKU types used)
CREATE OR REPLACE TEMP VIEW account_overview_sku AS
SELECT
  COUNT(DISTINCT sku_name) as top_sku_count,
  COUNT(DISTINCT workspace_id) as top_workspace_count,
  MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365);  -- Last 12 months

-- ============================================================================
-- 2. LATEST DATA DATES - Data Freshness Check
-- ============================================================================

CREATE OR REPLACE TEMP VIEW latest_data_dates AS
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

-- ============================================================================
-- 3. ACCOUNT INFO
-- ============================================================================

-- Account/Workspace metadata
-- Note: You'll need to create a custom table for Salesforce IDs and business units
CREATE OR REPLACE TEMP VIEW account_info AS
SELECT DISTINCT
  account_id,
  workspace_id,
  -- Custom fields - populate from your org structure
  'TBD' as salesforce_id,
  'TBD' as business_unit_l0,
  'TBD' as business_unit_l1,
  'TBD' as business_unit_l2,
  'TBD' as business_unit_l3,
  'TBD' as account_executive,
  'TBD' as solutions_architect,
  'TBD' as delivery_solutions_architect
FROM system.billing.usage
LIMIT 1;

-- ============================================================================
-- 4. TOTAL SPEND IN TIMEFRAME
-- ============================================================================

CREATE OR REPLACE TEMP VIEW total_spend_timeframe AS
SELECT
  account_id,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  SUM(usage_quantity) as dbu,
  SUM(usage_quantity * list_price_per_unit) as list_price,
  SUM(usage_quantity * pricing.default_price_per_unit) as discounted_price,
  SUM(usage_metadata.total_price) as revenue
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices pricing
  ON u.sku_name = pricing.sku_name
  AND u.usage_date >= pricing.price_start_time
  AND (u.usage_date < pricing.price_end_time OR pricing.price_end_time IS NULL)
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY account_id, cloud_provider
ORDER BY cloud_provider;

-- ============================================================================
-- 5. DETAILED USAGE BY SKU AND WORKSPACE
-- ============================================================================

CREATE OR REPLACE TEMP VIEW detailed_usage AS
SELECT
  usage_date,
  account_id,
  workspace_id,
  cloud_provider,
  sku_name,
  usage_unit,
  SUM(usage_quantity) as total_usage,
  SUM(usage_quantity * list_price_per_unit) as list_cost,
  SUM(usage_metadata.total_price) as actual_cost,
  COUNT(DISTINCT usage_record_id) as record_count
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY
  usage_date,
  account_id,
  workspace_id,
  cloud_provider,
  sku_name,
  usage_unit
ORDER BY usage_date DESC, actual_cost DESC;

-- ============================================================================
-- 6. DAILY CONSUMPTION TREND (for Contract Burndown Chart)
-- ============================================================================

CREATE OR REPLACE TEMP VIEW daily_consumption_trend AS
SELECT
  usage_date,
  cloud_provider,
  SUM(usage_quantity) as daily_dbu,
  SUM(usage_metadata.total_price) as daily_cost,
  SUM(SUM(usage_metadata.total_price)) OVER (
    PARTITION BY cloud_provider
    ORDER BY usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY usage_date, cloud_provider
ORDER BY usage_date;

-- ============================================================================
-- 7. TOP CONSUMING WORKSPACES
-- ============================================================================

CREATE OR REPLACE TEMP VIEW top_workspaces AS
SELECT
  workspace_id,
  cloud_provider,
  SUM(usage_quantity) as total_dbu,
  SUM(usage_metadata.total_price) as total_cost,
  COUNT(DISTINCT sku_name) as sku_count,
  COUNT(DISTINCT usage_date) as active_days
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)  -- Last 90 days
GROUP BY workspace_id, cloud_provider
ORDER BY total_cost DESC
LIMIT 10;

-- ============================================================================
-- 8. TOP CONSUMING SKUS
-- ============================================================================

CREATE OR REPLACE TEMP VIEW top_skus AS
SELECT
  sku_name,
  cloud_provider,
  usage_unit,
  SUM(usage_quantity) as total_usage,
  SUM(usage_metadata.total_price) as total_cost,
  COUNT(DISTINCT workspace_id) as workspace_count,
  COUNT(DISTINCT usage_date) as active_days
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)  -- Last 90 days
GROUP BY sku_name, cloud_provider, usage_unit
ORDER BY total_cost DESC
LIMIT 10;

-- ============================================================================
-- 9. MONTHLY SPEND SUMMARY
-- ============================================================================

CREATE OR REPLACE TEMP VIEW monthly_spend AS
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  SUM(usage_quantity) as monthly_dbu,
  SUM(usage_metadata.total_price) as monthly_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces,
  COUNT(DISTINCT sku_name) as unique_skus
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), cloud_provider
ORDER BY month DESC, cloud_provider;

-- ============================================================================
-- 10. COST BY PRODUCT CATEGORY
-- ============================================================================

CREATE OR REPLACE TEMP VIEW cost_by_category AS
SELECT
  usage_date,
  CASE
    WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
    WHEN sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
    WHEN sku_name LIKE '%DLT%' OR sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
    WHEN sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
    WHEN sku_name LIKE '%INFERENCE%' OR sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
    WHEN sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
    WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
    ELSE 'Other'
  END as category,
  cloud_provider,
  SUM(usage_quantity) as total_dbu,
  SUM(usage_metadata.total_price) as total_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY usage_date, category, cloud_provider
ORDER BY usage_date DESC, total_cost DESC;

-- ============================================================================
-- 11. QUERY TO GET ALL DATA FOR DASHBOARD
-- ============================================================================

-- Main dashboard query
SELECT
  u.usage_date,
  u.account_id,
  u.workspace_id,
  u.cloud_provider,
  u.sku_name,
  u.usage_unit,
  u.usage_quantity,
  u.usage_metadata.total_price as actual_cost,
  u.list_price_per_unit,
  lp.pricing.default_price_per_unit as discounted_price_per_unit,
  u.usage_quantity * u.list_price_per_unit as list_cost,
  u.usage_quantity * lp.pricing.default_price_per_unit as discounted_cost,
  u.usage_metadata.job_id,
  u.usage_metadata.warehouse_id,
  u.usage_metadata.cluster_id,
  u.usage_metadata.instance_pool_id,
  u.custom_tags
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.usage_date >= lp.price_start_time
  AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
ORDER BY u.usage_date DESC;
