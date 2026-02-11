-- Setup Schema and Tables for Account Monitor
-- This script creates all necessary Unity Catalog objects

-- Create schema
CREATE SCHEMA IF NOT EXISTS {{catalog}}.{{schema}}
COMMENT 'Account monitoring and cost tracking using system tables';

-- Create contracts table
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.contracts (
  contract_id STRING NOT NULL COMMENT 'Unique contract identifier',
  account_id STRING NOT NULL COMMENT 'Databricks account ID',
  cloud_provider STRING NOT NULL COMMENT 'Cloud provider: aws, azure, gcp',
  start_date DATE NOT NULL COMMENT 'Contract start date',
  end_date DATE NOT NULL COMMENT 'Contract end date',
  total_value DECIMAL(18,2) NOT NULL COMMENT 'Total contract value',
  currency STRING COMMENT 'Currency code',
  commitment_type STRING COMMENT 'DBU or SPEND commitment',
  status STRING COMMENT 'ACTIVE, EXPIRED, or PENDING',
  notes STRING COMMENT 'Additional notes',
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  CONSTRAINT pk_contracts PRIMARY KEY (contract_id)
)
USING DELTA
COMMENT 'Contract tracking for consumption monitoring'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Create account metadata table
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.account_metadata (
  account_id STRING NOT NULL COMMENT 'Databricks account ID',
  customer_name STRING NOT NULL COMMENT 'Customer display name',
  business_unit_l0 STRING COMMENT 'Top-level business unit',
  business_unit_l1 STRING COMMENT 'Second-level business unit',
  business_unit_l2 STRING COMMENT 'Third-level business unit',
  business_unit_l3 STRING COMMENT 'Fourth-level business unit',
  account_executive STRING COMMENT 'Account Executive name',
  solutions_architect STRING COMMENT 'Solutions Architect name',
  delivery_solutions_architect STRING COMMENT 'Delivery SA name',
  region STRING COMMENT 'Geographic region',
  industry STRING COMMENT 'Customer industry',
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  CONSTRAINT pk_account_metadata PRIMARY KEY (account_id)
)
USING DELTA
COMMENT 'Account metadata and organizational information'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Create dashboard data table
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.dashboard_data (
  usage_date DATE NOT NULL,
  account_id STRING NOT NULL,
  customer_name STRING,
  business_unit_l0 STRING,
  business_unit_l1 STRING,
  business_unit_l2 STRING,
  business_unit_l3 STRING,
  account_executive STRING,
  solutions_architect STRING,
  workspace_id STRING NOT NULL,
  cloud_provider STRING NOT NULL,
  sku_name STRING NOT NULL,
  usage_unit STRING,
  usage_quantity DECIMAL(18,6),
  price_per_unit DECIMAL(20,10),
  list_cost DECIMAL(18,2),
  actual_cost DECIMAL(18,2),
  product_category STRING,
  job_id STRING,
  job_name STRING,
  warehouse_id STRING,
  cluster_id STRING,
  run_as STRING,
  custom_tags MAP<STRING, STRING>,
  updated_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (usage_date)
COMMENT 'Pre-aggregated dashboard data'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Create daily summary table for faster queries
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.daily_summary (
  usage_date DATE NOT NULL,
  cloud_provider STRING NOT NULL,
  workspace_id STRING NOT NULL,
  total_dbu DECIMAL(18,6),
  total_cost DECIMAL(18,2),
  unique_skus INT,
  updated_at TIMESTAMP
)
USING DELTA
PARTITIONED BY (usage_date)
COMMENT 'Daily aggregated summary for fast queries'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Create forecast tables for Prophet-based predictions

-- Table: contract_forecast
-- Stores daily forecast predictions and exhaustion dates
CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.contract_forecast (
  contract_id STRING NOT NULL COMMENT 'Contract identifier',
  forecast_date DATE NOT NULL COMMENT 'Date this forecast was generated',
  model_version STRING COMMENT 'Model version/MLflow run ID',
  predicted_daily_cost DECIMAL(18,2) COMMENT 'Prophet predicted daily cost',
  predicted_cumulative DECIMAL(18,2) COMMENT 'Cumulative predicted cost from contract start',
  lower_bound DECIMAL(18,2) COMMENT '10th percentile (optimistic)',
  upper_bound DECIMAL(18,2) COMMENT '90th percentile (conservative)',
  exhaustion_date_p10 DATE COMMENT 'Optimistic exhaustion date (10th percentile)',
  exhaustion_date_p50 DATE COMMENT 'Median exhaustion date prediction',
  exhaustion_date_p90 DATE COMMENT 'Conservative exhaustion date (90th percentile)',
  days_to_exhaustion INT COMMENT 'Days until median exhaustion date',
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
  mape DECIMAL(10,4) COMMENT 'Mean Absolute Percentage Error',
  rmse DECIMAL(18,4) COMMENT 'Root Mean Square Error',
  mae DECIMAL(18,4) COMMENT 'Mean Absolute Error',
  mlflow_experiment_id STRING COMMENT 'MLflow experiment ID',
  mlflow_run_id STRING COMMENT 'MLflow run ID',
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
CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.contract_forecast_latest AS
SELECT *
FROM {{catalog}}.{{schema}}.contract_forecast f
WHERE forecast_date = (
  SELECT MAX(forecast_date)
  FROM {{catalog}}.{{schema}}.contract_forecast
  WHERE contract_id = f.contract_id
);

SELECT 'Schema and tables created successfully' as status;
