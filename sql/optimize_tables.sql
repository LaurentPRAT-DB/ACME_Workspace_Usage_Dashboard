-- Optimize Dashboard Tables
-- Runs after daily refresh to improve query performance

-- Optimize main dashboard data table
OPTIMIZE main.account_monitoring_dev.dashboard_data;
ANALYZE TABLE main.account_monitoring_dev.dashboard_data COMPUTE STATISTICS;

-- Optimize contract burndown table
OPTIMIZE main.account_monitoring_dev.contract_burndown;
ANALYZE TABLE main.account_monitoring_dev.contract_burndown COMPUTE STATISTICS;

-- Optimize daily summary table if it exists
OPTIMIZE main.account_monitoring_dev.daily_summary;
ANALYZE TABLE main.account_monitoring_dev.daily_summary COMPUTE STATISTICS;

SELECT 'All tables optimized successfully' as status;
