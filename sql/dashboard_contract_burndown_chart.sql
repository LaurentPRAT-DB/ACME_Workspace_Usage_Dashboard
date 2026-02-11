-- Contract Burndown Chart Query for Lakeview Dashboard
-- Shows actual vs projected consumption over time

SELECT
  contract_id,
  usage_date as date,
  cumulative_cost as actual_consumption,
  projected_linear_burn as ideal_consumption,
  commitment as contract_value,
  remaining_budget,
  budget_pct_consumed as pct_consumed,
  CONCAT(contract_id, ' ($', FORMAT_NUMBER(commitment, 0), ')') as contract_label
FROM {{catalog}}.{{schema}}.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)  -- Last 90 days for better visibility
ORDER BY contract_id, usage_date;
