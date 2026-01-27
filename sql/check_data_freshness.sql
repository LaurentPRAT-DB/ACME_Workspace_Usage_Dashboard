-- Check Data Freshness
-- Validates that system tables have recent data

CREATE OR REPLACE TEMP VIEW freshness_check AS
SELECT
  'system.billing.usage' as table_name,
  MAX(usage_date) as latest_date,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'OK'
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 5 THEN 'WARNING'
    ELSE 'CRITICAL'
  END as status
FROM system.billing.usage
WHERE record_type = 'ORIGINAL';

-- Display freshness status
SELECT
  table_name,
  latest_date,
  days_behind,
  status,
  CASE
    WHEN status = 'CRITICAL' THEN 'Data is more than 5 days old'
    WHEN status = 'WARNING' THEN 'Data is 3-5 days old'
    ELSE 'Data is fresh'
  END as message
FROM freshness_check;

-- Check and display result
SELECT
  CASE
    WHEN days_behind > 5 THEN 'WARNING: System tables data is more than 5 days old'
    ELSE 'Data freshness check passed'
  END as result
FROM freshness_check;
