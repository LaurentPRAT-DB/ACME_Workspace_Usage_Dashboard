-- Archive Old Data
-- Moves data older than 2 years to archive table

-- Create archive table if it doesn't exist
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.dashboard_data_archive
LIKE main.account_monitoring_dev.dashboard_data;

-- Archive data older than 2 years
INSERT INTO main.account_monitoring_dev.dashboard_data_archive
SELECT *
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- Count archived records
CREATE OR REPLACE TEMP VIEW archive_summary AS
SELECT
  COUNT(*) as archived_records,
  MIN(usage_date) as oldest_date,
  MAX(usage_date) as newest_date,
  ROUND(SUM(actual_cost), 2) as total_archived_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- Delete archived data from main table
DELETE FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- Optimize tables after deletion
OPTIMIZE main.account_monitoring_dev.dashboard_data;
VACUUM main.account_monitoring_dev.dashboard_data RETAIN 168 HOURS;

-- Return summary
SELECT
  'Archive completed' as status,
  archived_records,
  oldest_date,
  newest_date,
  total_archived_cost
FROM archive_summary;
