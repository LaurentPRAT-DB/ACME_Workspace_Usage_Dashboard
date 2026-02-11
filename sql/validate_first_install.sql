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
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contracts');

SELECT
  'account_metadata' as table_name,
  COUNT(*) as total_rows
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.account_metadata');

SELECT
  'dashboard_data' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT usage_date) as unique_dates,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data');

SELECT
  'contract_burndown' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT contract_id) as contracts_tracked,
  MIN(usage_date) as earliest_date,
  MAX(usage_date) as latest_date
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown');

SELECT
  'contract_forecast' as table_name,
  COUNT(*) as total_rows,
  COUNT(DISTINCT contract_id) as contracts_forecasted
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast');

-- Show forecast summary
SELECT
  contract_id,
  exhaustion_date_p50 as predicted_exhaustion_date,
  DATEDIFF(exhaustion_date_p50, CURRENT_DATE()) as days_until_exhaustion,
  model_version
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast')
WHERE forecast_date = (SELECT MAX(forecast_date) FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast'))
ORDER BY contract_id;

-- Check Prophet model status
SELECT
  'FORECAST MODEL CHECK' as check_name,
  model_version,
  CASE
    WHEN model_version = 'prophet' THEN 'OK - Prophet model active'
    WHEN model_version = 'linear_fallback' THEN 'WARNING - Using linear fallback (Prophet may have failed)'
    ELSE 'UNKNOWN'
  END as status
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast')
WHERE forecast_date = (SELECT MAX(forecast_date) FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_forecast'))
LIMIT 1;

-- Final status
SELECT
  'SUCCESS: First install validation complete!' as status,
  'Open the Contract Consumption Monitor dashboard to view results' as next_step;
