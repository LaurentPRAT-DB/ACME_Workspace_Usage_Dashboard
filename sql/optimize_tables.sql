-- Optimize Dashboard Tables
-- Runs after daily refresh to improve query performance

-- Optimize main dashboard data table
OPTIMIZE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data');
ANALYZE TABLE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.dashboard_data') COMPUTE STATISTICS;

-- Optimize contract burndown table
OPTIMIZE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown');
ANALYZE TABLE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contract_burndown') COMPUTE STATISTICS;

-- Optimize daily summary table if it exists
OPTIMIZE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.daily_summary');
ANALYZE TABLE IDENTIFIER({{catalog}} || '.' || {{schema}} || '.daily_summary') COMPUTE STATISTICS;

SELECT 'All tables optimized successfully' as status;
