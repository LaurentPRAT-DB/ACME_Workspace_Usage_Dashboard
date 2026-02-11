-- Refresh Dashboard Data
-- Loads usage and cost data from system tables into dashboard_data table

-- Replace the dashboard_data table with fresh data from last 365 days
CREATE OR REPLACE TABLE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data') AS
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
LEFT JOIN IDENTIFIER({{catalog}} || '.' || {{schema}} || '.account_metadata') am
  ON u.account_id = am.account_id
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL';

-- Refresh daily summary table
CREATE OR REPLACE TABLE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.daily_summary') AS
SELECT
  usage_date,
  cloud_provider,
  workspace_id,
  SUM(usage_quantity) as total_dbu,
  SUM(actual_cost) as total_cost,
  COUNT(DISTINCT sku_name) as unique_skus,
  CURRENT_TIMESTAMP() as updated_at
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
GROUP BY usage_date, cloud_provider, workspace_id;

-- Return summary
SELECT
  'Dashboard data refreshed' as status,
  COUNT(*) as total_records,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date,
  SUM(actual_cost) as total_cost
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data');
