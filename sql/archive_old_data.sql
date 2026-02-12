-- Archive Old Data
-- Moves data older than 2 years to archive table

-- ============================================================================
-- Step 1: Create archive table if it doesn't exist (using CTAS with empty result)
-- ============================================================================

CREATE TABLE IF NOT EXISTS IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data_archive')
AS SELECT * FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
WHERE 1 = 0;

-- ============================================================================
-- Step 2: Count records to be archived (before archiving)
-- ============================================================================

CREATE OR REPLACE TEMP VIEW archive_summary AS
SELECT
  COUNT(*) as archived_records,
  MIN(usage_date) as oldest_date,
  MAX(usage_date) as newest_date,
  ROUND(SUM(actual_cost), 2) as total_archived_cost
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- ============================================================================
-- Step 3: Archive data older than 2 years
-- ============================================================================

INSERT INTO IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data_archive')
SELECT *
FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- ============================================================================
-- Step 4: Delete archived data from main table
-- ============================================================================

DELETE FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data')
WHERE usage_date < DATE_SUB(CURRENT_DATE(), 730);

-- ============================================================================
-- Step 5: Optimize tables after deletion
-- ============================================================================

OPTIMIZE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data');
OPTIMIZE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data_archive');

-- ============================================================================
-- Step 6: Return summary
-- ============================================================================

SELECT
  'Archive completed' as status,
  archived_records,
  oldest_date,
  newest_date,
  total_archived_cost
FROM archive_summary;
