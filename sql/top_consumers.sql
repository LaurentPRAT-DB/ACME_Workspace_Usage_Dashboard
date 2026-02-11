-- Top Consumers Analysis
-- Identifies top consuming workspaces, SKUs, and jobs

-- Top 10 workspaces by cost
CREATE OR REPLACE TEMP VIEW top_workspaces_view AS
SELECT
  workspace_id,
  cloud_provider,
  COUNT(DISTINCT usage_date) as active_days,
  COUNT(DISTINCT sku_name) as unique_skus,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(actual_cost), 2) as total_cost,
  ROUND(AVG(actual_cost), 2) as avg_daily_cost
FROM {{catalog}}.{{schema}}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id, cloud_provider
ORDER BY total_cost DESC
LIMIT 10;

-- Top 10 SKUs by cost
CREATE OR REPLACE TEMP VIEW top_skus_view AS
SELECT
  sku_name,
  cloud_provider,
  product_category,
  COUNT(DISTINCT workspace_id) as workspace_count,
  ROUND(SUM(usage_quantity), 2) as total_usage,
  ROUND(SUM(actual_cost), 2) as total_cost,
  ROUND(AVG(price_per_unit), 4) as avg_price_per_unit
FROM {{catalog}}.{{schema}}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY sku_name, cloud_provider, product_category
ORDER BY total_cost DESC
LIMIT 10;

-- Top 10 jobs by cost
CREATE OR REPLACE TEMP VIEW top_jobs_view AS
SELECT
  job_id,
  job_name,
  cloud_provider,
  COUNT(DISTINCT usage_date) as run_days,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(actual_cost), 2) as total_cost,
  ROUND(AVG(actual_cost), 2) as avg_run_cost
FROM {{catalog}}.{{schema}}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND job_id IS NOT NULL
GROUP BY job_id, job_name, cloud_provider
ORDER BY total_cost DESC
LIMIT 10;

-- Top 10 users by cost
CREATE OR REPLACE TEMP VIEW top_users_view AS
SELECT
  run_as,
  cloud_provider,
  COUNT(DISTINCT usage_date) as active_days,
  COUNT(DISTINCT workspace_id) as workspace_count,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM {{catalog}}.{{schema}}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND run_as IS NOT NULL
GROUP BY run_as, cloud_provider
ORDER BY total_cost DESC
LIMIT 10;

-- Summary report
SELECT 'TOP WORKSPACES' as report_section, * FROM top_workspaces_view
UNION ALL
SELECT 'TOP SKUS' as report_section,
       sku_name as workspace_id,
       cloud_provider,
       workspace_count as active_days,
       NULL as unique_skus,
       total_usage as total_dbu,
       total_cost,
       NULL as avg_daily_cost
FROM top_skus_view
UNION ALL
SELECT 'TOP JOBS' as report_section,
       COALESCE(job_name, job_id) as workspace_id,
       cloud_provider,
       run_days as active_days,
       NULL as unique_skus,
       total_dbu,
       total_cost,
       avg_run_cost as avg_daily_cost
FROM top_jobs_view
UNION ALL
SELECT 'TOP USERS' as report_section,
       run_as as workspace_id,
       cloud_provider,
       active_days,
       workspace_count as unique_skus,
       total_dbu,
       total_cost,
       NULL as avg_daily_cost
FROM top_users_view;
