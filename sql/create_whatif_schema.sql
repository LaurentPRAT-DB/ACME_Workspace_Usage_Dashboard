-- Create What-If Simulation Schema and Tables
-- Tables for discount scenario simulation and savings analysis

-- ============================================================================
-- Table: discount_tiers
-- Configurable discount rates by commitment level and duration
-- ============================================================================
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.discount_tiers (
  tier_id STRING NOT NULL COMMENT 'Unique tier identifier',
  tier_name STRING NOT NULL COMMENT 'Human-readable tier name',
  min_commitment DECIMAL(18,2) NOT NULL COMMENT 'Minimum commitment for this tier',
  max_commitment DECIMAL(18,2) COMMENT 'Maximum commitment (NULL = unlimited)',
  duration_years INT NOT NULL COMMENT 'Contract duration in years (1, 2, or 3)',
  discount_rate DECIMAL(5,4) NOT NULL COMMENT 'Discount rate as decimal (e.g., 0.15 = 15%)',
  cloud_provider STRING COMMENT 'Cloud provider (NULL = all providers)',
  effective_date DATE COMMENT 'When this tier becomes effective',
  expiration_date DATE COMMENT 'When this tier expires',
  notes STRING COMMENT 'Additional notes about this tier',
  created_at TIMESTAMP COMMENT 'When this tier was created',
  CONSTRAINT pk_discount_tiers PRIMARY KEY (tier_id)
)
USING DELTA
COMMENT 'Configurable discount tiers by commitment level and duration'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================================
-- Table: discount_scenarios
-- User-defined what-if scenarios for contracts
-- ============================================================================
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.discount_scenarios (
  scenario_id STRING NOT NULL COMMENT 'Unique scenario identifier (UUID)',
  contract_id STRING NOT NULL COMMENT 'Base contract for simulation',
  scenario_name STRING NOT NULL COMMENT 'User-friendly scenario name',
  description STRING COMMENT 'Detailed description of scenario',
  -- Discount parameters
  discount_pct DECIMAL(5,2) NOT NULL COMMENT 'Overall discount percentage (0-100)',
  discount_type STRING COMMENT 'Type: overall, sku_specific, tier_based',
  -- Contract variations
  adjusted_total_value DECIMAL(18,2) COMMENT 'Modified contract value (NULL = use base)',
  adjusted_start_date DATE COMMENT 'Modified start date (NULL = use base)',
  adjusted_end_date DATE COMMENT 'Modified end date (NULL = use base)',
  -- Scenario metadata
  is_baseline BOOLEAN COMMENT 'True if this is the baseline (0% discount)',
  is_recommended BOOLEAN COMMENT 'True if this is the recommended scenario',
  status STRING COMMENT 'Status: DRAFT, ACTIVE, ARCHIVED',
  created_by STRING COMMENT 'User who created scenario',
  created_at TIMESTAMP COMMENT 'When scenario was created',
  updated_at TIMESTAMP COMMENT 'When scenario was last updated',
  CONSTRAINT pk_scenarios PRIMARY KEY (scenario_id)
)
USING DELTA
COMMENT 'What-if discount scenarios for contract simulation'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================================
-- Table: scenario_burndown
-- Simulated daily burndown for each scenario
-- ============================================================================
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.scenario_burndown (
  scenario_id STRING NOT NULL COMMENT 'Scenario this burndown belongs to',
  contract_id STRING NOT NULL COMMENT 'Base contract reference',
  usage_date DATE NOT NULL COMMENT 'Simulation date',
  -- Original values (from actual burndown)
  original_daily_cost DECIMAL(18,2) COMMENT 'Actual daily cost without discount',
  original_cumulative DECIMAL(18,2) COMMENT 'Actual cumulative cost',
  -- Simulated values (with discount applied)
  simulated_daily_cost DECIMAL(18,2) COMMENT 'Daily cost after discount',
  simulated_cumulative DECIMAL(18,2) COMMENT 'Cumulative cost after discount',
  -- Scenario commitment (may differ from base contract)
  scenario_commitment DECIMAL(18,2) COMMENT 'Contract value for this scenario',
  simulated_remaining DECIMAL(18,2) COMMENT 'Remaining budget in scenario',
  -- Savings metrics
  daily_savings DECIMAL(18,2) COMMENT 'Savings on this day',
  cumulative_savings DECIMAL(18,2) COMMENT 'Total savings to date',
  -- Extension scenario flag
  is_projected BOOLEAN COMMENT 'True if this is projected future data (for extension scenarios)',
  -- Metadata
  calculated_at TIMESTAMP COMMENT 'When this row was calculated',
  CONSTRAINT pk_scenario_burndown PRIMARY KEY (scenario_id, usage_date)
)
USING DELTA
PARTITIONED BY (scenario_id)
COMMENT 'Simulated burndown data for discount scenarios'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- Table: scenario_forecast
-- Prophet-based predictions for each scenario
-- ============================================================================
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.scenario_forecast (
  scenario_id STRING NOT NULL COMMENT 'Scenario this forecast belongs to',
  contract_id STRING NOT NULL COMMENT 'Base contract reference',
  forecast_date DATE NOT NULL COMMENT 'Forecast date',
  -- Predictions (adjusted for discount)
  predicted_daily_cost DECIMAL(18,2) COMMENT 'Predicted daily cost with discount',
  predicted_cumulative DECIMAL(18,2) COMMENT 'Predicted cumulative with discount',
  lower_bound DECIMAL(18,2) COMMENT '10th percentile',
  upper_bound DECIMAL(18,2) COMMENT '90th percentile',
  -- Exhaustion predictions (adjusted for scenario commitment)
  exhaustion_date_p10 DATE COMMENT 'Optimistic exhaustion date',
  exhaustion_date_p50 DATE COMMENT 'Median exhaustion date',
  exhaustion_date_p90 DATE COMMENT 'Conservative exhaustion date',
  days_to_exhaustion INT COMMENT 'Days until median exhaustion',
  -- Comparison to baseline
  baseline_exhaustion_date DATE COMMENT 'Baseline (0%) exhaustion date',
  days_extended INT COMMENT 'Additional days vs baseline (positive = longer)',
  savings_at_exhaustion DECIMAL(18,2) COMMENT 'Total savings when baseline exhausts',
  -- Model info
  model_version STRING COMMENT 'prophet or linear_fallback',
  created_at TIMESTAMP COMMENT 'When this forecast was created',
  CONSTRAINT pk_scenario_forecast PRIMARY KEY (scenario_id, forecast_date)
)
USING DELTA
PARTITIONED BY (scenario_id)
COMMENT 'Forecasts for discount scenarios'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================================
-- Table: scenario_summary
-- Denormalized summary for fast dashboard queries
-- ============================================================================
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.scenario_summary (
  scenario_id STRING NOT NULL COMMENT 'Scenario identifier',
  contract_id STRING NOT NULL COMMENT 'Base contract reference',
  scenario_name STRING COMMENT 'Scenario display name',
  discount_pct DECIMAL(5,2) COMMENT 'Discount percentage',
  -- Contract parameters
  base_commitment DECIMAL(18,2) COMMENT 'Original contract value',
  scenario_commitment DECIMAL(18,2) COMMENT 'Scenario contract value',
  contract_start DATE COMMENT 'Contract start date',
  contract_end DATE COMMENT 'Contract end date',
  -- Current state
  actual_cumulative DECIMAL(18,2) COMMENT 'Actual spend to date',
  simulated_cumulative DECIMAL(18,2) COMMENT 'Simulated spend to date',
  cumulative_savings DECIMAL(18,2) COMMENT 'Savings to date',
  -- Projections
  baseline_exhaustion_date DATE COMMENT 'When baseline runs out',
  scenario_exhaustion_date DATE COMMENT 'When scenario runs out',
  days_extended INT COMMENT 'Additional days gained',
  -- Break-even analysis
  break_even_consumption DECIMAL(18,2) COMMENT 'Consumption needed to justify commit',
  utilization_pct DECIMAL(10,2) COMMENT 'Current utilization percentage',
  break_even_status STRING COMMENT 'ABOVE_BREAKEVEN, AT_RISK, BELOW_BREAKEVEN',
  -- Status indicators
  exhaustion_status STRING COMMENT 'EARLY_EXHAUSTION, ON_TRACK, EXTENDED',
  pct_savings DECIMAL(5,2) COMMENT 'Savings as % of base',
  is_sweet_spot BOOLEAN COMMENT 'True if this is optimal scenario',
  -- Timestamps
  last_calculated TIMESTAMP COMMENT 'When summary was last calculated',
  CONSTRAINT pk_scenario_summary PRIMARY KEY (scenario_id)
)
USING DELTA
COMMENT 'Summary metrics for scenario comparison'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================================
-- View: scenario_comparison
-- Compare all active scenarios for a contract
-- ============================================================================
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.scenario_comparison AS
SELECT
  s.scenario_id,
  s.contract_id,
  s.scenario_name,
  s.discount_pct,
  s.is_baseline,
  s.is_recommended,
  sm.base_commitment,
  sm.scenario_commitment,
  sm.actual_cumulative,
  sm.simulated_cumulative,
  sm.cumulative_savings,
  sm.baseline_exhaustion_date,
  sm.scenario_exhaustion_date,
  sm.days_extended,
  sm.utilization_pct,
  sm.pct_savings,
  sm.is_sweet_spot,
  sm.exhaustion_status,
  sm.break_even_status
FROM {{catalog}}.{{schema}}.discount_scenarios s
INNER JOIN {{catalog}}.{{schema}}.scenario_summary sm
  ON s.scenario_id = sm.scenario_id
WHERE s.status = 'ACTIVE'
ORDER BY s.contract_id, s.discount_pct;

-- ============================================================================
-- View: scenario_burndown_chart
-- Data for multi-line burndown comparison chart
-- ============================================================================
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.scenario_burndown_chart AS
SELECT
  sb.contract_id,
  sb.usage_date,
  s.scenario_name,
  s.discount_pct,
  sb.simulated_cumulative as cumulative_cost,
  sb.scenario_commitment as commitment,
  sb.cumulative_savings,
  s.is_baseline
FROM {{catalog}}.{{schema}}.scenario_burndown sb
INNER JOIN {{catalog}}.{{schema}}.discount_scenarios s
  ON sb.scenario_id = s.scenario_id
WHERE s.status = 'ACTIVE'
ORDER BY sb.contract_id, sb.usage_date, s.discount_pct;

-- ============================================================================
-- View: sweet_spot_recommendation
-- Shows the optimal scenario per contract
-- ============================================================================
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.sweet_spot_recommendation AS
SELECT
  contract_id,
  scenario_id,
  scenario_name,
  discount_pct,
  cumulative_savings,
  days_extended,
  utilization_pct,
  pct_savings
FROM {{catalog}}.{{schema}}.scenario_summary
WHERE is_sweet_spot = TRUE;

SELECT 'What-If simulation schema created successfully' as status;
