-- Cleanup Schema - Drop All Account Monitor Objects
-- =================================================
-- This script removes all tables, views, and the schema created by Account Monitor.
-- Use this to start from scratch before redeploying.
--
-- WARNING: This will DELETE ALL DATA. This action cannot be undone.
--
-- Usage:
--   Option 1: Run via bundle job
--     databricks bundle run account_monitor_cleanup --profile YOUR_PROFILE
--
--   Option 2: Run manually
--     databricks bundle deploy --profile YOUR_PROFILE
--     databricks sql execute --file sql/cleanup_schema.sql --profile YOUR_PROFILE
--
--   Option 3: Full reset (destroy everything)
--     databricks bundle run account_monitor_cleanup --profile YOUR_PROFILE
--     databricks bundle destroy --profile YOUR_PROFILE

-- ============================================================================
-- Step 1: Drop Views (must drop before tables they depend on)
-- ============================================================================

-- Forecast views
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast_latest');
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.forecast_model_active');
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast_details');
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.forecast_features');
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.forecast_feature_summary');

-- Burndown views
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown_summary');

-- What-If views
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_comparison');
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_burndown_chart');
DROP VIEW IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.sweet_spot_recommendation');

SELECT 'Views dropped' AS status;

-- ============================================================================
-- Step 2: Drop Tables
-- ============================================================================

-- What-If simulation tables
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_summary');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_forecast');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.scenario_burndown');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.discount_scenarios');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.discount_tiers');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.whatif_debug_log');

-- Forecast tables
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.forecast_model_registry');

-- Burndown and consumption tables
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.daily_summary');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data_archive');

-- Core tables
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contracts');
DROP TABLE IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.account_metadata');

SELECT 'Tables dropped' AS status;

-- ============================================================================
-- Step 3: Drop Schema (optional - uncomment if you want to remove the schema)
-- ============================================================================

-- WARNING: This removes the schema entirely. Only uncomment if you want a complete reset.
-- DROP SCHEMA IF EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}}) CASCADE;

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'Cleanup complete. Schema is now empty.' AS status;

-- Show remaining objects (should be empty)
SHOW TABLES IN IDENTIFIER({{catalog}} || '.' || {{schema}});
