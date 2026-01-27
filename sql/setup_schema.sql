-- Setup Schema and Tables for Account Monitor
-- This script creates all necessary Unity Catalog objects

-- Create schema
CREATE SCHEMA IF NOT EXISTS main.account_monitoring_dev
COMMENT 'Account monitoring and cost tracking using system tables';

-- Create contracts table
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.contracts (
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
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.account_metadata (
  account_id STRING NOT NULL COMMENT 'Databricks account ID',
  customer_name STRING NOT NULL COMMENT 'Customer display name',
  salesforce_id STRING COMMENT 'Salesforce account ID',
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
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.dashboard_data (
  usage_date DATE NOT NULL,
  account_id STRING NOT NULL,
  customer_name STRING,
  salesforce_id STRING,
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
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.daily_summary (
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

SELECT 'Schema and tables created successfully' as status;
