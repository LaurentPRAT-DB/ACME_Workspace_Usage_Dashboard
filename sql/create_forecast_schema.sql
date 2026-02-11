-- Create Forecast Schema and Tables
-- Tables for Prophet-based consumption forecasting

-- Table: contract_forecast
-- Stores daily forecast predictions and exhaustion dates
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.contract_forecast (
  contract_id STRING NOT NULL COMMENT 'Contract identifier',
  forecast_date DATE NOT NULL COMMENT 'Date this forecast was generated',
  model_version STRING COMMENT 'Model version/MLflow run ID',
  -- Daily predictions
  predicted_daily_cost DECIMAL(18,2) COMMENT 'Prophet predicted daily cost',
  predicted_cumulative DECIMAL(18,2) COMMENT 'Cumulative predicted cost from contract start',
  lower_bound DECIMAL(18,2) COMMENT '10th percentile (optimistic)',
  upper_bound DECIMAL(18,2) COMMENT '90th percentile (conservative)',
  -- Exhaustion predictions
  exhaustion_date_p10 DATE COMMENT 'Optimistic exhaustion date (10th percentile)',
  exhaustion_date_p50 DATE COMMENT 'Median exhaustion date prediction',
  exhaustion_date_p90 DATE COMMENT 'Conservative exhaustion date (90th percentile)',
  days_to_exhaustion INT COMMENT 'Days until median exhaustion date',
  -- Metadata
  created_at TIMESTAMP COMMENT 'When this forecast was created',
  CONSTRAINT pk_forecast PRIMARY KEY (contract_id, forecast_date)
)
USING DELTA
COMMENT 'Prophet-based consumption forecasts for contracts'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Table: forecast_model_registry
-- Tracks trained models and their performance
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.forecast_model_registry (
  model_id STRING NOT NULL COMMENT 'Unique model identifier',
  contract_id STRING NOT NULL COMMENT 'Contract this model was trained for',
  trained_at TIMESTAMP COMMENT 'When the model was trained',
  training_start_date DATE COMMENT 'Start of training data window',
  training_end_date DATE COMMENT 'End of training data window',
  training_points INT COMMENT 'Number of data points used for training',
  -- Model metrics
  mape DECIMAL(10,4) COMMENT 'Mean Absolute Percentage Error',
  rmse DECIMAL(18,4) COMMENT 'Root Mean Square Error',
  mae DECIMAL(18,4) COMMENT 'Mean Absolute Error',
  -- MLflow tracking
  mlflow_experiment_id STRING COMMENT 'MLflow experiment ID',
  mlflow_run_id STRING COMMENT 'MLflow run ID',
  -- Status
  is_active BOOLEAN COMMENT 'Whether this model is currently active',
  CONSTRAINT pk_model_registry PRIMARY KEY (model_id)
)
USING DELTA
COMMENT 'Registry of trained Prophet models for forecasting'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- View: Latest forecast per contract
-- Shows most recent forecast for each contract
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.contract_forecast_latest AS
SELECT *
FROM {{catalog}}.{{schema}}.contract_forecast f
WHERE forecast_date = (
  SELECT MAX(forecast_date)
  FROM {{catalog}}.{{schema}}.contract_forecast
  WHERE contract_id = f.contract_id
);

-- View: Active model per contract
-- Shows the active model for each contract
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.forecast_model_active AS
SELECT *
FROM {{catalog}}.{{schema}}.forecast_model_registry
WHERE is_active = TRUE;

-- View: Forecast with contract details
-- Joins forecast with contract information for dashboard use
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.contract_forecast_details AS
SELECT
  f.contract_id,
  f.forecast_date,
  c.cloud_provider,
  c.start_date as contract_start,
  c.end_date as contract_end,
  c.total_value as contract_value,
  f.predicted_daily_cost,
  f.predicted_cumulative,
  f.lower_bound,
  f.upper_bound,
  f.exhaustion_date_p10,
  f.exhaustion_date_p50,
  f.exhaustion_date_p90,
  f.days_to_exhaustion,
  -- Calculated fields
  CASE
    WHEN f.exhaustion_date_p50 IS NOT NULL AND f.exhaustion_date_p50 < c.end_date THEN 'AT RISK'
    WHEN f.exhaustion_date_p90 IS NOT NULL AND f.exhaustion_date_p90 < c.end_date THEN 'WATCH'
    ELSE 'ON TRACK'
  END as forecast_status,
  f.model_version,
  f.created_at
FROM {{catalog}}.{{schema}}.contract_forecast f
INNER JOIN {{catalog}}.{{schema}}.contracts c
  ON f.contract_id = c.contract_id
WHERE c.status = 'ACTIVE';

SELECT 'Forecast schema created successfully' as status;
