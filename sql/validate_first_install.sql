-- ============================================================================
-- First Install Validation
-- ============================================================================
-- Verifies that all tables are properly populated after first install

-- Show validation report
SELECT
  'FIRST INSTALL VALIDATION REPORT' as status,
  '================================' as separator;

-- Table row counts
SELECT
  'contracts' as table_name,
  COUNT(*) as total_rows,
  SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_rows
FROM main.account_monitoring_dev.contracts;

SELECT
  'account_metadata' as table_name,
  COUNT(*) as total_rows
FROM main.account_monitoring_dev.account_metadata;

SELECT
  'dashboard_data' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT usage_date) as unique_dates,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date
FROM main.account_monitoring_dev.dashboard_data;

SELECT
  'contract_burndown' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT contract_id) as contracts_tracked,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date
FROM main.account_monitoring_dev.contract_burndown;

SELECT
  'contract_forecast' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT contract_id) as contracts_forecasted
FROM main.account_monitoring_dev.contract_forecast;

-- Show forecast summary
SELECT
  contract_id,
  exhaustion_date_p50 as predicted_exhaustion_date,
  DATEDIFF(exhaustion_date_p50, CURRENT_DATE()) as days_until_exhaustion,
  model_version
FROM main.account_monitoring_dev.contract_forecast
WHERE forecast_date = (SELECT MAX(forecast_date) FROM main.account_monitoring_dev.contract_forecast)
ORDER BY contract_id;

-- Final status
SELECT
  'SUCCESS: First install validation complete!' as status,
  'Open account_monitor_notebook to view the dashboard' as next_step;
