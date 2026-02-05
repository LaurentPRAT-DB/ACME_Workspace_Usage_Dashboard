# Databricks Account Monitor

**Track consumption, forecast contract exhaustion, and manage Databricks spending**

[![Databricks](https://img.shields.io/badge/Databricks-Asset_Bundle-FF3621?logo=databricks)](https://databricks.com)
[![Version](https://img.shields.io/badge/Version-1.8.0-green)](CHANGELOG.md)

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

## Quick Start - First Install

Complete setup in 5 steps. After this, you'll have a working dashboard with ML forecasts.

```mermaid
flowchart LR
    subgraph step1["1️⃣ Configure"]
        config["Edit contracts.yml"]
    end

    subgraph step2["2️⃣ Deploy"]
        deploy["databricks bundle deploy"]
    end

    subgraph step3["3️⃣ Setup"]
        setup["Run setup job"]
    end

    subgraph step4["4️⃣ Load Data"]
        refresh["Run daily refresh"]
    end

    subgraph step5["5️⃣ Train Model"]
        train["Run weekly training"]
    end

    subgraph done["✅ Ready"]
        dashboard["Open Dashboard"]
    end

    step1 --> step2 --> step3 --> step4 --> step5 --> done
```

### Step 1: Configure Your Contracts

Edit `config/contracts.yml` with your contract details:

```yaml
account_metadata:
  account_id: "auto"                    # Auto-detect from billing
  customer_name: "Your Organization"

contracts:
  - contract_id: "MY-CONTRACT-001"
    cloud_provider: "auto"              # Auto-detect (AWS/Azure/GCP)
    start_date: "auto"                  # Or specific date: "2025-01-01"
    end_date: "auto"                    # Or specific date: "2025-12-31"
    total_value: 50000.00               # Your contract commitment
    currency: "USD"
    commitment_type: "SPEND"
    status: "ACTIVE"
    notes: "Annual contract"
```

### Step 2: Deploy the Bundle

```bash
# Set your profile (replace with your actual profile name)
export PROFILE="YOUR_PROFILE"

# Deploy all resources to Databricks
databricks bundle deploy --profile $PROFILE
```

### Step 3: Run Initial Setup

This creates tables and loads your contracts from the config file:

```bash
databricks bundle run account_monitor_setup --profile $PROFILE
```

**Expected output:** Schema created, contracts loaded from `contracts.yml`

### Step 4: Load Historical Data

Run the daily refresh to populate burndown data from `system.billing.usage`:

```bash
databricks bundle run account_monitor_daily_refresh --profile $PROFILE
```

**Expected output:** `dashboard_data` and `contract_burndown` tables populated

### Step 5: Train the Forecast Model

Run the weekly training job to generate ML predictions:

```bash
databricks bundle run account_monitor_weekly_training --profile $PROFILE
```

**Expected output:** Prophet model trained, `contract_forecast` table populated with exhaustion dates

### Step 6: View the Dashboard

1. Open your Databricks workspace
2. Navigate to **Workspace** > **Users** > **your-email** > **account_monitor** > **files** > **notebooks**
3. Open **account_monitor_notebook**
4. Click **Run All**

You should see:
- Contract summary with status
- Daily cost trends
- **Burndown chart with ML forecast line**
- Predicted contract exhaustion date

---

## Architecture

```mermaid
flowchart TB
    subgraph sources["🗂️ Data Sources"]
        usage[("system.billing.usage")]
        prices[("system.billing.list_prices")]
    end

    subgraph daily["⚙️ Daily Refresh Job"]
        direction LR
        join["Join & Enrich Data"]
    end

    subgraph catalog["📦 Unity Catalog Tables"]
        contracts[("contracts")]
        burndown[("contract_burndown")]
        dashboard_data[("dashboard_data")]
    end

    subgraph weekly["🤖 Weekly Training Job"]
        prophet["Prophet ML Model"]
    end

    subgraph forecast_table["📊 Forecast Output"]
        forecast[("contract_forecast")]
    end

    subgraph output["📈 Dashboard"]
        notebook["Account Monitor Notebook"]
    end

    usage --> daily
    prices --> daily
    daily --> burndown
    daily --> dashboard_data

    burndown --> weekly
    contracts --> weekly
    weekly --> forecast_table

    contracts --> notebook
    burndown --> notebook
    forecast --> notebook
    dashboard_data --> notebook
```

---

## Data Model

```mermaid
erDiagram
    CONTRACTS ||--o{ CONTRACT_BURNDOWN : "tracks daily"
    CONTRACTS ||--o{ CONTRACT_FORECAST : "predicts"
    CONTRACTS ||--o{ DASHBOARD_DATA : "enriches"

    CONTRACTS {
        string contract_id PK
        string account_id
        string cloud_provider
        date start_date
        date end_date
        decimal total_value
        string currency
        string commitment_type
        string status
        string notes
    }

    CONTRACT_BURNDOWN {
        string contract_id FK
        date usage_date
        decimal daily_cost
        decimal cumulative_cost
        decimal remaining_budget
        decimal burn_rate_7d
    }

    CONTRACT_FORECAST {
        string contract_id FK
        date forecast_date
        decimal predicted_cumulative
        date exhaustion_date_p10
        date exhaustion_date_p50
        date exhaustion_date_p90
        string model_version
    }

    DASHBOARD_DATA {
        date usage_date
        string account_id FK
        string workspace_id
        string sku_name
        decimal usage_quantity
        decimal actual_cost
    }
```

### System Tables (Read-Only)

| Table | Description |
|-------|-------------|
| `system.billing.usage` | Raw usage records (DBUs, dates, workspaces, SKUs) |
| `system.billing.list_prices` | Pricing information per SKU and cloud |

---

## Job Schedule

```mermaid
gantt
    title Automated Job Schedule
    dateFormat HH:mm
    axisFormat %H:%M

    section Daily
    Daily Refresh (2 AM)     :daily, 02:00, 60min

    section Weekly
    Training - Sun 3 AM      :train, 03:00, 120min
    Review - Mon 8 AM        :review, 08:00, 60min

    section Monthly
    Summary - 1st 6 AM       :monthly, 06:00, 60min
```

| Job | Schedule | Purpose | Manual Command |
|-----|----------|---------|----------------|
| **Daily Refresh** | 2:00 AM UTC | Update consumption data | `databricks bundle run account_monitor_daily_refresh` |
| **Weekly Training** | Sunday 3:00 AM | Retrain Prophet models | `databricks bundle run account_monitor_weekly_training` |
| **Weekly Review** | Monday 8:00 AM | Contract analysis | `databricks bundle run account_monitor_weekly_review` |
| **Monthly Summary** | 1st @ 6:00 AM | Archive & reports | `databricks bundle run account_monitor_monthly_summary` |

---

## Setup

### Prerequisites

- Databricks workspace with **Unity Catalog** enabled
- Access to **system.billing** tables (account admin or granted access)
- **Databricks CLI** installed and configured
- A **SQL Warehouse** (serverless recommended)

### Step 1: Configure the Bundle

Edit `databricks.yml` with your workspace settings:

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

### Step 2: Configure Your Contracts

Edit `config/contracts.yml` to define your organization and contracts:

```yaml
# config/contracts.yml
account_metadata:
  account_id: "auto"                    # Auto-detect from billing data
  customer_name: "Your Organization"
  business_unit_l0: "AMER"
  account_executive: "John Doe"
  solutions_architect: "Jane Smith"
  region: "US-WEST"
  industry: "Technology"

contracts:
  - contract_id: "CONTRACT-2026-001"
    cloud_provider: "auto"              # Auto-detect (AWS/Azure/GCP)
    start_date: "2025-07-01"            # Or "auto" for 1 year ago
    end_date: "2026-06-30"              # Or "auto" for 1 year from now
    total_value: 50000.00
    currency: "USD"
    commitment_type: "SPEND"
    status: "ACTIVE"
    notes: "Annual enterprise contract"

  # Add more contracts as needed:
  - contract_id: "CONTRACT-2026-002"
    cloud_provider: "AWS"
    start_date: "2026-01-01"
    end_date: "2026-12-31"
    total_value: 100000.00
    currency: "USD"
    commitment_type: "DBU"
    status: "PENDING"
    notes: "DBU commitment for next year"
```

**Auto-detection:**
- `account_id: "auto"` → Reads from `system.billing.usage`
- `cloud_provider: "auto"` → Detects from your actual usage data
- `start_date: "auto"` → Sets to 1 year ago
- `end_date: "auto"` → Sets to 1 year from now

### Step 3: Deploy and Setup

```bash
# Authenticate
databricks auth login --host https://your-workspace.cloud.databricks.com --profile YOUR_PROFILE

# Deploy all resources
databricks bundle deploy --profile YOUR_PROFILE

# Run setup (creates tables + loads contracts from config)
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

### Updating Contracts Later

To add or modify contracts after initial setup:

1. Edit `config/contracts.yml`
2. Redeploy: `databricks bundle deploy --profile YOUR_PROFILE`
3. Re-run setup: `databricks bundle run account_monitor_setup --profile YOUR_PROFILE`

Or use the **Contract Management CRUD** notebook for manual changes

---

## Visualizations

### Contract Burndown Chart

The burndown chart shows cumulative spending over time compared to the contract limit:

![Contract Burndown with ML Forecast](docs/user-guide/contract_burndown_predict.png)

**Chart Legend:**
| Element | Description |
|---------|-------------|
| **Historical Consumption** (blue dots) | Actual cumulative spending to date |
| **ML Forecast (Prophet)** (cyan line) | Prophet-predicted future spending |
| **Contract Commitment** (dashed line) | Contract limit amount |
| **Intersection Point** | Where forecast crosses the limit = **predicted exhaustion date** |

### Exhaustion Prediction

```mermaid
flowchart LR
    subgraph current["📊 Current State"]
        spent["$30,000 Spent"]
        rate["$166/day avg"]
    end

    subgraph prediction["🔮 ML Prediction"]
        exhaust["Exhaustion: Jan 30, 2026"]
        conf["Confidence: 80%"]
    end

    subgraph action["⚠️ Action Required"]
        alert["120 days remaining"]
    end

    current --> prediction --> action
```

**Forecast Summary Output:**
```
============================================================
FORECAST SUMMARY
============================================================
Contract ID: CONTRACT-2026-001
Contract Value: $50,000.00
Current Spend: $30,000.00
Model: prophet
Predicted Exhaustion Date: 2026-01-30
Days Remaining: 120
============================================================
```

---

## Verifying Data Freshness

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

```mermaid
flowchart TD
    A[Issue?] --> B{No data in charts?}
    B -->|Yes| C[Run daily refresh job]
    B -->|No| D{Forecast not showing?}
    D -->|Yes| E[Run weekly training job]
    D -->|No| F{Jobs failing?}
    F -->|Yes| G[Check warehouse status]
    F -->|No| H[Check Unity Catalog permissions]

    C --> I[databricks bundle run account_monitor_daily_refresh]
    E --> J[databricks bundle run account_monitor_weekly_training]
    G --> K[Start SQL Warehouse in UI]
    H --> L[Grant SELECT on system.billing tables]
```

### Common Commands

```bash
# Check system tables have data
databricks sql -e "SELECT COUNT(*) FROM system.billing.usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)"

# Run the daily refresh
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE

# Run forecast training
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE

# Check job run status
databricks runs get --run-id <RUN_ID> --profile YOUR_PROFILE
```

---

## File Structure

```mermaid
flowchart LR
    subgraph root["📁 Root"]
        readme["README.md"]
        dbconfig["databricks.yml"]
    end

    subgraph configdir["📝 config/"]
        contracts["contracts.yml"]
    end

    subgraph notebooks["📓 notebooks/"]
        monitor["account_monitor_notebook.py"]
        crud["contract_management_crud.py"]
        forecast["consumption_forecaster.py"]
        setupnb["setup_contracts.py"]
    end

    subgraph sql["🗃️ sql/"]
        setup["setup_schema.sql"]
        refresh["refresh_*.sql"]
    end

    subgraph resources["⚙️ resources/"]
        jobs["jobs.yml"]
    end

    root --> configdir
    root --> notebooks
    root --> sql
    root --> resources
    configdir -->|"loaded by"| setupnb
```

```
databricks_conso_reports/
├── databricks.yml              # Bundle configuration
├── README.md                   # This file
├── config/
│   └── contracts.yml           # 📝 YOUR CONTRACT CONFIGURATION
├── notebooks/
│   ├── account_monitor_notebook.py    # Main dashboard
│   ├── contract_management_crud.py    # CRUD operations
│   ├── consumption_forecaster.py      # ML forecasting
│   ├── setup_contracts.py             # Config loader
│   └── post_deployment_validation.py  # Setup verification
├── sql/
│   ├── setup_schema.sql               # Create all tables
│   ├── refresh_dashboard_data.sql     # Daily data refresh
│   ├── refresh_contract_burndown.sql  # Burndown calculation
│   └── build_forecast_features.sql    # ML feature prep
├── resources/
│   └── jobs.yml                       # Job definitions
└── docs/
    └── user-guide/
        └── USER_GUIDE.md              # Detailed documentation
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.8.0** | 2026-02-05 | Added Quick Start first-install guide with step-by-step workflow |
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
