# Databricks Account Monitor

**Track consumption, forecast contract exhaustion, and manage Databricks spending**

[![Databricks](https://img.shields.io/badge/Databricks-Asset_Bundle-FF3621?logo=databricks)](https://databricks.com)
[![Version](https://img.shields.io/badge/Version-1.7.0-green)](CHANGELOG.md)

---

## Overview

The Account Monitor is a complete solution for tracking Databricks consumption and predicting when contracts will be exhausted. It combines:

- **Real-time cost tracking** from Databricks system tables
- **ML-based forecasting** using Prophet to predict future consumption
- **Contract burndown visualization** showing historical spend and projected exhaustion dates
- **Automated refresh jobs** to keep data current

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Cost Monitoring** | Track spending across all workspaces, SKUs, and products |
| **Contract Management** | Store contract details (value, dates, cloud provider) |
| **Burndown Analysis** | Visualize cumulative spend vs contract limit |
| **ML Forecasting** | Prophet-based predictions with exhaustion dates |
| **Automated Jobs** | Daily refresh, weekly training, monthly summaries |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATABRICKS SYSTEM TABLES                     │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │ system.billing.usage│    │system.billing.      │             │
│  │                     │    │    list_prices      │             │
│  └──────────┬──────────┘    └──────────┬──────────┘             │
└─────────────┼──────────────────────────┼────────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DAILY REFRESH JOB                           │
│         Joins usage with prices, enriches with metadata          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UNITY CATALOG TABLES                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  contracts  │ │dashboard_data│ │contract_    │ │ forecast_  │ │
│  │             │ │              │ │  burndown   │ │  models    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEEKLY TRAINING JOB                           │
│              Train Prophet models per contract                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTRACT_FORECAST TABLE                        │
│          Daily predictions + exhaustion dates (p10/p50/p90)      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DASHBOARD NOTEBOOK                            │
│         Burndown charts, forecasts, cost analysis                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup

### Prerequisites

- Databricks workspace with **Unity Catalog** enabled
- Access to **system.billing** tables (account admin or granted access)
- **Databricks CLI** installed and configured
- A **SQL Warehouse** (serverless recommended)

### Step 1: Configure the Bundle

Edit `databricks.yml` with your settings:

```yaml
targets:
  dev:
    workspace:
      host: https://your-workspace.cloud.databricks.com
    variables:
      warehouse_id: "your-warehouse-id"   # From SQL Warehouses page
      catalog: "main"
      schema: "account_monitoring_dev"
```

### Step 2: Deploy

```bash
# Authenticate
databricks auth login --host https://your-workspace.cloud.databricks.com --profile YOUR_PROFILE

# Deploy all resources
databricks bundle deploy --profile YOUR_PROFILE

# Run setup to create tables
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

### Step 3: Add Your Contract Data

Open the **Contract Management CRUD** notebook and add your actual contract:

```sql
-- Example: Add a contract
MERGE INTO main.account_monitoring_dev.contracts AS target
USING (SELECT
  'CONTRACT-2026-001' as contract_id,
  'your-databricks-account-id' as account_id,
  'AWS' as cloud_provider,
  DATE '2025-07-01' as start_date,
  DATE '2026-06-30' as end_date,
  50000.00 as total_value,
  'USD' as currency,
  'SPEND' as commitment_type,
  'ACTIVE' as status,
  'Annual enterprise contract' as notes
) AS source
ON target.contract_id = source.contract_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

---

## Data Model

### System Tables (Read-Only, Managed by Databricks)

These are the source tables containing raw billing data:

| Table | Description |
|-------|-------------|
| `system.billing.usage` | Raw usage records (DBUs, dates, workspaces, SKUs) |
| `system.billing.list_prices` | Pricing information per SKU and cloud |

### Application Tables (Created by Setup Job)

#### `contracts` - Your Contract Information

| Column | Type | Description |
|--------|------|-------------|
| `contract_id` | STRING | Unique identifier (PK) |
| `account_id` | STRING | Databricks account ID |
| `cloud_provider` | STRING | AWS, Azure, or GCP |
| `start_date` | DATE | Contract start |
| `end_date` | DATE | Contract end |
| `total_value` | DECIMAL(18,2) | Contract commitment amount |
| `currency` | STRING | USD, EUR, etc. |
| `commitment_type` | STRING | SPEND or DBU |
| `status` | STRING | ACTIVE, EXPIRED, PENDING |
| `notes` | STRING | Additional notes |

#### `contract_burndown` - Daily Consumption Tracking

| Column | Type | Description |
|--------|------|-------------|
| `contract_id` | STRING | Link to contract |
| `usage_date` | DATE | Day of consumption |
| `daily_cost` | DECIMAL(18,2) | Cost for that day |
| `cumulative_cost` | DECIMAL(18,2) | Running total from contract start |
| `remaining_budget` | DECIMAL(18,2) | Contract value minus cumulative |
| `burn_rate_7d` | DECIMAL(18,2) | 7-day average daily spend |

#### `contract_forecast` - ML Predictions

| Column | Type | Description |
|--------|------|-------------|
| `contract_id` | STRING | Link to contract |
| `forecast_date` | DATE | Predicted date |
| `predicted_cumulative` | DECIMAL(18,2) | Predicted total spend by this date |
| `exhaustion_date_p10` | DATE | Optimistic exhaustion (10th percentile) |
| `exhaustion_date_p50` | DATE | Median exhaustion prediction |
| `exhaustion_date_p90` | DATE | Conservative exhaustion (90th percentile) |
| `model_version` | STRING | "prophet" or "linear_fallback" |

---

## Running the Solution

### Scheduled Jobs

| Job | Schedule | Purpose | Command to Run Manually |
|-----|----------|---------|------------------------|
| **Daily Refresh** | 2:00 AM UTC | Update consumption data from system tables | `databricks bundle run account_monitor_daily_refresh` |
| **Weekly Training** | Sunday 3:00 AM | Retrain Prophet models with latest data | `databricks bundle run account_monitor_weekly_training` |
| **Weekly Review** | Monday 8:00 AM | Contract analysis and anomaly detection | `databricks bundle run account_monitor_weekly_review` |
| **Monthly Summary** | 1st of month 6:00 AM | Archive old data, generate reports | `databricks bundle run account_monitor_monthly_summary` |

### Verifying Data Freshness

Run this query to check when data was last updated:

```sql
-- Check data freshness
SELECT
  'contract_burndown' as table_name,
  MAX(usage_date) as latest_data,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_stale
FROM main.account_monitoring_dev.contract_burndown

UNION ALL

SELECT
  'contract_forecast' as table_name,
  MAX(forecast_date) as latest_data,
  DATEDIFF(CURRENT_DATE(), MAX(created_at)) as days_stale
FROM main.account_monitoring_dev.contract_forecast;
```

**Expected Results:**
- `contract_burndown.latest_data` should be yesterday or today
- `contract_forecast` should be updated within the last 7 days

### Monitoring Job Health

```bash
# Check recent job runs
databricks jobs list --profile YOUR_PROFILE

# View run history for daily refresh
databricks runs list --job-id <JOB_ID> --profile YOUR_PROFILE
```

---

## Visualizations

### Contract Burndown Chart

The burndown chart shows cumulative spending over time compared to the contract limit:

```
Cost ($)
    │
 50K├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Contract Limit ($50,000)
    │                                    ╱
 40K├                               ╱╱╱╱
    │                          ╱╱╱╱
 30K├                     ╱╱╱╱
    │                ╱╱╱╱
 20K├           ▄▄▄▀
    │       ▄▄▀▀
 10K├   ▄▄▀▀
    │▄▀▀
    └────┬────┬────┬────┬────┬────┬────┬────┬────► Date
       Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb  Mar
       2025                                   2026

    ▄▄▄ Historical Consumption (Yellow)
    ╱╱╱ ML Forecast (Red)
    ─ ─ Contract Limit (Dashed Blue)
```

**How to read it:**
- **Yellow line**: Actual cumulative spending to date
- **Red line**: Prophet-predicted future spending
- **Dashed line**: Contract commitment amount
- **Intersection**: Where red crosses the dashed line = predicted exhaustion date

### Forecast with Exhaustion Date

The ML forecast visualization shows when the contract will be exhausted:

```
Cost ($)
    │
 50K├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╳ ─ ─ ─ ─  Contract Limit
    │                            ╱ │
 40K├                         ╱╱   │
    │                      ╱╱╱     │
 30K├                   ╱╱╱        │
    │                ╱╱╱           │
 20K├           ▄▄▄▀╱              │
    │       ▄▄▀▀                   │
 10K├   ▄▄▀▀                       │
    │▄▀▀                           │
    └────┬────┬────┬────┬────┬────┬┴───┬────► Date
       Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb
       2025                       ▲   2026
                                  │
                        Predicted Exhaustion
                         Date: 2026-01-30
```

**Forecast Summary Output:**
```
============================================================
FORECAST SUMMARY
============================================================
Contract ID: CONTRACT-2026-001
Contract Value: $50,000.00
Current Spend: $22,456.78
Model: prophet
Predicted Exhaustion Date: 2026-01-30
============================================================
```

---

## Notebooks

| Notebook | Purpose |
|----------|---------|
| **account_monitor_notebook.py** | Main dashboard with all visualizations |
| **contract_management_crud.py** | Add, update, delete contracts and metadata |
| **consumption_forecaster.py** | Prophet model training and inference |
| **post_deployment_validation.py** | Verify setup and data integrity |

### Opening the Dashboard

1. Navigate to your Databricks workspace
2. Go to **Workspace** > **Users** > **your-email** > **account_monitor** > **files** > **notebooks**
3. Open **account_monitor_notebook**
4. Click **Run All** to see all visualizations

---

## Troubleshooting

### No Data in Charts

```bash
# 1. Check system tables have data
databricks sql -e "SELECT COUNT(*) FROM system.billing.usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)"

# 2. Run the daily refresh
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE

# 3. Verify contract exists
databricks sql -e "SELECT * FROM main.account_monitoring_dev.contracts WHERE status = 'ACTIVE'"
```

### Forecast Not Showing

```bash
# 1. Check if forecast table has data
databricks sql -e "SELECT COUNT(*) FROM main.account_monitoring_dev.contract_forecast"

# 2. If empty, run the training job
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE

# 3. Check training logs
databricks sql -e "SELECT * FROM main.account_monitoring_dev.forecast_debug_log ORDER BY created_at DESC LIMIT 10"
```

### Jobs Failing

```bash
# Check job run status
databricks runs get --run-id <RUN_ID> --profile YOUR_PROFILE

# Common fixes:
# - Warehouse stopped: Start it in the SQL Warehouses page
# - Table not found: Run setup job first
# - Permission denied: Check Unity Catalog grants
```

---

## File Structure

```
databricks_conso_reports/
├── databricks.yml              # Bundle configuration
├── README.md                   # This file
│
├── notebooks/
│   ├── account_monitor_notebook.py    # Main dashboard
│   ├── contract_management_crud.py    # CRUD operations
│   ├── consumption_forecaster.py      # ML forecasting
│   └── post_deployment_validation.py  # Setup verification
│
├── sql/
│   ├── setup_schema.sql               # Create all tables
│   ├── insert_sample_data.sql         # Sample contract data
│   ├── refresh_dashboard_data.sql     # Daily data refresh
│   ├── refresh_contract_burndown.sql  # Burndown calculation
│   ├── build_forecast_features.sql    # ML feature prep
│   └── create_forecast_schema.sql     # Forecast tables
│
├── resources/
│   └── jobs.yml                       # Job definitions
│
└── docs/
    └── user-guide/
        └── USER_GUIDE.md              # Detailed documentation
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.7.0** | 2026-02-05 | Added Prophet ML forecasting, exhaustion predictions |
| **1.6.1** | 2026-02-04 | Removed salesforce_id, added notes column |
| **1.5.0** | 2026-02-01 | Initial stable release |

---

## Quick Reference

```bash
# Deploy everything
databricks bundle deploy --profile YOUR_PROFILE

# Run setup (first time only)
databricks bundle run account_monitor_setup --profile YOUR_PROFILE

# Refresh data now
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE

# Train forecast models
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE

# Check job status
databricks jobs list --profile YOUR_PROFILE
```

---

**Need more details?** See the [Complete User Guide](docs/user-guide/USER_GUIDE.md)
