# Contract Burndown Guide

## Overview

The contract burndown functionality has been fully implemented with sample data and is ready for visualization in Lakeview dashboards.

## What Was Added

### 1. **Database Objects**

#### Contract Burndown Table (`main.account_monitoring_dev.contract_burndown`)
Stores daily consumption data for each active contract:
- `cumulative_cost` - Running total of actual spend
- `projected_linear_burn` - Ideal linear consumption path
- `remaining_budget` - How much is left
- `budget_pct_consumed` - Percentage of contract consumed
- `time_pct_complete` - Percentage of contract period elapsed

#### Contract Burndown Summary View (`main.account_monitoring_dev.contract_burndown_summary`)
Provides latest status for each contract:
- Pace analysis (🟢 ON PACE, 🟡 ABOVE PACE, 🔴 OVER PACE, 🔵 UNDER PACE)
- Projected end date based on current burn rate
- Days remaining vs budget remaining

### 2. **Sample Contract Data**

Two contracts have been inserted:

**Contract 1: 1-Year $2000 Demo Contract**
- Contract ID: `CONTRACT-2026-001`
- Amount: $2,000 USD
- Period: 1 year (365 days from today going backwards)
- Status: ACTIVE
- Purpose: Demonstrates realistic burndown with actual usage data

**Contract 2: Enterprise Multi-Year Contract**
- Contract ID: `CONTRACT-ENTERPRISE-001`
- Amount: $500,000 USD
- Period: 3 years (2024-2026)
- Status: ACTIVE
- Purpose: Shows long-term contract tracking

### 3. **SQL Files Created**

#### `sql/refresh_contract_burndown.sql`
- Creates/refreshes the contract_burndown table
- Calculates cumulative costs and projections
- Creates the summary view
- Runs as part of daily refresh job

#### `sql/dashboard_contract_burndown_chart.sql`
- Optimized query for Lakeview dashboard visualization
- Shows last 90 days for better chart readability
- Returns data formatted for line charts

### 4. **Job Updates**

The **Daily Refresh Job** now includes:
1. `refresh_dashboard_data` - Loads usage/cost data
2. `refresh_contract_burndown` - ⭐ NEW: Calculates burndown metrics
3. `optimize_tables` - Optimizes all tables including burndown
4. `check_data_freshness` - Validates data quality

### 5. **Dashboard Configuration**

Updated `lakeview_dashboard_config.json` with:
- New `contract_burndown` dataset using the materialized table
- New `contract_summary` dataset showing pace analysis
- Enhanced burndown chart showing:
  - **Actual consumption** (blue line) - Real spend over time
  - **Ideal consumption** (green line) - Linear burn rate
  - **Contract value** (horizontal line) - Total commitment

## How to View the Data

### Query the Burndown Table

```sql
-- View burndown data for a specific contract
SELECT
  usage_date,
  daily_cost,
  cumulative_cost,
  projected_linear_burn,
  remaining_budget,
  budget_pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE contract_id = 'CONTRACT-2026-001'
ORDER BY usage_date;

-- View summary for all contracts
SELECT * FROM main.account_monitoring_dev.contract_burndown_summary;
```

### Check Contract Status

```sql
-- See which contracts are over/under pace
SELECT
  contract_id,
  commitment,
  total_consumed,
  consumed_pct,
  pace_status,
  days_remaining,
  projected_end_date
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY
  CASE
    WHEN pace_status LIKE '%OVER%' THEN 1
    WHEN pace_status LIKE '%ABOVE%' THEN 2
    ELSE 3
  END;
```

## Creating the Lakeview Dashboard

### Step 1: Create a New Dashboard

1. Go to **Dashboards** in Databricks workspace
2. Click **Create Dashboard**
3. Select **Lakeview Dashboard**

### Step 2: Create SQL Queries

Create these queries in SQL Editor:

**Query 1: Contract Burndown Chart Data**
```sql
SELECT
  contract_id,
  CONCAT(contract_id, ' ($', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
  usage_date as date,
  cumulative_cost as actual_consumption,
  projected_linear_burn as ideal_consumption,
  commitment as contract_value,
  budget_pct_consumed as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
ORDER BY contract_id, usage_date;
```

**Query 2: Contract Summary Table**
```sql
SELECT
  contract_id,
  cloud_provider,
  CONCAT('$', FORMAT_NUMBER(commitment, 0)) as total_value,
  CONCAT('$', FORMAT_NUMBER(total_consumed, 2)) as consumed,
  CONCAT('$', FORMAT_NUMBER(budget_remaining, 2)) as remaining,
  CONCAT(consumed_pct, '%') as pct_consumed,
  pace_status,
  days_remaining,
  projected_end_date
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY consumed_pct DESC;
```

### Step 3: Create Visualizations

#### Line Chart: Contract Burndown
- **Query**: Use Query 1 above
- **Chart Type**: Line Chart
- **X-Axis**: `date`
- **Y-Axis**:
  - `actual_consumption` (Label: "Actual Spend")
  - `ideal_consumption` (Label: "Ideal Linear Burn")
  - `contract_value` (Label: "Contract Value")
- **Group By**: `contract_label`
- **Legend**: Show
- **Title**: "Contract Burndown - Actual vs Ideal"

#### Table: Contract Summary
- **Query**: Use Query 2 above
- **Chart Type**: Table
- **Title**: "Active Contracts Status"

### Step 4: Interpret the Visualization

**What to Look For:**

✅ **On Pace** (Green)
- Actual consumption line follows ideal line closely
- Budget consumed ≈ time elapsed

⚠️ **Above Pace** (Yellow)
- Actual consumption is 10-20% ahead of ideal
- Consider cost optimization measures

🚨 **Over Pace** (Red)
- Actual consumption is >20% ahead of ideal
- Risk of running out of budget early
- Immediate action required

📉 **Under Pace** (Blue)
- Actual consumption is <80% of ideal
- May have unused capacity
- Consider accelerating usage or renegotiating

## Maintenance

### Daily Automatic Refresh

The contract burndown table is automatically refreshed every day at 2 AM UTC by the daily refresh job:
```bash
databricks jobs list --profile LPT_FREE_EDITION | grep "Daily Refresh"
```

### Manual Refresh

To manually refresh the burndown data:
```bash
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

Or run just the burndown refresh in SQL Editor:
```sql
-- Run the refresh script
%run /Workspace/Users/your.email@company.com/account_monitor/sql/refresh_contract_burndown
```

## Adding Real Contracts

Replace the sample contracts with your actual contracts:

```sql
-- Delete sample contracts
DELETE FROM main.account_monitoring_dev.contracts
WHERE contract_id IN ('CONTRACT-2026-001', 'CONTRACT-ENTERPRISE-001');

-- Insert your real contract
INSERT INTO main.account_monitoring_dev.contracts VALUES (
  'YOUR-CONTRACT-ID',           -- contract_id
  'your-account-id',            -- account_id (from system.billing.usage)
  'aws',                        -- cloud_provider (aws, azure, gcp)
  DATE'2025-01-01',             -- start_date
  DATE'2026-12-31',             -- end_date
  100000.00,                    -- total_value
  'USD',                        -- currency
  'SPEND',                      -- commitment_type (SPEND or DBU)
  'ACTIVE',                     -- status
  'Description of contract',    -- notes
  CURRENT_TIMESTAMP(),          -- created_at
  CURRENT_TIMESTAMP()           -- updated_at
);

-- Refresh burndown data
%run /Workspace/Users/your.email@company.com/account_monitor/sql/refresh_contract_burndown
```

## Troubleshooting

### No Data in Burndown Table

**Check if contracts exist:**
```sql
SELECT * FROM main.account_monitoring_dev.contracts WHERE status = 'ACTIVE';
```

**Check if dashboard data covers contract period:**
```sql
SELECT
  MIN(usage_date) as earliest_data,
  MAX(usage_date) as latest_data
FROM main.account_monitoring_dev.dashboard_data;
```

**Solution**: Ensure contract dates overlap with available usage data.

### Chart Shows Flat Lines

**Likely cause**: No actual consumption data for the contract period.

**Check consumption:**
```sql
SELECT
  c.contract_id,
  COUNT(*) as data_points,
  SUM(d.actual_cost) as total_cost
FROM main.account_monitoring_dev.contracts c
LEFT JOIN main.account_monitoring_dev.dashboard_data d
  ON c.account_id = d.account_id
  AND c.cloud_provider = d.cloud_provider
  AND d.usage_date BETWEEN c.start_date AND c.end_date
WHERE c.status = 'ACTIVE'
GROUP BY c.contract_id;
```

### Burndown Table Not Updating

**Check job run history:**
```bash
databricks jobs runs list --profile LPT_FREE_EDITION --limit 5
```

**Manually run refresh:**
```bash
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

## Next Steps

1. ✅ Sample contracts loaded with realistic $2000 1-year contract
2. ✅ Burndown table populated with historical data
3. ✅ Daily refresh job configured
4. 📋 **TODO**: Create Lakeview dashboard with burndown chart
5. 📋 **TODO**: Replace sample contracts with real contracts
6. 📋 **TODO**: Set up alerts for contracts over pace

## Reference

- **Burndown Table**: `main.account_monitoring_dev.contract_burndown`
- **Summary View**: `main.account_monitoring_dev.contract_burndown_summary`
- **Dashboard Config**: `lakeview_dashboard_config.json`
- **Refresh SQL**: `sql/refresh_contract_burndown.sql`
- **Chart SQL**: `sql/dashboard_contract_burndown_chart.sql`

---

**Dashboard Location**: `/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/`

**Job Status**: Check at https://dbc-cbb9ade6-873a.cloud.databricks.com/#job/1070695203704098
