# Account Monitor - User Guide

**Version 1.12.0**

A comprehensive guide for managing and monitoring Databricks account costs and contract consumption.

---

## Table of Contents

1. [Overview](#overview)
2. [Understanding the Data Model](#understanding-the-data-model)
3. [Installation & Setup](#installation--setup)
4. [Data Refresh Jobs](#data-refresh-jobs)
5. [Managing Contracts (CRUD Operations)](#managing-contracts-crud-operations)
6. [Dashboard & Burndown Charts](#dashboard--burndown-charts)
7. [Consumption Forecasting (ML)](#consumption-forecasting-ml)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Account Monitor solution helps you:
- Track Databricks usage and costs across your organization
- Monitor contract consumption and burndown
- Manage contracts and account metadata
- Visualize spending trends and forecasts

### Key Components

- **Unity Catalog Tables**: Store contracts and account metadata
- **System Tables**: Source of usage and pricing data (`system.billing.usage`, `system.billing.list_prices`)
- **Jobs**: Automated data refresh (daily, weekly, monthly)
- **Notebooks**: Interactive dashboards and CRUD operations
- **Lakeview Dashboard**: Visual analytics and burndown charts

---

## Understanding the Data Model

### Tables Overview

The solution uses three main schemas:

#### 1. `main.account_monitoring_dev` (Development)
- **contracts** - Contract tracking and details
- **account_metadata** - Account organization and team info
- **dashboard_data** - Pre-aggregated usage data
- **daily_summary** - Daily cost summaries
- **contract_burndown** - Contract consumption tracking
- **contract_burndown_summary** - Aggregated burndown data

#### 2. `account_monitoring` (Production/Notebook)
Same structure as dev, used by interactive notebooks

### Table Schemas

#### contracts
Stores contract information for consumption tracking.

| Column | Type | Description |
|--------|------|-------------|
| contract_id | STRING | Unique contract identifier (Primary Key) |
| account_id | STRING | Databricks account ID |
| cloud_provider | STRING | Cloud provider: aws, azure, gcp |
| start_date | DATE | Contract start date |
| end_date | DATE | Contract end date |
| total_value | DECIMAL(18,2) | Total contract value |
| currency | STRING | Currency code (e.g., USD, EUR) |
| commitment_type | STRING | DBU or SPEND |
| status | STRING | ACTIVE, EXPIRED, or PENDING |
| notes | STRING | Additional contract notes |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

**Example Data:**
```sql
contract_id: '1694992'
account_id: 'abc-123-def'
cloud_provider: 'AWS'
start_date: 2025-02-04
end_date: 2027-02-04
total_value: 3000.00
currency: 'USD'
commitment_type: 'SPEND'
status: 'ACTIVE'
notes: '2-year $3000 sample contract'
```

#### account_metadata
Stores organizational information for accounts.

| Column | Type | Description |
|--------|------|-------------|
| account_id | STRING | Databricks account ID (Primary Key) |
| customer_name | STRING | Customer display name |
| business_unit_l0 | STRING | Top-level business unit (e.g., AMER, EMEA) |
| business_unit_l1 | STRING | Second-level unit (e.g., West, East) |
| business_unit_l2 | STRING | Third-level unit (e.g., California) |
| business_unit_l3 | STRING | Fourth-level unit (e.g., Enterprise) |
| account_executive | STRING | Account Executive name |
| solutions_architect | STRING | Solutions Architect name |
| delivery_solutions_architect | STRING | Delivery SA name |
| region | STRING | Geographic region |
| industry | STRING | Customer industry |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

**Example Data:**
```sql
account_id: 'abc-123-def'
customer_name: 'Acme Corporation'
business_unit_l0: 'AMER'
business_unit_l1: 'West'
business_unit_l2: 'California'
business_unit_l3: 'Enterprise'
account_executive: 'John Doe'
solutions_architect: 'Jane Smith'
```

#### dashboard_data
Pre-aggregated usage data for fast dashboard queries.

**Key Columns:**
- usage_date, account_id, customer_name
- business_unit_l0 through l3
- workspace_id, cloud_provider
- sku_name, usage_quantity
- actual_cost, list_cost
- product_category (All Purpose Compute, Jobs, SQL, etc.)

This table is refreshed daily by the `account_monitor_daily_refresh` job.

---

## Installation & Setup

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- Databricks CLI installed and authenticated
- Access to `system.billing.usage` and `system.billing.list_prices` tables
- SQL Warehouse (serverless or provisioned)

### Step 1: Authenticate with Databricks

```bash
# Check your current profile
databricks auth profiles

# If needed, authenticate
databricks auth login https://your-workspace.cloud.databricks.com --profile YOUR_PROFILE
```

### Step 2: Configure the Bundle

Edit `databricks.yml` to set your profile:

```yaml
workspace:
  profile: YOUR_PROFILE  # Change this to your profile name

variables:
  warehouse_id: "your-warehouse-id"  # Your SQL Warehouse ID
```

### Step 3: Deploy with Databricks Asset Bundles (DABs)

```bash
# Validate the bundle configuration
databricks bundle validate --profile YOUR_PROFILE

# Deploy to development environment
databricks bundle deploy --profile YOUR_PROFILE

# Deploy to production (optional)
databricks bundle deploy --target prod --profile YOUR_PROFILE
```

The deployment will:
- ✅ Upload notebooks to workspace
- ✅ Upload SQL files
- ✅ Create/update 4 scheduled jobs
- ✅ Configure permissions

### Step 4: Run Initial Setup

Run the setup job to create tables and load sample data:

```bash
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

Or run it from the Databricks UI:
1. Go to **Workflows** > **Jobs**
2. Find `[dev] Account Monitor - Setup`
3. Click **Run Now**

This will:
- Create Unity Catalog schema and tables
- Insert sample account metadata and contracts
- Verify data integrity

### Step 5: Update Account Information

After setup, update the tables with your actual data:

1. Open the **Contract Management CRUD** notebook
2. Navigate to the "UPDATE" section
3. Update account metadata with your organization details
4. Add your actual contracts

---

## Data Refresh Jobs

The solution includes automated jobs to keep data fresh.

### Job Overview

| Job | Schedule | Purpose |
|-----|----------|---------|
| **Setup** | On-demand | Initial schema and data setup |
| **Daily Refresh** | Daily at 2 AM UTC | Refresh dashboard data from system tables |
| **Weekly Review** | Monday at 8 AM UTC | Contract analysis and cost anomalies |
| **Monthly Summary** | 1st of month at 6 AM UTC | Monthly summary and data archival |

### Daily Refresh Job

**Tasks:**
1. **refresh_dashboard_data** - Loads last 365 days from system.billing.usage
2. **refresh_contract_burndown** - Updates contract consumption tracking
3. **optimize_tables** - Runs OPTIMIZE on Delta tables
4. **check_data_freshness** - Validates data is up-to-date

**Monitoring:**
```bash
# Check job status
databricks bundle summary --profile YOUR_PROFILE

# View recent runs
databricks jobs list-runs --job-id YOUR_JOB_ID --profile YOUR_PROFILE
```

### Weekly Review Job

Analyzes contracts and identifies:
- Contract consumption rates
- Cost anomalies (unexpected spikes)
- Top consuming workspaces/resources

### Monthly Summary Job

Generates monthly reports and:
- Archives data older than 2 years
- Calculates month-over-month trends
- Identifies expiring contracts

### Running Jobs Manually

**Via CLI:**
```bash
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE
```

**Via UI:**
1. Navigate to **Workflows** > **Jobs**
2. Find the job (e.g., `[dev] Account Monitor - Daily Refresh`)
3. Click **Run Now**
4. Monitor progress in the run details page

---

## Managing Contracts (CRUD Operations)

Use the **Contract Management CRUD** notebook for all contract and account metadata operations.

### Accessing the Notebook

**Workspace Path:**
```
/Workspace/Users/YOUR_EMAIL/account_monitor/files/notebooks/contract_management_crud
```

### Quick Navigation

The notebook is organized into sections:

1. **Contract Management**
   - Read (view contracts)
   - Create (add new contracts)
   - Update (modify existing contracts)
   - Delete (remove contracts)

2. **Account Metadata Management**
   - Read (view account info)
   - Create (add new accounts)
   - Update (modify team assignments)
   - Delete (remove accounts)

3. **Utilities**
   - View contract-account joins
   - Summary statistics
   - Data validation
   - Export to CSV

### Common Operations

#### View All Contracts

```sql
SELECT
  contract_id,
  account_id,
  cloud_provider,
  start_date,
  end_date,
  total_value,
  status
FROM main.account_monitoring_dev.contracts
ORDER BY start_date DESC;
```

#### Add a New Contract

```sql
INSERT INTO main.account_monitoring_dev.contracts (
  contract_id, account_id, cloud_provider,
  start_date, end_date, total_value, currency,
  commitment_type, status, notes,
  created_at, updated_at
)
VALUES (
  'CONTRACT_2026_001',           -- Unique ID
  'your-account-id',             -- Your account
  'AWS',                         -- Cloud provider
  '2026-01-01',                  -- Start date
  '2027-01-01',                  -- End date
  10000.00,                      -- Total value
  'USD',                         -- Currency
  'SPEND',                       -- Type
  'ACTIVE',                      -- Status
  'Annual contract FY26',        -- Notes
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
```

#### Update Contract Status

```sql
UPDATE main.account_monitoring_dev.contracts
SET
  status = 'EXPIRED',
  updated_at = CURRENT_TIMESTAMP()
WHERE contract_id = 'CONTRACT_2026_001';
```

#### Update Contract Value

```sql
UPDATE main.account_monitoring_dev.contracts
SET
  total_value = 5000.00,
  updated_at = CURRENT_TIMESTAMP()
WHERE contract_id = '1694992';
```

#### Delete a Contract

```sql
-- ⚠️ WARNING: This permanently removes the contract
DELETE FROM main.account_monitoring_dev.contracts
WHERE contract_id = 'CONTRACT_2026_001';
```

#### Update Account Metadata

```sql
UPDATE main.account_monitoring_dev.account_metadata
SET
  customer_name = 'Your Company Name',
  business_unit_l0 = 'AMER',
  account_executive = 'John Doe',
  solutions_architect = 'Jane Smith',
  updated_at = CURRENT_TIMESTAMP()
WHERE account_id = 'your-account-id';
```

### Best Practices

✅ **DO:**
- Always update `updated_at` timestamp when modifying records
- Use descriptive contract IDs (e.g., `CONTRACT_2026_Q1`)
- Add notes to contracts for context
- Run data validation after bulk operations
- Back up data before large deletions

❌ **DON'T:**
- Don't use generic IDs like '1', '2', '3'
- Don't delete contracts that have historical data
- Don't modify `created_at` timestamps
- Don't skip the validation checks

### Data Validation

After making changes, run the validation function:

```python
# In the CRUD notebook
validate_data()
```

This checks for:
- Orphaned contracts (no account metadata)
- Invalid date ranges
- Duplicate contract IDs
- Missing required fields

---

## Dashboard & Burndown Charts

### Account Monitor Dashboard Notebook

**Path:** `/Workspace/Users/YOUR_EMAIL/account_monitor/files/notebooks/account_monitor_notebook`

This interactive notebook provides:
- **Cost Analysis** - Daily, weekly, monthly spending
- **Usage Trends** - DBU consumption over time
- **Contract Burndown** - Track consumption vs. total value
- **Top Consumers** - Identify highest-cost workspaces
- **Product Category Breakdown** - Costs by service type

### Key Visualizations

#### 1. Cost Over Time
Line chart showing daily costs with trend line.

```python
# The notebook automatically generates this
# Shows last 365 days of spending
```

#### 2. Contract Burndown Chart

**What it shows:**
- **Total Contract Value** (horizontal line)
- **Cumulative Spend** (rising line)
- **Projected End Date** (if spending continues at current rate)
- **Days Remaining** in contract

**How to interpret:**
- If cumulative spend line crosses total value before contract end date → **overspending**
- If line is below and parallel → **on track**
- If line is flat → **underutilizing**

**Example:**
```
Total Contract Value: $3,000
Current Spend: $1,200
Days Elapsed: 180 / 730 (25%)
Burn Rate: $6.67/day
Projected Total: $4,869 ⚠️ (162% of contract)
```

#### 3. Product Category Costs

Bar chart showing costs by:
- All Purpose Compute
- Jobs Compute
- SQL Warehouse
- Delta Live Tables
- Model Serving
- Vector Search
- Serverless

#### 4. Top Consumers

Table showing:
- Top workspaces by cost
- Top SKUs by usage
- Top users by consumption

### Refreshing the Dashboard

The dashboard reads from pre-aggregated tables that are refreshed by jobs.

**To get the latest data:**
1. Ensure the `account_monitor_daily_refresh` job ran successfully
2. Re-run all cells in the dashboard notebook
3. Or use **Run All** from the notebook menu

**Manual refresh:**
```sql
-- Trigger refresh of dashboard data
REFRESH TABLE main.account_monitoring_dev.dashboard_data;
REFRESH TABLE main.account_monitoring_dev.contract_burndown;
```

### Lakeview Dashboard

A visual dashboard built with Databricks Lakeview.

**Features:**
- Real-time cost metrics
- Interactive burndown charts
- Drill-down capabilities
- Exportable reports

**Accessing:**
1. Navigate to **Dashboards** in Databricks UI
2. Find "Account Monitor Dashboard"
3. Click to view

**Creating Your Own:**
See `docs/archive/CREATE_LAKEVIEW_DASHBOARD.md` for detailed instructions.

### What-If Analysis Page

The What-If Analysis page helps you understand contract optimization opportunities:

**Widgets:**

| Widget | Description |
|--------|-------------|
| **What-If Burndown Chart** | Multi-line chart comparing baseline vs extension scenarios |
| **Sweet Spot Summary** | Recommended scenario per contract |
| **Strategy & Savings Explained** | Dynamic business summary with live contract data |

**Strategy & Savings Explained Widget:**

This widget displays 6 lines of live scenario data:

| Line | Example Content |
|------|-----------------|
| 📋 CONTRACT | $35,000,000 commitment |
| 📅 CURRENT TERM | Feb 1, 2025 → Feb 28, 2027 (381 days remaining) |
| 📈 CONSUMED | $10,896,372 of $35,000,000 (31.1%) — $24,103,628 remaining |
| ⚠️ STATUS | EXTENDED — contract will NOT exhaust before end date |
| 💡 EXTENSION | Extend to 3yr (new end: Feb 1, 2028) for 40% discount |
| 💰 SAVINGS | $14,349,431 total savings with extension |

**Understanding the Status:**
- **EXTENDED**: Contract under-consumed — won't exhaust before end date
- **EARLY EXHAUSTION**: Will consume commitment before contract end
- **ON TRACK**: Consumption aligns well with contract timeline

---

## Consumption Forecasting (ML)

Version 1.7.0 introduces Prophet-based machine learning forecasting for contract consumption prediction.

### How It Works

The forecasting system uses Facebook Prophet to analyze historical daily spending patterns and predict future consumption. Key features:

- **Time Series Analysis**: Captures yearly, weekly, and monthly seasonality patterns
- **Confidence Intervals**: Provides p10 (optimistic), p50 (median), and p90 (conservative) predictions
- **Automatic Fallback**: Uses linear projection when insufficient data (<30 days)
- **MLflow Integration**: Tracks experiments and model versions

### Forecast Tables

Two new tables store forecasting data:

#### contract_forecast
Stores daily predictions and exhaustion dates.

| Column | Description |
|--------|-------------|
| contract_id | Contract identifier |
| forecast_date | Date of prediction |
| predicted_daily_cost | Prophet predicted daily cost |
| predicted_cumulative | Cumulative predicted cost |
| lower_bound | 10th percentile (optimistic) |
| upper_bound | 90th percentile (conservative) |
| exhaustion_date_p10 | Optimistic exhaustion date |
| exhaustion_date_p50 | Median exhaustion date |
| exhaustion_date_p90 | Conservative exhaustion date |
| days_to_exhaustion | Days until median exhaustion |
| model_version | "prophet" or "linear_fallback" |

#### forecast_model_registry
Tracks trained models and performance metrics.

| Column | Description |
|--------|-------------|
| model_id | Unique model identifier |
| contract_id | Contract this model is for |
| trained_at | Training timestamp |
| mape | Mean Absolute Percentage Error |
| rmse | Root Mean Square Error |
| mlflow_run_id | MLflow experiment run ID |
| is_active | Whether model is currently active |

### Jobs

Two jobs manage forecasting:

| Job | Schedule | Purpose |
|-----|----------|---------|
| **Weekly Training** | Sunday 3 AM UTC | Train Prophet models for all contracts |
| **Daily Inference** | Part of daily refresh | Generate forecasts using trained models |

### Running Forecasts Manually

**Train new models:**
```bash
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE
```

**Run inference only:**
```bash
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE
```

**Run the notebook interactively:**
1. Open `notebooks/consumption_forecaster.py`
2. Set widget parameters:
   - `mode`: "training", "inference", or "both"
   - `forecast_horizon_days`: 365 (default)
   - `confidence_interval`: 0.80 (default)
   - `min_training_days`: 30 (minimum days required)
3. Run all cells

### Interpreting Forecasts

#### Exhaustion Dates

The forecast provides three exhaustion date predictions:

- **p10 (Optimistic)**: 10% chance contract exhausts before this date
- **p50 (Median)**: 50% probability - most likely exhaustion date
- **p90 (Conservative)**: 90% chance contract exhausts before this date

**Example Interpretation:**
```
exhaustion_date_p10: 2026-08-15  (10% probability)
exhaustion_date_p50: 2026-10-01  (most likely)
exhaustion_date_p90: 2026-12-01  (90% probability)
```

This means there's:
- 10% chance the contract exhausts by August 15
- 50% chance by October 1
- 90% chance by December 1

#### Forecast Status

The enhanced burndown chart shows:
- **Blue line**: Historical actual spend
- **Green dashed line**: Forecasted median spend
- **Green shaded area**: 80% confidence band
- **Red line**: Contract limit
- **Orange vertical line**: Predicted exhaustion date (p50)

#### Model Quality Metrics

Check model quality in the model registry:

```sql
SELECT
  contract_id,
  ROUND(mape, 2) as mape_pct,
  ROUND(rmse, 2) as rmse_dollars,
  training_points,
  is_active
FROM main.account_monitoring_dev.forecast_model_registry
WHERE is_active = TRUE;
```

**MAPE Guidelines:**
- < 10%: Excellent accuracy
- 10-20%: Good accuracy
- 20-30%: Acceptable
- > 30%: Consider investigating data quality

### Viewing Forecasts

**SQL Query - Latest Forecast:**
```sql
SELECT * FROM main.account_monitoring_dev.contract_forecast_latest;
```

**SQL Query - Forecast Details with Contract Info:**
```sql
SELECT * FROM main.account_monitoring_dev.contract_forecast_details;
```

**Dashboard:**
The Account Monitor notebook (Section 9b) displays an enhanced burndown chart with forecast overlay when forecast data is available.

### Troubleshooting Forecasts

#### "No forecast data available"

**Cause:** Weekly training job hasn't run yet.

**Solution:**
```bash
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE
```

#### "Insufficient data" warning

**Cause:** Contract has fewer than 30 days of historical data.

**Solution:** The system automatically falls back to linear projection. Wait for more data to accumulate or reduce `min_training_days` parameter (not recommended for accuracy).

#### Poor forecast accuracy (high MAPE)

**Causes:**
- Irregular spending patterns
- Sudden changes in usage
- Too few data points

**Solutions:**
1. Check if spending patterns are highly irregular
2. Consider adjusting Prophet parameters in the notebook
3. Wait for more historical data

#### MLflow experiment not found

**Cause:** First time running or experiment was deleted.

**Solution:** The forecaster automatically creates the experiment on first run. Check MLflow UI at `/Shared/consumption_forecaster`.

---

## Troubleshooting

### Common Issues

#### Issue: "Table not found" error

**Solution:**
```bash
# Run the setup job again
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

#### Issue: "No data in dashboard"

**Causes:**
- Daily refresh job hasn't run yet
- No usage data in system.billing.usage

**Solution:**
```bash
# Check if system tables have data
SELECT COUNT(*) FROM system.billing.usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);

# Run refresh job manually
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE
```

#### Issue: "Cannot resolve salesforce_id" or other column errors

**Solution:**
This should be fixed in version 1.6.1. If you see this error:
```bash
# Drop and recreate tables
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

#### Issue: Job fails with "Warehouse not found"

**Solution:**
Update `databricks.yml` with correct warehouse ID:
```yaml
variables:
  warehouse_id: "your-actual-warehouse-id"
```

Find your warehouse ID:
```bash
databricks sql warehouses list --profile YOUR_PROFILE
```

### Getting Help

1. **Check Job Logs:**
   - Go to Workflows > Jobs > [Job Name] > Recent Runs
   - Click on failed run
   - Check task output for error messages

2. **Validate Configuration:**
   ```bash
   databricks bundle validate --profile YOUR_PROFILE
   ```

3. **Check Permissions:**
   Ensure you have:
   - USE CATALOG on `main` catalog
   - USE SCHEMA on `account_monitoring_dev` schema
   - SELECT on `system.billing.*` tables
   - CAN MANAGE on SQL Warehouse

4. **Review Logs:**
   - Notebook output cells for errors
   - Job run output for task failures
   - Warehouse query history

---

## Appendix

### Useful SQL Queries

**Check contract status:**
```sql
SELECT
  c.contract_id,
  c.status,
  c.total_value,
  DATEDIFF(c.end_date, CURRENT_DATE()) as days_remaining,
  SUM(d.actual_cost) as total_spent,
  (SUM(d.actual_cost) / c.total_value * 100) as percent_consumed
FROM main.account_monitoring_dev.contracts c
LEFT JOIN main.account_monitoring_dev.dashboard_data d
  ON c.account_id = d.account_id
WHERE c.status = 'ACTIVE'
GROUP BY c.contract_id, c.status, c.total_value, c.end_date;
```

**Find high-cost days:**
```sql
SELECT
  usage_date,
  SUM(actual_cost) as daily_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY usage_date
ORDER BY daily_cost DESC
LIMIT 10;
```

### File Structure

```
databricks_conso_reports/
├── databricks.yml              # DAB configuration
├── README.md                   # Project overview
├── docs/
│   ├── user-guide/
│   │   └── USER_GUIDE.md      # This guide
│   └── archive/               # Old summaries
├── notebooks/
│   ├── account_monitor_notebook.py    # Main dashboard
│   ├── consumption_forecaster.py      # Prophet ML forecasting
│   ├── contract_management_crud.py    # CRUD operations
│   └── post_deployment_validation.py  # Validation checks
├── sql/
│   ├── setup_schema.sql               # Schema + forecast tables
│   ├── create_forecast_schema.sql     # Forecast tables only
│   ├── build_forecast_features.sql    # Feature engineering
│   ├── insert_sample_data.sql
│   └── refresh_*.sql
└── resources/
    └── jobs.yml               # Job definitions (incl. weekly training)
```

### Version History

- **1.12.0** (2026-02-11) - Enhanced What-If Analysis page
  - Simplified dashboard with focused widgets
  - New Strategy & Savings Explained widget with live contract data
  - Shows contract term, consumption %, extension opportunities
- **1.11.0** (2026-02-08) - Administrator Operations Guide
- **1.10.0** (2026-02-07) - What-If discount simulation
- **1.7.0** (2026-02-05) - Added Prophet-based ML consumption forecasting
  - New tables: contract_forecast, forecast_model_registry
  - Weekly training job for Prophet models
  - Enhanced burndown chart with forecast overlay
  - Confidence intervals (p10/p50/p90) for exhaustion dates
  - MLflow experiment tracking
- **1.6.1** (2026-02-04) - Fixed salesforce_id errors, added notes column
- **1.5.x** - Initial stable release

---

## Quick Reference Card

| Task | Command/Action |
|------|----------------|
| Deploy | `databricks bundle deploy --profile PROFILE` |
| Run Setup | `databricks bundle run account_monitor_setup --profile PROFILE` |
| View Jobs | Navigate to Workflows > Jobs in UI |
| Add Contract | Use Contract Management CRUD notebook |
| View Dashboard | Open account_monitor_notebook |
| Refresh Data | Run `account_monitor_daily_refresh` job |
| Validate Data | Run validation checks in CRUD notebook |

---

**Need Help?** Check the troubleshooting section or review job logs in the Databricks UI.
