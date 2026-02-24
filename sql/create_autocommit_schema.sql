-- Create Auto-Commit Optimization Schema and Tables
-- Tables for computing optimal contract commitment amounts

-- ============================================================================
-- Table: auto_commit_recommendations
-- Stores computed optimal commitment recommendations per account
-- ============================================================================
CREATE TABLE IF NOT EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_recommendations') (
  recommendation_id STRING NOT NULL COMMENT 'Unique recommendation identifier (UUID)',
  account_id STRING NOT NULL COMMENT 'Account this recommendation is for',
  -- Time parameters
  analysis_date DATE NOT NULL COMMENT 'Date when this analysis was performed',
  historical_start DATE NOT NULL COMMENT 'Start of historical data used',
  historical_end DATE NOT NULL COMMENT 'End of historical data (typically today)',
  proposed_start DATE NOT NULL COMMENT 'Proposed contract start date',
  proposed_end DATE NOT NULL COMMENT 'Proposed contract end date',
  duration_years INT NOT NULL COMMENT 'Contract duration in years',
  -- Consumption analysis
  historical_daily_avg DECIMAL(18,2) COMMENT 'Average daily consumption from historical data',
  historical_total DECIMAL(18,2) COMMENT 'Total historical consumption in analysis period',
  forecasted_daily_avg DECIMAL(18,2) COMMENT 'Prophet-predicted average daily consumption',
  forecasted_total DECIMAL(18,2) COMMENT 'Total forecasted consumption over contract',
  projected_total DECIMAL(18,2) COMMENT 'Combined historical + forecasted total for contract period',
  -- Optimal recommendation
  optimal_commitment DECIMAL(18,2) NOT NULL COMMENT 'Recommended contract commitment amount',
  optimal_discount_rate DECIMAL(5,4) COMMENT 'Discount rate for optimal commitment',
  optimal_tier_name STRING COMMENT 'Name of the discount tier',
  optimal_utilization_pct DECIMAL(5,2) COMMENT 'Expected utilization percentage',
  -- Comparison with no discount
  list_price_total DECIMAL(18,2) COMMENT 'What you would pay at list price',
  committed_price_total DECIMAL(18,2) COMMENT 'What you pay with optimal commitment',
  total_savings DECIMAL(18,2) COMMENT 'Total savings vs list price',
  savings_pct DECIMAL(5,2) COMMENT 'Savings as percentage',
  -- Alternative recommendations
  conservative_commitment DECIMAL(18,2) COMMENT 'Lower commitment option (safer)',
  conservative_discount_rate DECIMAL(5,4) COMMENT 'Discount for conservative option',
  aggressive_commitment DECIMAL(18,2) COMMENT 'Higher commitment option (more savings)',
  aggressive_discount_rate DECIMAL(5,4) COMMENT 'Discount for aggressive option',
  -- Model info
  model_used STRING COMMENT 'prophet or linear_fallback',
  confidence_level DECIMAL(3,2) COMMENT 'Confidence in forecast (0-1)',
  -- Status
  status STRING COMMENT 'DRAFT, ACTIVE, ACCEPTED, REJECTED',
  notes STRING COMMENT 'Additional notes or caveats',
  created_at TIMESTAMP COMMENT 'When this recommendation was created',
  updated_at TIMESTAMP COMMENT 'When this recommendation was last updated',
  CONSTRAINT pk_auto_commit_recommendations PRIMARY KEY (recommendation_id)
)
USING DELTA
COMMENT 'Optimal contract commitment recommendations based on consumption analysis'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================================
-- Table: auto_commit_scenarios
-- Detailed scenarios for each commitment level analyzed
-- ============================================================================
CREATE TABLE IF NOT EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_scenarios') (
  scenario_id STRING NOT NULL COMMENT 'Unique scenario identifier',
  recommendation_id STRING NOT NULL COMMENT 'Parent recommendation this belongs to',
  account_id STRING NOT NULL COMMENT 'Account reference',
  -- Commitment parameters
  commitment_amount DECIMAL(18,2) NOT NULL COMMENT 'Commitment amount for this scenario',
  duration_years INT NOT NULL COMMENT 'Contract duration',
  discount_tier_id STRING COMMENT 'Discount tier applied',
  discount_tier_name STRING COMMENT 'Discount tier name',
  discount_rate DECIMAL(5,4) NOT NULL COMMENT 'Discount rate as decimal',
  -- Consumption projections
  projected_consumption DECIMAL(18,2) COMMENT 'Total projected consumption',
  effective_cost DECIMAL(18,2) COMMENT 'Cost after discount',
  utilization_pct DECIMAL(5,2) COMMENT 'Expected utilization (consumption/commitment)',
  -- Value analysis
  savings_vs_list DECIMAL(18,2) COMMENT 'Savings compared to list price',
  savings_vs_baseline DECIMAL(18,2) COMMENT 'Savings vs no commitment',
  waste_amount DECIMAL(18,2) COMMENT 'Unused commitment (if utilization < 100%)',
  net_benefit DECIMAL(18,2) COMMENT 'savings_vs_list - waste_amount',
  roi_score DECIMAL(10,4) COMMENT 'Return on investment score',
  -- Flags
  is_optimal BOOLEAN COMMENT 'True if this is the recommended scenario',
  is_conservative BOOLEAN COMMENT 'True if this is the conservative option',
  is_aggressive BOOLEAN COMMENT 'True if this is the aggressive option',
  risk_level STRING COMMENT 'LOW, MEDIUM, HIGH based on utilization variance',
  -- Metadata
  created_at TIMESTAMP COMMENT 'When this scenario was computed',
  CONSTRAINT pk_auto_commit_scenarios PRIMARY KEY (scenario_id)
)
USING DELTA
COMMENT 'Detailed analysis of different commitment scenarios'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================================
-- Table: auto_commit_forecast_detail
-- Daily forecast breakdown for recommendations
-- ============================================================================
CREATE TABLE IF NOT EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_forecast_detail') (
  recommendation_id STRING NOT NULL COMMENT 'Parent recommendation',
  forecast_date DATE NOT NULL COMMENT 'Date in the forecast',
  source STRING NOT NULL COMMENT 'historical or forecast',
  -- Daily values
  daily_cost DECIMAL(18,2) COMMENT 'Daily consumption cost',
  cumulative_cost DECIMAL(18,2) COMMENT 'Running total',
  -- Prophet forecast details (for forecast period only)
  predicted_lower DECIMAL(18,2) COMMENT 'Lower bound prediction',
  predicted_upper DECIMAL(18,2) COMMENT 'Upper bound prediction',
  -- Metadata
  created_at TIMESTAMP COMMENT 'When this record was created',
  CONSTRAINT pk_auto_commit_forecast PRIMARY KEY (recommendation_id, forecast_date)
)
USING DELTA
PARTITIONED BY (recommendation_id)
COMMENT 'Daily breakdown of consumption forecast for recommendations'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- View: latest_recommendations
-- Most recent recommendation per account
-- ============================================================================
CREATE OR REPLACE VIEW IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_latest') AS
SELECT r.*
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_recommendations') r
INNER JOIN (
  SELECT account_id, MAX(analysis_date) as max_date
  FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_recommendations')
  GROUP BY account_id
) latest ON r.account_id = latest.account_id AND r.analysis_date = latest.max_date;

-- ============================================================================
-- View: recommendation_summary
-- Summary view for dashboard display
-- ============================================================================
CREATE OR REPLACE VIEW IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_summary') AS
SELECT
  r.recommendation_id,
  r.account_id,
  am.customer_name,
  r.analysis_date,
  r.duration_years,
  r.proposed_start,
  r.proposed_end,
  r.historical_daily_avg,
  r.forecasted_daily_avg,
  r.projected_total,
  r.optimal_commitment,
  r.optimal_discount_rate,
  CONCAT(CAST(r.optimal_discount_rate * 100 AS INT), '%') as discount_display,
  r.optimal_tier_name,
  r.optimal_utilization_pct,
  r.total_savings,
  r.savings_pct,
  r.conservative_commitment,
  r.aggressive_commitment,
  r.model_used,
  r.confidence_level,
  r.status
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.auto_commit_latest') r
LEFT JOIN IDENTIFIER({{catalog}} || '.' || {{schema}} || '.account_metadata') am
  ON r.account_id = am.account_id;

SELECT 'Auto-commit optimization schema created successfully' as status;
