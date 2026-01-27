-- ============================================================================
-- DATABRICKS ACCOUNT MONITOR - CORRECTED SQL QUERIES
-- Uses ACTUAL system table schema verified from Databricks documentation
-- Unity Catalog enabled
-- ============================================================================

-- IMPORTANT: Replace 'main' with your actual catalog name throughout this file
-- USE CATALOG main;

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
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND record_type = 'ORIGINAL';  -- Exclude corrections

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
WHERE record_type = 'ORIGINAL';

-- ============================================================================
-- 3. ACCOUNT INFO
-- ============================================================================

-- Account/Workspace metadata from custom Unity Catalog table
CREATE OR REPLACE TEMP VIEW account_info AS
SELECT
  am.account_id,
  am.customer_name,
  am.salesforce_id,
  am.business_unit_l0,
  am.business_unit_l1,
  am.business_unit_l2,
  am.business_unit_l3,
  am.account_executive,
  am.solutions_architect,
  am.delivery_solutions_architect,
  COUNT(DISTINCT u.workspace_id) as workspace_count
FROM main.account_monitoring.account_metadata am
LEFT JOIN system.billing.usage u
  ON am.account_id = u.account_id
  AND u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
GROUP BY ALL;

-- ============================================================================
-- 4. TOTAL SPEND IN TIMEFRAME
-- ============================================================================

CREATE OR REPLACE TEMP VIEW total_spend_timeframe AS
SELECT
  u.account_id,
  u.cloud as cloud,
  MIN(u.usage_start_time) as start_date,
  MAX(u.usage_end_time) as end_date,
  SUM(u.usage_quantity) as dbu,
  -- Calculate costs using list_prices join
  SUM(u.usage_quantity * CAST(lp.pricing.default AS DECIMAL(20,10))) as list_price,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as discounted_price,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as revenue
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.account_id, u.cloud
ORDER BY u.cloud;

-- ============================================================================
-- 5. DETAILED USAGE BY SKU AND WORKSPACE
-- ============================================================================

CREATE OR REPLACE TEMP VIEW detailed_usage AS
SELECT
  u.usage_date,
  u.account_id,
  u.workspace_id,
  u.cloud,
  u.sku_name,
  u.usage_unit,
  SUM(u.usage_quantity) as total_usage,
  SUM(u.usage_quantity * CAST(lp.pricing.default AS DECIMAL(20,10))) as list_cost,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as actual_cost,
  COUNT(DISTINCT u.record_id) as record_count
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
GROUP BY
  u.usage_date,
  u.account_id,
  u.workspace_id,
  u.cloud,
  u.sku_name,
  u.usage_unit
ORDER BY u.usage_date DESC, actual_cost DESC;

-- ============================================================================
-- 6. DAILY CONSUMPTION TREND (for Contract Burndown Chart)
-- ============================================================================

CREATE OR REPLACE TEMP VIEW daily_consumption_trend AS
SELECT
  u.usage_date,
  u.cloud,
  SUM(u.usage_quantity) as daily_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost,
  SUM(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)))) OVER (
    PARTITION BY u.cloud
    ORDER BY u.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.usage_date, u.cloud
ORDER BY u.usage_date;

-- ============================================================================
-- 7. TOP CONSUMING WORKSPACES
-- ============================================================================

CREATE OR REPLACE TEMP VIEW top_workspaces AS
SELECT
  u.workspace_id,
  u.cloud,
  SUM(u.usage_quantity) as total_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost,
  COUNT(DISTINCT u.sku_name) as sku_count,
  COUNT(DISTINCT u.usage_date) as active_days
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.workspace_id, u.cloud
ORDER BY total_cost DESC
LIMIT 10;

-- ============================================================================
-- 8. TOP CONSUMING SKUS
-- ============================================================================

CREATE OR REPLACE TEMP VIEW top_skus AS
SELECT
  u.sku_name,
  u.cloud,
  u.usage_unit,
  SUM(u.usage_quantity) as total_usage,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost,
  COUNT(DISTINCT u.workspace_id) as workspace_count,
  COUNT(DISTINCT u.usage_date) as active_days
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.sku_name, u.cloud, u.usage_unit
ORDER BY total_cost DESC
LIMIT 10;

-- ============================================================================
-- 9. MONTHLY SPEND SUMMARY
-- ============================================================================

CREATE OR REPLACE TEMP VIEW monthly_spend AS
SELECT
  DATE_TRUNC('MONTH', u.usage_date) as month,
  u.cloud,
  SUM(u.usage_quantity) as monthly_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as monthly_cost,
  COUNT(DISTINCT u.workspace_id) as active_workspaces,
  COUNT(DISTINCT u.sku_name) as unique_skus
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
GROUP BY DATE_TRUNC('MONTH', u.usage_date), u.cloud
ORDER BY month DESC, u.cloud;

-- ============================================================================
-- 10. COST BY PRODUCT CATEGORY
-- ============================================================================

CREATE OR REPLACE TEMP VIEW cost_by_category AS
SELECT
  u.usage_date,
  CASE
    WHEN u.sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
    WHEN u.sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
    WHEN u.sku_name LIKE '%DLT%' OR u.sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
    WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
    WHEN u.sku_name LIKE '%INFERENCE%' OR u.sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
    WHEN u.sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
    WHEN u.sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
    ELSE 'Other'
  END as category,
  u.cloud,
  SUM(u.usage_quantity) as total_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 90)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.usage_date, category, u.cloud
ORDER BY u.usage_date DESC, total_cost DESC;

-- ============================================================================
-- 11. CONTRACT CONSUMPTION TRACKING
-- ============================================================================

CREATE OR REPLACE TEMP VIEW contract_consumption AS
SELECT
  c.contract_id,
  c.cloud_provider as platform,
  c.start_date,
  c.end_date,
  c.total_value,
  COALESCE(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 0) as consumed,
  ROUND(
    COALESCE(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 0)
    / c.total_value * 100,
    1
  ) as consumed_pct
FROM main.account_monitoring.contracts c
LEFT JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND c.cloud_provider = u.cloud
  AND u.usage_date BETWEEN c.start_date AND c.end_date
  AND u.record_type = 'ORIGINAL'
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE c.status = 'ACTIVE'
GROUP BY
  c.contract_id,
  c.cloud_provider,
  c.start_date,
  c.end_date,
  c.total_value
ORDER BY c.start_date;

-- ============================================================================
-- 12. CONTRACT BURNDOWN DATA
-- ============================================================================

CREATE OR REPLACE TEMP VIEW contract_burndown_data AS
SELECT
  c.contract_id,
  c.start_date,
  c.end_date,
  c.total_value as commitment,
  u.usage_date,
  u.cloud,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost,
  SUM(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)))) OVER (
    PARTITION BY c.contract_id
    ORDER BY u.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost
FROM main.account_monitoring.contracts c
LEFT JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND c.cloud_provider = u.cloud
  AND u.usage_date BETWEEN c.start_date AND c.end_date
  AND u.record_type = 'ORIGINAL'
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE c.status = 'ACTIVE'
GROUP BY
  c.contract_id,
  c.start_date,
  c.end_date,
  c.total_value,
  u.usage_date,
  u.cloud
ORDER BY u.usage_date;

-- ============================================================================
-- 13. MAIN DASHBOARD EXPORT QUERY
-- ============================================================================

-- This is the comprehensive query for dashboard_data table
CREATE OR REPLACE TABLE main.account_monitoring.dashboard_data AS
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
  u.cloud as cloud_provider,
  u.sku_name,
  u.usage_unit,
  u.usage_quantity,
  -- Calculated cost fields
  CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)) as price_per_unit,
  u.usage_quantity * CAST(lp.pricing.default AS DECIMAL(20,10)) as list_cost,
  u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)) as actual_cost,
  -- Product categorization
  CASE
    WHEN u.sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
    WHEN u.sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
    WHEN u.sku_name LIKE '%DLT%' OR u.sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
    WHEN u.sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
    WHEN u.sku_name LIKE '%INFERENCE%' OR u.sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
    WHEN u.sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
    WHEN u.sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
    ELSE 'Other'
  END as product_category,
  -- Metadata fields
  u.usage_metadata.job_id,
  u.usage_metadata.job_name,
  u.usage_metadata.warehouse_id,
  u.usage_metadata.cluster_id,
  u.identity_metadata.run_as,
  u.custom_tags,
  CURRENT_TIMESTAMP() as updated_at
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
LEFT JOIN main.account_monitoring.account_metadata am
  ON u.account_id = am.account_id
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL';

-- ============================================================================
-- EXAMPLE QUERIES FOR TESTING
-- ============================================================================

-- Test 1: Check if system tables are accessible
SELECT COUNT(*) as record_count
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);

-- Test 2: Get latest data date
SELECT MAX(usage_date) as latest_date
FROM system.billing.usage;

-- Test 3: Yesterday's total cost
SELECT
  u.cloud,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL'
GROUP BY u.cloud;

-- Test 4: Verify pricing join works
SELECT
  u.sku_name,
  u.usage_unit,
  lp.pricing.default as list_price,
  lp.pricing.effective_list.default as effective_price,
  COUNT(*) as record_count
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL'
GROUP BY u.sku_name, u.usage_unit, lp.pricing.default, lp.pricing.effective_list.default
LIMIT 10;
