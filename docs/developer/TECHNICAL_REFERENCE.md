# Account Monitor - Technical Reference

**For: Developers, Data Engineers, Contributors**

---

## Overview

This document covers the technical internals of the Account Monitor system, including schema design, SQL patterns, debugging approaches, and architectural decisions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐                                                        │
│  │  system.billing  │                                                        │
│  │  ┌────────────┐  │                                                        │
│  │  │   usage    │──┼──┐                                                     │
│  │  └────────────┘  │  │                                                     │
│  │  ┌────────────┐  │  │    ┌──────────────────┐                             │
│  │  │list_prices │──┼──┼───▶│  dashboard_data  │ (aggregated billing)        │
│  │  └────────────┘  │  │    └────────┬─────────┘                             │
│  └──────────────────┘  │             │                                       │
│                        │             ▼                                       │
│  ┌──────────────────┐  │    ┌──────────────────┐    ┌───────────────────┐   │
│  │    contracts     │──┼───▶│contract_burndown │───▶│ contract_forecast │   │
│  │  (YAML config)   │  │    │ (cumulative cost)│    │ (Prophet ML)      │   │
│  └──────────────────┘  │    └──────────────────┘    └───────────────────┘   │
│                        │                                      │              │
│                        │                                      ▼              │
│  ┌──────────────────┐  │                           ┌───────────────────┐    │
│  │  discount_tiers  │──┼──────────────────────────▶│ scenario_summary  │    │
│  │  (YAML config)   │  │                           │ (What-If results) │    │
│  └──────────────────┘  │                           └───────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schema Reference

### Core Tables

#### contracts
Primary contract definitions loaded from YAML config.

```sql
CREATE TABLE contracts (
  contract_id STRING,
  cloud_provider STRING,      -- AWS, AZURE, GCP
  start_date DATE,
  end_date DATE,
  total_value DECIMAL(18,2),  -- Commitment amount
  currency STRING,
  status STRING,              -- ACTIVE, INACTIVE
  customer_name STRING,
  account_id STRING
);
```

#### dashboard_data
Aggregated billing data from system tables.

```sql
CREATE TABLE dashboard_data (
  usage_date DATE,
  workspace_id STRING,
  sku_name STRING,
  usage_quantity DOUBLE,
  usage_unit STRING,
  dollar_cost DOUBLE,         -- List price * quantity
  cloud_provider STRING
);
```

#### contract_burndown
Daily cumulative consumption per contract.

```sql
CREATE TABLE contract_burndown (
  contract_id STRING,
  usage_date DATE,
  daily_cost DOUBLE,
  cumulative_cost DOUBLE,     -- Running total
  commitment DOUBLE,          -- From contracts.total_value
  cloud_provider STRING,
  start_date DATE,
  end_date DATE
);
```

#### contract_forecast
ML predictions from Prophet model.

```sql
CREATE TABLE contract_forecast (
  contract_id STRING,
  forecast_date DATE,
  forecast_model STRING,      -- 'prophet' or 'linear_fallback'
  predicted_daily DOUBLE,
  predicted_cumulative DOUBLE,
  yhat_lower DOUBLE,          -- 10th percentile
  yhat_upper DOUBLE,          -- 90th percentile
  exhaustion_date_p50 DATE,   -- When cumulative crosses commitment
  training_date TIMESTAMP
);
```

### What-If Tables

#### discount_tiers
Configurable discount rates by commitment and duration.

```sql
CREATE TABLE discount_tiers (
  tier_id STRING,
  tier_name STRING,
  min_commitment DOUBLE,
  max_commitment DOUBLE,
  duration_years INT,
  discount_rate DOUBLE,       -- 0.0 to 1.0
  created_at TIMESTAMP
);
```

#### scenario_summary
Pre-computed What-If scenario results.

```sql
CREATE TABLE scenario_summary (
  scenario_id STRING,
  contract_id STRING,
  scenario_name STRING,
  discount_rate DOUBLE,
  original_commitment DOUBLE,
  discounted_commitment DOUBLE,
  predicted_consumption DOUBLE,
  total_savings DOUBLE,
  utilization_pct DOUBLE,
  exhaustion_date DATE,
  is_sweet_spot BOOLEAN,
  strategy_reason STRING,
  created_at TIMESTAMP
);
```

### Views

#### contract_burndown_summary
Real-time contract status aggregation.

```sql
CREATE VIEW contract_burndown_summary AS
SELECT
  contract_id,
  commitment,
  MAX(cumulative_cost) as total_consumed,
  commitment - MAX(cumulative_cost) as remaining,
  MAX(cumulative_cost) / commitment * 100 as consumed_pct,
  DATEDIFF(CURRENT_DATE(), MIN(start_date)) as days_into_contract,
  DATEDIFF(MAX(end_date), MIN(start_date)) as total_days
FROM contract_burndown
GROUP BY contract_id, commitment;
```

---

## SQL Patterns

### Parameterized Queries with IDENTIFIER()

DAB uses `IDENTIFIER()` for dynamic table names:

```sql
-- Correct: IDENTIFIER() for table references
SELECT * FROM IDENTIFIER({{catalog}} || '.' || {{schema}} || '.contracts');

-- Incorrect: String interpolation (won't work)
SELECT * FROM '${catalog}.${schema}.contracts';  -- ERROR
```

**Limitation**: `IDENTIFIER()` doesn't work with all DDL:

```sql
-- Works
CREATE TABLE IF NOT EXISTS IDENTIFIER(...) AS SELECT ...;
INSERT INTO IDENTIFIER(...) VALUES ...;
SELECT * FROM IDENTIFIER(...);

-- Does NOT work
CREATE TABLE ... LIKE IDENTIFIER(...);  -- ERROR
ALTER TABLE IDENTIFIER(...) ADD COLUMN ...;  -- May fail
```

**Workaround for LIKE**: Use CTAS with false condition:

```sql
-- Instead of: CREATE TABLE new_table LIKE existing_table
CREATE TABLE IF NOT EXISTS IDENTIFIER(...)
AS SELECT * FROM IDENTIFIER(...)
WHERE 1 = 0;  -- Creates empty table with same schema
```

### CTEs vs Temp Views

CTEs are scoped to a single statement only:

```sql
-- PROBLEM: CTE goes out of scope
WITH my_data AS (SELECT * FROM table1)
SELECT * FROM my_data;  -- Works

SELECT * FROM my_data;  -- ERROR: Table not found

-- SOLUTION: Use temp views for multi-statement scripts
CREATE OR REPLACE TEMP VIEW my_data AS SELECT * FROM table1;
SELECT * FROM my_data;  -- Works
SELECT * FROM my_data;  -- Still works
```

### Date Handling in SQL

```sql
-- Current date (midnight)
CURRENT_DATE()

-- Days between dates
DATEDIFF(end_date, start_date)

-- Add days
DATE_ADD(start_date, 30)

-- Format for display
DATE_FORMAT(usage_date, 'MMM d, yyyy')  -- "Feb 11, 2026"

-- Month extraction
DATE_TRUNC('month', usage_date)
```

### Aggregation Patterns

```sql
-- Running total (cumulative sum)
SUM(daily_cost) OVER (
  PARTITION BY contract_id
  ORDER BY usage_date
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) as cumulative_cost

-- Month-over-month change
LAG(total_cost, 1) OVER (ORDER BY month) as prev_month,
(total_cost - LAG(total_cost, 1) OVER (ORDER BY month)) /
  NULLIF(LAG(total_cost, 1) OVER (ORDER BY month), 0) * 100 as mom_change_pct
```

---

## Prophet ML Integration

### Installation on Serverless

Prophet requires subprocess installation (not %pip):

```python
# This works on serverless
import subprocess
subprocess.run(['pip', 'install', 'prophet'], check=True)

# This FAILS on serverless
# %pip install prophet  # Don't use this
```

### Model Training

```python
from prophet import Prophet
import pandas as pd

# Prepare data - Prophet requires 'ds' and 'y' columns
df = spark.sql("""
    SELECT usage_date as ds, daily_cost as y
    FROM contract_burndown
    WHERE contract_id = 'CONTRACT-001'
""").toPandas()

# Train model
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False
)
model.fit(df)

# Forecast 365 days
future = model.make_future_dataframe(periods=365)
forecast = model.predict(future)
```

### Handling Data Type Issues

```python
# Decimal to float conversion (required for Prophet)
df['y'] = df['y'].astype(float)

# NaT handling for dates
def safe_date_str(val):
    if pd.isna(val) or val is pd.NaT:
        return 'NULL'
    return f"'{val.strftime('%Y-%m-%d')}'"
```

### Linear Fallback

When Prophet can't train (< 30 days data), use linear fallback:

```python
if len(df) < 30:
    # Simple linear projection
    avg_daily = df['y'].mean()
    forecast = [avg_daily] * 365
    model_type = 'linear_fallback'
else:
    # Use Prophet
    model.fit(df)
    model_type = 'prophet'
```

---

## Job Definitions

### jobs.yml Structure

```yaml
resources:
  jobs:
    account_monitor_daily_refresh:
      name: "Account Monitor - Daily Refresh"
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"  # 2 AM daily
        timezone_id: UTC
      tasks:
        - task_key: refresh_data
          notebook_task:
            notebook_path: ${workspace.file_path}/sql/refresh_dashboard_data.sql
          warehouse_id: ${var.warehouse_id}
```

### Task Dependencies

```yaml
tasks:
  - task_key: setup_schema
    # First task - no dependencies

  - task_key: load_data
    depends_on:
      - task_key: setup_schema  # Runs after setup

  - task_key: train_model
    depends_on:
      - task_key: load_data  # Runs after data load
```

### Parameter Passing

```yaml
notebook_task:
  notebook_path: ${workspace.file_path}/notebooks/forecaster.py
  base_parameters:
    mode: "inference"
    catalog: ${var.catalog}
    schema: ${var.schema}
```

---

## Dashboard JSON Structure

### Lakeview Dashboard Format

```json
{
  "display_name": "Contract Consumption Monitor",
  "datasets": [
    {
      "name": "ds_contracts",
      "query": "SELECT * FROM main.account_monitoring_dev.contracts"
    }
  ],
  "pages": [
    {
      "name": "executive_summary",
      "display_name": "Executive Summary",
      "layout": [
        {
          "widget": {
            "name": "w_total_value",
            "queries": [
              {
                "name": "main_query",
                "query": {
                  "dataset_name": "ds_contracts",
                  "fields": [...],
                  "disaggregated": true
                }
              }
            ],
            "spec": {
              "version": 3,
              "widgetType": "counter",
              "encodings": {...}
            }
          },
          "position": {"x": 0, "y": 0, "width": 2, "height": 2}
        }
      ]
    }
  ]
}
```

### Widget Types

| Type | Use Case |
|------|----------|
| `counter` | Single KPI value |
| `table` | Data grid |
| `bar` | Bar chart |
| `line` | Line/area chart |
| `pie` | Pie chart |

### Dataset Queries

Datasets support full SQL or disaggregated field queries:

```json
// Full SQL query
{
  "name": "ds_custom",
  "query": "SELECT a, SUM(b) FROM table GROUP BY a"
}

// Disaggregated (widget builds query from fields)
{
  "query": {
    "dataset_name": "ds_base",
    "fields": [
      {"name": "usage_date", "expression": "`usage_date`"},
      {"name": "total_cost", "expression": "SUM(`dollar_cost`)"}
    ],
    "disaggregated": true
  }
}
```

---

## Debugging Guide

### Common Errors

#### "Table or view not found"

```
[TABLE_OR_VIEW_NOT_FOUND] The table or view 'xyz' cannot be found
```

**Causes**:
1. CTE out of scope (see CTEs vs Temp Views)
2. Wrong catalog/schema
3. Table not created yet

**Debug**:
```sql
SHOW TABLES IN main.account_monitoring_dev;
DESCRIBE TABLE main.account_monitoring_dev.contracts;
```

#### IDENTIFIER() syntax errors

```
[PARSE_SYNTAX_ERROR] Syntax error at or near '('
```

**Cause**: Using IDENTIFIER() where not supported.

**Fix**: Use literal table name or CTAS workaround.

#### Decimal * float TypeError

```
TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'
```

**Cause**: Spark returns Decimal, pandas expects float.

**Fix**: Convert before arithmetic:
```python
df['column'] = df['column'].astype(float)
```

### Validation Queries

```sql
-- Check data freshness
SELECT
  'contract_burndown' as table_name,
  MAX(usage_date) as latest_date,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_stale
FROM main.account_monitoring_dev.contract_burndown

UNION ALL

SELECT
  'contract_forecast',
  MAX(forecast_date),
  DATEDIFF(CURRENT_DATE(), MAX(forecast_date))
FROM main.account_monitoring_dev.contract_forecast;

-- Verify Prophet vs linear_fallback
SELECT forecast_model, COUNT(*) as records
FROM main.account_monitoring_dev.contract_forecast
GROUP BY forecast_model;
```

---

## Development Workflow

### Local Testing

```bash
# Validate bundle configuration
databricks bundle validate --profile YOUR_PROFILE

# Deploy to dev target
databricks bundle deploy --profile YOUR_PROFILE

# Run specific job
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE

# Force deploy (overwrites remote changes)
databricks bundle deploy --force --profile YOUR_PROFILE
```

### Dashboard Updates via API

When bundle deploy doesn't update the dashboard:

```bash
# Get current dashboard
databricks api get /api/2.0/lakeview/dashboards/DASHBOARD_ID

# Update dashboard
databricks api patch /api/2.0/lakeview/dashboards/DASHBOARD_ID \
  --json '{"serialized_dashboard": "..."}'

# Publish changes
databricks api post /api/2.0/lakeview/dashboards/DASHBOARD_ID/published \
  --json '{}'
```

### Adding New Tables

1. Add CREATE TABLE to `sql/setup_schema.sql`
2. Add IDENTIFIER() compatible INSERT to appropriate SQL file
3. Update `sql/validate_first_install.sql` to check new table
4. Update schema documentation

### Adding Dashboard Widgets

1. Add dataset to `datasets` array in dashboard JSON
2. Add widget to appropriate page's `layout` array
3. Define position (x, y, width, height in grid units)
4. Deploy and publish

---

## File Organization

```
databricks_conso_reports/
├── config/
│   ├── contracts.yml          # Contract definitions
│   └── discount_tiers.yml     # What-If tier config
├── notebooks/
│   ├── consumption_forecaster.py    # Prophet ML training
│   ├── setup_contracts.py           # Contract loader
│   └── whatif_simulator.py          # Scenario generator
├── resources/
│   ├── dashboards/
│   │   └── contract_consumption_monitor.json
│   └── jobs.yml               # Job definitions
├── sql/
│   ├── setup_schema.sql       # Table creation
│   ├── refresh_dashboard_data.sql
│   ├── refresh_contract_burndown.sql
│   └── validate_first_install.sql
└── databricks.yml             # Bundle configuration
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [SCHEMA_REFERENCE.md](../SCHEMA_REFERENCE.md) | Detailed schema documentation |
| [scheduled_jobs_guide.md](../scheduled_jobs_guide.md) | Job explanations with examples |
| [ADMIN_GUIDE.md](../administrator/ADMIN_GUIDE.md) | Installation and operations |

---

*Last updated: February 2026*
