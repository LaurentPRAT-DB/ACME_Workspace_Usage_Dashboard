-- Monthly Summary Report
-- Generates comprehensive monthly cost and usage summary

-- ============================================================================
-- Step 1: Create temp views for reusable calculations
-- ============================================================================

-- Previous month date range
CREATE OR REPLACE TEMP VIEW prev_month_range AS
SELECT
  DATE_TRUNC('MONTH', DATE_SUB(CURRENT_DATE(), 30)) as month_start,
  LAST_DAY(DATE_SUB(CURRENT_DATE(), 30)) as month_end;

-- Monthly statistics by cloud provider
CREATE OR REPLACE TEMP VIEW monthly_stats_view AS
SELECT
  d.cloud_provider,
  COUNT(DISTINCT d.usage_date) as days_with_data,
  COUNT(DISTINCT d.workspace_id) as active_workspaces,
  COUNT(DISTINCT d.sku_name) as unique_skus,
  ROUND(SUM(d.usage_quantity), 2) as total_dbu,
  ROUND(SUM(d.actual_cost), 2) as total_cost,
  ROUND(AVG(dc.daily_cost), 2) as avg_daily_cost,
  ROUND(MAX(dc.daily_cost), 2) as max_daily_cost,
  ROUND(MIN(dc.daily_cost), 2) as min_daily_cost
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data') d
CROSS JOIN prev_month_range pm
JOIN (
  SELECT usage_date, SUM(actual_cost) as daily_cost
  FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
  GROUP BY usage_date
) dc ON d.usage_date = dc.usage_date
WHERE d.usage_date >= pm.month_start
  AND d.usage_date <= pm.month_end
GROUP BY d.cloud_provider;

-- Product category breakdown
CREATE OR REPLACE TEMP VIEW product_breakdown_view AS
SELECT
  d.product_category,
  ROUND(SUM(d.actual_cost), 2) as cost,
  ROUND(SUM(d.actual_cost) * 100.0 / NULLIF(SUM(SUM(d.actual_cost)) OVER (), 0), 1) as pct
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data') d
CROSS JOIN prev_month_range pm
WHERE d.usage_date >= pm.month_start
  AND d.usage_date <= pm.month_end
GROUP BY d.product_category;

-- Month-over-month comparison
CREATE OR REPLACE TEMP VIEW month_over_month_view AS
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  ROUND(SUM(actual_cost), 2) as monthly_cost,
  LAG(ROUND(SUM(actual_cost), 2)) OVER (
    PARTITION BY cloud_provider
    ORDER BY DATE_TRUNC('MONTH', usage_date)
  ) as prev_month_cost
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY DATE_TRUNC('MONTH', usage_date), cloud_provider;

-- ============================================================================
-- Step 2: Generate reports
-- ============================================================================

-- Main summary
SELECT
  (SELECT month_start FROM prev_month_range) as report_month,
  'MONTHLY SUMMARY' as section,
  ms.cloud_provider,
  ms.days_with_data,
  ms.active_workspaces,
  ms.unique_skus,
  ms.total_dbu,
  ms.total_cost,
  ms.avg_daily_cost,
  ms.max_daily_cost,
  ms.min_daily_cost
FROM monthly_stats_view ms;

-- Product category breakdown
SELECT
  (SELECT month_start FROM prev_month_range) as report_month,
  'PRODUCT BREAKDOWN' as section,
  product_category,
  cost,
  pct as cost_pct
FROM product_breakdown_view
ORDER BY cost DESC;

-- Month-over-month comparison
SELECT
  month,
  'MOM COMPARISON' as section,
  cloud_provider,
  monthly_cost,
  prev_month_cost,
  ROUND(monthly_cost - COALESCE(prev_month_cost, 0), 2) as cost_change,
  ROUND((monthly_cost - prev_month_cost) / NULLIF(prev_month_cost, 0) * 100, 1) as pct_change
FROM month_over_month_view
WHERE prev_month_cost IS NOT NULL
ORDER BY month DESC;
