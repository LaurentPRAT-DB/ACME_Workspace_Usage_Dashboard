-- Contract Analysis
-- Analyzes contract consumption and pace

WITH contract_consumption AS (
  SELECT
    c.contract_id,
    c.cloud_provider,
    c.start_date,
    c.end_date,
    c.total_value,
    DATEDIFF(c.end_date, c.start_date) as total_days,
    DATEDIFF(CURRENT_DATE(), c.start_date) as elapsed_days,
    DATEDIFF(c.end_date, CURRENT_DATE()) as remaining_days,
    SUM(d.actual_cost) as consumed
  FROM {{catalog}}.{{schema}}.contracts c
  LEFT JOIN {{catalog}}.{{schema}}.dashboard_data d
    ON c.account_id = d.account_id
    AND c.cloud_provider = d.cloud_provider
    AND d.usage_date BETWEEN c.start_date AND c.end_date
  WHERE c.status = 'ACTIVE'
    AND c.end_date >= CURRENT_DATE()
  GROUP BY ALL
)
SELECT
  contract_id,
  cloud_provider,
  start_date,
  end_date,
  ROUND(total_value, 2) as total_value,
  ROUND(consumed, 2) as consumed,
  ROUND(total_value - consumed, 2) as remaining,
  ROUND(consumed * 100.0 / total_value, 1) as consumed_pct,
  ROUND(elapsed_days * 100.0 / total_days, 1) as time_elapsed_pct,
  remaining_days,
  -- Pace analysis
  CASE
    WHEN consumed / total_value > elapsed_days / total_days * 1.2 THEN '🔴 OVER PACE'
    WHEN consumed / total_value > elapsed_days / total_days * 1.1 THEN '🟡 ABOVE PACE'
    WHEN consumed / total_value < elapsed_days / total_days * 0.8 THEN '🔵 UNDER PACE'
    ELSE '🟢 ON PACE'
  END as pace_status,
  -- Projected end date based on current rate
  DATE_ADD(
    CURRENT_DATE(),
    CAST((total_value - consumed) / (consumed / NULLIF(elapsed_days, 0)) AS INT)
  ) as projected_end_date
FROM contract_consumption
ORDER BY
  CASE
    WHEN consumed / total_value > elapsed_days / total_days * 1.2 THEN 1
    WHEN consumed / total_value > elapsed_days / total_days * 1.1 THEN 2
    ELSE 3
  END,
  consumed_pct DESC;
