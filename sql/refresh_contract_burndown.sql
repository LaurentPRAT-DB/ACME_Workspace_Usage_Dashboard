-- Refresh Contract Burndown Table
-- Creates daily burndown data for active contracts

CREATE OR REPLACE TABLE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown') AS
SELECT
  c.contract_id,
  c.cloud_provider,
  c.start_date,
  c.end_date,
  c.total_value as commitment,
  c.currency,
  c.commitment_type,
  c.notes,
  d.usage_date,
  -- Daily metrics
  SUM(d.actual_cost) as daily_cost,
  -- Cumulative actual consumption
  SUM(SUM(d.actual_cost)) OVER (
    PARTITION BY c.contract_id
    ORDER BY d.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_cost,
  -- Remaining budget
  c.total_value - SUM(SUM(d.actual_cost)) OVER (
    PARTITION BY c.contract_id
    ORDER BY d.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as remaining_budget,
  -- Ideal linear burn (evenly distributed over contract period)
  (DATEDIFF(d.usage_date, c.start_date) * c.total_value /
   GREATEST(DATEDIFF(c.end_date, c.start_date), 1)) as projected_linear_burn,
  -- Days into contract
  DATEDIFF(d.usage_date, c.start_date) as days_elapsed,
  -- Total contract days
  DATEDIFF(c.end_date, c.start_date) as total_contract_days,
  -- Percentage complete (time-wise)
  ROUND(DATEDIFF(d.usage_date, c.start_date) * 100.0 /
        GREATEST(DATEDIFF(c.end_date, c.start_date), 1), 2) as time_pct_complete,
  -- Percentage consumed (budget-wise)
  ROUND(SUM(SUM(d.actual_cost)) OVER (
    PARTITION BY c.contract_id
    ORDER BY d.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) * 100.0 / c.total_value, 2) as budget_pct_consumed,
  -- Current timestamp for freshness tracking
  CURRENT_TIMESTAMP() as refreshed_at
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contracts') c
INNER JOIN IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data') d
  ON c.account_id = d.account_id
  AND c.cloud_provider = d.cloud_provider
  AND d.usage_date BETWEEN c.start_date AND c.end_date
WHERE c.status = 'ACTIVE'
GROUP BY
  c.contract_id,
  c.cloud_provider,
  c.start_date,
  c.end_date,
  c.total_value,
  c.currency,
  c.commitment_type,
  c.notes,
  d.usage_date
ORDER BY c.contract_id, d.usage_date;

-- Create summary view for latest status
CREATE OR REPLACE VIEW IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown_summary') AS
WITH latest_burndown AS (
  SELECT
    contract_id,
    cloud_provider,
    start_date,
    end_date,
    commitment,
    currency,
    MAX(usage_date) as last_usage_date,
    MAX(cumulative_cost) as total_consumed,
    -- BUG FIX: remaining_budget decreases over time, so MAX() returns earliest value
    -- Instead, calculate from commitment - total_consumed
    MAX(days_elapsed) as days_into_contract,
    MAX(total_contract_days) as contract_duration,
    MAX(budget_pct_consumed) as pct_consumed
  FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown')
  GROUP BY contract_id, cloud_provider, start_date, end_date, commitment, currency
)
SELECT
  contract_id,
  cloud_provider,
  start_date,
  end_date,
  commitment,
  total_consumed,
  -- Calculate remaining budget correctly: commitment - consumed
  GREATEST(commitment - total_consumed, 0) as budget_remaining,
  ROUND(total_consumed * 100.0 / commitment, 2) as consumed_pct,
  days_into_contract,
  DATEDIFF(end_date, CURRENT_DATE()) as days_remaining,
  -- Pace analysis
  CASE
    WHEN pct_consumed > (days_into_contract * 100.0 / contract_duration) * 1.2 THEN '🔴 OVER PACE (>20%)'
    WHEN pct_consumed > (days_into_contract * 100.0 / contract_duration) * 1.1 THEN '🟡 ABOVE PACE (>10%)'
    WHEN pct_consumed < (days_into_contract * 100.0 / contract_duration) * 0.8 THEN '🔵 UNDER PACE (<80%)'
    ELSE '🟢 ON PACE'
  END as pace_status,
  -- Projected completion date based on current burn rate (capped at 2032-12-31)
  LEAST(
    CASE
      WHEN total_consumed > 0 AND days_into_contract > 0 THEN
        DATE_ADD(
          start_date,
          CAST((commitment * days_into_contract / total_consumed) AS INT)
        )
      ELSE end_date
    END,
    DATE'2032-12-31'
  ) as projected_end_date,
  last_usage_date
FROM latest_burndown
ORDER BY
  CASE
    WHEN pct_consumed > (days_into_contract * 100.0 / contract_duration) * 1.2 THEN 1
    WHEN pct_consumed > (days_into_contract * 100.0 / contract_duration) * 1.1 THEN 2
    ELSE 3
  END,
  pct_consumed DESC;

-- Display summary
SELECT
  'Contract burndown data refreshed' as status,
  COUNT(DISTINCT contract_id) as contract_count,
  COUNT(*) as total_data_points,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown');
