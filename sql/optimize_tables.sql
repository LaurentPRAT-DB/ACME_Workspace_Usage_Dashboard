-- Optimize Dashboard Tables
-- Runs after daily refresh to improve query performance

-- Optimize main dashboard data table
OPTIMIZE {{catalog}}.{{schema}}.dashboard_data;
ANALYZE TABLE {{catalog}}.{{schema}}.dashboard_data COMPUTE STATISTICS;

-- Optimize contract burndown table
OPTIMIZE {{catalog}}.{{schema}}.contract_burndown;
ANALYZE TABLE {{catalog}}.{{schema}}.contract_burndown COMPUTE STATISTICS;

-- Optimize daily summary table if it exists
OPTIMIZE {{catalog}}.{{schema}}.daily_summary;
ANALYZE TABLE {{catalog}}.{{schema}}.daily_summary COMPUTE STATISTICS;

SELECT 'All tables optimized successfully' as status;
