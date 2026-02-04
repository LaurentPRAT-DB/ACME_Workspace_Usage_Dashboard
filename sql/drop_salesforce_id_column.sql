-- Migration Script: Remove salesforce_id Column
-- This script removes the salesforce_id column from account_metadata and dashboard_data tables

-- Drop salesforce_id from account_metadata if it exists
ALTER TABLE main.account_monitoring_dev.account_metadata
DROP COLUMN IF EXISTS salesforce_id;

-- Drop salesforce_id from dashboard_data if it exists
ALTER TABLE main.account_monitoring_dev.dashboard_data
DROP COLUMN IF EXISTS salesforce_id;

-- Verify columns were dropped
SELECT 'Migration complete - salesforce_id column removed' as status;

-- Show remaining columns in account_metadata
DESCRIBE main.account_monitoring_dev.account_metadata;
