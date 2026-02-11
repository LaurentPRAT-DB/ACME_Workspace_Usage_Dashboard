-- Cost Anomalies Detection
-- Identifies unusual spending patterns

-- Day-over-day anomalies
CREATE OR REPLACE TEMP VIEW daily_anomalies AS
WITH daily_costs AS (
  SELECT
    usage_date,
    cloud_provider,
    workspace_id,
    SUM(actual_cost) as daily_cost,
    LAG(SUM(actual_cost)) OVER (
      PARTITION BY cloud_provider, workspace_id
      ORDER BY usage_date
    ) as prev_day_cost
  FROM {{catalog}}.{{schema}}.dashboard_data
  WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  GROUP BY usage_date, cloud_provider, workspace_id
)
SELECT
  usage_date,
  cloud_provider,
  workspace_id,
  ROUND(daily_cost, 2) as today_cost,
  ROUND(prev_day_cost, 2) as yesterday_cost,
  ROUND(daily_cost - prev_day_cost, 2) as cost_change,
  ROUND((daily_cost - prev_day_cost) / NULLIF(prev_day_cost, 0) * 100, 1) as pct_change
FROM daily_costs
WHERE prev_day_cost > 0
  AND ABS((daily_cost - prev_day_cost) / prev_day_cost) > 0.5  -- 50% change
ORDER BY ABS(pct_change) DESC;

-- Weekend usage anomalies
CREATE OR REPLACE TEMP VIEW weekend_anomalies AS
SELECT
  usage_date,
  DAYOFWEEK(usage_date) as day_of_week,
  workspace_id,
  cloud_provider,
  ROUND(SUM(actual_cost), 2) as cost
FROM {{catalog}}.{{schema}}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND DAYOFWEEK(usage_date) IN (1, 7)  -- Sunday or Saturday
  AND actual_cost > 100  -- Threshold
GROUP BY usage_date, workspace_id, cloud_provider
ORDER BY cost DESC;

-- New workspaces (first-time usage in last 30 days)
CREATE OR REPLACE TEMP VIEW new_workspaces AS
WITH first_usage AS (
  SELECT
    workspace_id,
    cloud_provider,
    MIN(usage_date) as first_seen
  FROM {{catalog}}.{{schema}}.dashboard_data
  GROUP BY workspace_id, cloud_provider
)
SELECT
  f.workspace_id,
  f.cloud_provider,
  f.first_seen,
  DATEDIFF(CURRENT_DATE(), f.first_seen) as days_active,
  COUNT(DISTINCT d.usage_date) as usage_days,
  ROUND(SUM(d.actual_cost), 2) as total_cost
FROM first_usage f
JOIN {{catalog}}.{{schema}}.dashboard_data d
  ON f.workspace_id = d.workspace_id
  AND f.cloud_provider = d.cloud_provider
WHERE f.first_seen >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY f.workspace_id, f.cloud_provider, f.first_seen
ORDER BY total_cost DESC;

-- Summary of all anomalies
SELECT
  'Daily Anomalies' as anomaly_type,
  COUNT(*) as count,
  ROUND(SUM(cost_change), 2) as total_impact
FROM daily_anomalies

UNION ALL

SELECT
  'Weekend Usage' as anomaly_type,
  COUNT(*) as count,
  ROUND(SUM(cost), 2) as total_impact
FROM weekend_anomalies

UNION ALL

SELECT
  'New Workspaces' as anomaly_type,
  COUNT(*) as count,
  ROUND(SUM(total_cost), 2) as total_impact
FROM new_workspaces;

-- Detailed daily anomalies
SELECT
  'DAILY SPIKE' as alert_type,
  usage_date,
  cloud_provider,
  workspace_id,
  today_cost,
  yesterday_cost,
  pct_change
FROM daily_anomalies
WHERE pct_change > 0  -- Only increases
LIMIT 10;
