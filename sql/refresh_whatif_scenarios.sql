-- Refresh What-If Scenarios
-- SQL-based refresh for scenario summary metrics
-- Run this after consumption data updates to refresh what-if analysis

-- ============================================================================
-- Step 1: Refresh scenario_burndown from contract_burndown
-- Apply discount factors to historical consumption
-- ============================================================================

MERGE INTO IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_burndown') AS target
USING (
  SELECT
    ds.scenario_id,
    ds.contract_id,
    cb.usage_date,
    cb.daily_cost AS original_daily_cost,
    cb.cumulative_cost AS original_cumulative,
    cb.daily_cost * (1 - ds.discount_pct / 100) AS simulated_daily_cost,
    SUM(cb.daily_cost * (1 - ds.discount_pct / 100)) OVER (
      PARTITION BY ds.scenario_id ORDER BY cb.usage_date
    ) AS simulated_cumulative,
    ds.adjusted_total_value AS scenario_commitment,
    ds.adjusted_total_value - SUM(cb.daily_cost * (1 - ds.discount_pct / 100)) OVER (
      PARTITION BY ds.scenario_id ORDER BY cb.usage_date
    ) AS simulated_remaining,
    cb.daily_cost - cb.daily_cost * (1 - ds.discount_pct / 100) AS daily_savings,
    SUM(cb.daily_cost - cb.daily_cost * (1 - ds.discount_pct / 100)) OVER (
      PARTITION BY ds.scenario_id ORDER BY cb.usage_date
    ) AS cumulative_savings
  FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.discount_scenarios') ds
  INNER JOIN IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown') cb
    ON ds.contract_id = cb.contract_id
  WHERE ds.status = 'ACTIVE'
) AS source
ON target.scenario_id = source.scenario_id AND target.usage_date = source.usage_date
WHEN MATCHED THEN UPDATE SET
  original_daily_cost = source.original_daily_cost,
  original_cumulative = source.original_cumulative,
  simulated_daily_cost = source.simulated_daily_cost,
  simulated_cumulative = source.simulated_cumulative,
  scenario_commitment = source.scenario_commitment,
  simulated_remaining = source.simulated_remaining,
  daily_savings = source.daily_savings,
  cumulative_savings = source.cumulative_savings,
  calculated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
  scenario_id, contract_id, usage_date, original_daily_cost, original_cumulative,
  simulated_daily_cost, simulated_cumulative, scenario_commitment, simulated_remaining,
  daily_savings, cumulative_savings, calculated_at
) VALUES (
  source.scenario_id, source.contract_id, source.usage_date, source.original_daily_cost,
  source.original_cumulative, source.simulated_daily_cost, source.simulated_cumulative,
  source.scenario_commitment, source.simulated_remaining, source.daily_savings,
  source.cumulative_savings, CURRENT_TIMESTAMP()
);

-- ============================================================================
-- Step 2: Refresh scenario_forecast from contract_forecast
-- Scale Prophet predictions by discount factor
-- ============================================================================

MERGE INTO IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_forecast') AS target
USING (
  WITH baseline_exhaustion AS (
    SELECT
      contract_id,
      MAX(exhaustion_date_p50) AS baseline_exhaustion_date
    FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast')
    GROUP BY contract_id
  ),
  scaled_forecasts AS (
    SELECT
      ds.scenario_id,
      ds.contract_id,
      cf.forecast_date,
      cf.predicted_daily_cost * (1 - ds.discount_pct / 100) AS predicted_daily_cost,
      SUM(cf.predicted_daily_cost * (1 - ds.discount_pct / 100)) OVER (
        PARTITION BY ds.scenario_id ORDER BY cf.forecast_date
      ) AS predicted_cumulative,
      cf.lower_bound * (1 - ds.discount_pct / 100) AS lower_bound,
      cf.upper_bound * (1 - ds.discount_pct / 100) AS upper_bound,
      cf.model_version,
      be.baseline_exhaustion_date,
      ds.adjusted_total_value AS commitment
    FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.discount_scenarios') ds
    INNER JOIN IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast') cf
      ON ds.contract_id = cf.contract_id
    LEFT JOIN baseline_exhaustion be
      ON ds.contract_id = be.contract_id
    WHERE ds.status = 'ACTIVE'
  ),
  exhaustion_calc AS (
    SELECT
      *,
      MIN(CASE WHEN predicted_cumulative >= commitment THEN forecast_date END) OVER (PARTITION BY scenario_id) AS exhaustion_date_p50,
      MIN(CASE WHEN SUM(upper_bound) OVER (PARTITION BY scenario_id ORDER BY forecast_date) >= commitment THEN forecast_date END) OVER (PARTITION BY scenario_id) AS exhaustion_date_p10,
      MIN(CASE WHEN SUM(lower_bound) OVER (PARTITION BY scenario_id ORDER BY forecast_date) >= commitment THEN forecast_date END) OVER (PARTITION BY scenario_id) AS exhaustion_date_p90
    FROM scaled_forecasts
  )
  SELECT
    scenario_id,
    contract_id,
    forecast_date,
    predicted_daily_cost,
    predicted_cumulative,
    lower_bound,
    upper_bound,
    exhaustion_date_p10,
    exhaustion_date_p50,
    exhaustion_date_p90,
    DATEDIFF(exhaustion_date_p50, forecast_date) AS days_to_exhaustion,
    baseline_exhaustion_date,
    DATEDIFF(exhaustion_date_p50, baseline_exhaustion_date) AS days_extended,
    model_version
  FROM exhaustion_calc
) AS source
ON target.scenario_id = source.scenario_id AND target.forecast_date = source.forecast_date
WHEN MATCHED THEN UPDATE SET
  predicted_daily_cost = source.predicted_daily_cost,
  predicted_cumulative = source.predicted_cumulative,
  lower_bound = source.lower_bound,
  upper_bound = source.upper_bound,
  exhaustion_date_p10 = source.exhaustion_date_p10,
  exhaustion_date_p50 = source.exhaustion_date_p50,
  exhaustion_date_p90 = source.exhaustion_date_p90,
  days_to_exhaustion = source.days_to_exhaustion,
  baseline_exhaustion_date = source.baseline_exhaustion_date,
  days_extended = source.days_extended,
  model_version = source.model_version,
  created_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
  scenario_id, contract_id, forecast_date, predicted_daily_cost, predicted_cumulative,
  lower_bound, upper_bound, exhaustion_date_p10, exhaustion_date_p50, exhaustion_date_p90,
  days_to_exhaustion, baseline_exhaustion_date, days_extended, model_version, created_at
) VALUES (
  source.scenario_id, source.contract_id, source.forecast_date, source.predicted_daily_cost,
  source.predicted_cumulative, source.lower_bound, source.upper_bound, source.exhaustion_date_p10,
  source.exhaustion_date_p50, source.exhaustion_date_p90, source.days_to_exhaustion,
  source.baseline_exhaustion_date, source.days_extended, source.model_version, CURRENT_TIMESTAMP()
);

-- ============================================================================
-- Step 3: Refresh scenario_summary with latest metrics
-- ============================================================================

MERGE INTO IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary') AS target
USING (
  WITH latest_burndown AS (
    SELECT
      scenario_id,
      contract_id,
      MAX(usage_date) AS latest_date,
      MAX(original_cumulative) AS actual_cumulative,
      MAX(simulated_cumulative) AS simulated_cumulative,
      MAX(cumulative_savings) AS cumulative_savings
    FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_burndown')
    GROUP BY scenario_id, contract_id
  ),
  latest_forecast AS (
    SELECT
      scenario_id,
      contract_id,
      MIN(exhaustion_date_p50) AS scenario_exhaustion_date,
      MIN(baseline_exhaustion_date) AS baseline_exhaustion_date,
      MAX(days_extended) AS days_extended
    FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_forecast')
    WHERE exhaustion_date_p50 IS NOT NULL
    GROUP BY scenario_id, contract_id
  ),
  summary_calc AS (
    SELECT
      ds.scenario_id,
      ds.contract_id,
      ds.scenario_name,
      ds.discount_pct,
      c.total_value AS base_commitment,
      COALESCE(ds.adjusted_total_value, c.total_value) AS scenario_commitment,
      c.start_date AS contract_start,
      c.end_date AS contract_end,
      COALESCE(lb.actual_cumulative, 0) AS actual_cumulative,
      COALESCE(lb.simulated_cumulative, 0) AS simulated_cumulative,
      COALESCE(lb.cumulative_savings, 0) AS cumulative_savings,
      lf.baseline_exhaustion_date,
      lf.scenario_exhaustion_date,
      lf.days_extended,
      -- Break-even: commitment / (1 - discount_rate)
      CASE
        WHEN ds.discount_pct < 100 THEN c.total_value / (1 - ds.discount_pct / 100)
        ELSE 0
      END AS break_even_consumption,
      -- Utilization %
      CASE
        WHEN c.total_value > 0 THEN COALESCE(lb.simulated_cumulative, 0) / c.total_value * 100
        ELSE 0
      END AS utilization_pct,
      -- Break-even status
      CASE
        WHEN COALESCE(lb.actual_cumulative, 0) >= c.total_value / (1 - ds.discount_pct / 100) THEN 'ABOVE_BREAKEVEN'
        WHEN COALESCE(lb.actual_cumulative, 0) >= c.total_value / (1 - ds.discount_pct / 100) * 0.8 THEN 'AT_RISK'
        ELSE 'BELOW_BREAKEVEN'
      END AS break_even_status,
      -- Exhaustion status
      CASE
        WHEN lf.scenario_exhaustion_date IS NULL THEN 'EXTENDED'
        WHEN lf.scenario_exhaustion_date < c.end_date THEN 'EARLY_EXHAUSTION'
        WHEN lf.scenario_exhaustion_date > DATE_ADD(c.end_date, 30) THEN 'EXTENDED'
        ELSE 'ON_TRACK'
      END AS exhaustion_status,
      ds.discount_pct AS pct_savings
    FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.discount_scenarios') ds
    INNER JOIN IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contracts') c
      ON ds.contract_id = c.contract_id
    LEFT JOIN latest_burndown lb
      ON ds.scenario_id = lb.scenario_id
    LEFT JOIN latest_forecast lf
      ON ds.scenario_id = lf.scenario_id
    WHERE ds.status = 'ACTIVE'
  )
  SELECT * FROM summary_calc
) AS source
ON target.scenario_id = source.scenario_id
WHEN MATCHED THEN UPDATE SET
  scenario_name = source.scenario_name,
  discount_pct = source.discount_pct,
  base_commitment = source.base_commitment,
  scenario_commitment = source.scenario_commitment,
  contract_start = source.contract_start,
  contract_end = source.contract_end,
  actual_cumulative = source.actual_cumulative,
  simulated_cumulative = source.simulated_cumulative,
  cumulative_savings = source.cumulative_savings,
  baseline_exhaustion_date = source.baseline_exhaustion_date,
  scenario_exhaustion_date = source.scenario_exhaustion_date,
  days_extended = source.days_extended,
  break_even_consumption = source.break_even_consumption,
  utilization_pct = source.utilization_pct,
  break_even_status = source.break_even_status,
  exhaustion_status = source.exhaustion_status,
  pct_savings = source.pct_savings,
  last_calculated = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (
  scenario_id, contract_id, scenario_name, discount_pct, base_commitment, scenario_commitment,
  contract_start, contract_end, actual_cumulative, simulated_cumulative, cumulative_savings,
  baseline_exhaustion_date, scenario_exhaustion_date, days_extended, break_even_consumption,
  utilization_pct, break_even_status, exhaustion_status, pct_savings, is_sweet_spot, last_calculated
) VALUES (
  source.scenario_id, source.contract_id, source.scenario_name, source.discount_pct,
  source.base_commitment, source.scenario_commitment, source.contract_start, source.contract_end,
  source.actual_cumulative, source.simulated_cumulative, source.cumulative_savings,
  source.baseline_exhaustion_date, source.scenario_exhaustion_date, source.days_extended,
  source.break_even_consumption, source.utilization_pct, source.break_even_status,
  source.exhaustion_status, source.pct_savings, FALSE, CURRENT_TIMESTAMP()
);

-- ============================================================================
-- Step 4: Update sweet spot flags
-- Sweet spot = max savings with utilization >= 85%
-- ============================================================================

-- Reset all sweet spot flags
UPDATE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary')
SET is_sweet_spot = FALSE
WHERE is_sweet_spot = TRUE;

-- Set sweet spot for each contract
MERGE INTO IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary') AS target
USING (
  SELECT scenario_id
  FROM (
    SELECT
      scenario_id,
      contract_id,
      cumulative_savings,
      utilization_pct,
      ROW_NUMBER() OVER (
        PARTITION BY contract_id
        ORDER BY
          CASE WHEN utilization_pct >= 85 OR discount_pct = 0 THEN cumulative_savings ELSE -1 END DESC
      ) AS rn
    FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary')
  )
  WHERE rn = 1
) AS source
ON target.scenario_id = source.scenario_id
WHEN MATCHED THEN UPDATE SET
  is_sweet_spot = TRUE;

-- Also update discount_scenarios is_recommended flag using MERGE
MERGE INTO IDENTIFIER({{catalog}} || '.' || {{schema}} || '.discount_scenarios') AS target
USING (
  SELECT scenario_id, is_sweet_spot
  FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary')
) AS source
ON target.scenario_id = source.scenario_id
WHEN MATCHED THEN UPDATE SET
  is_recommended = COALESCE(source.is_sweet_spot, FALSE);

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'What-If scenarios refreshed successfully' AS status;

SELECT
  COUNT(DISTINCT scenario_id) AS total_scenarios,
  COUNT(DISTINCT contract_id) AS contracts_covered,
  SUM(CASE WHEN is_sweet_spot THEN 1 ELSE 0 END) AS sweet_spots_identified
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary');
