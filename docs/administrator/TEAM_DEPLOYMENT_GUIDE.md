# Databricks Account Monitor - Team Deployment Guide

**Complete guide for teams deploying to their own Databricks environment**

**Version:** 2.0
**Last Updated:** 2026-01-29
**Deployment Time:** 1.5-3 hours

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Contract Data Setup](#contract-data-setup)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Overview

### What This Solution Provides

The Databricks Account Monitor is a complete cost and usage tracking solution that:

- **Tracks consumption** across all workspaces using Databricks System Tables
- **Monitors contract burndown** against committed spend
- **Provides Lakeview dashboards** with 17 pre-built queries
- **Automates data refresh** with scheduled jobs
- **Validates deployment** with comprehensive tests

### Key Features

✅ **Contract Management** - Track multiple contracts with burndown visualization
✅ **Cost Analytics** - Break down costs by workspace, SKU, product category
✅ **Usage Trends** - Daily, weekly, and monthly consumption patterns
✅ **Automated Refresh** - Scheduled jobs for data updates
✅ **Multi-Account Support** - Handle multiple accounts and business units

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Databricks Workspace                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────┐         ┌──────────────────┐                    │
│  │  System Tables    │         │  Unity Catalog   │                    │
│  │  (Read-Only)      │         │  (Your Data)     │                    │
│  ├───────────────────┤         ├──────────────────┤                    │
│  │ billing.usage     │────────>│ contracts        │                    │
│  │ billing.list_     │   JOIN  │ account_metadata │                    │
│  │   prices          │         │ dashboard_data   │                    │
│  └───────────────────┘         │ daily_summary    │                    │
│                                 │ contract_        │                    │
│                                 │   burndown       │                    │
│                                 └──────────────────┘                    │
│                                          │                               │
│                                          v                               │
│                                 ┌──────────────────┐                    │
│                                 │  Scheduled Jobs  │                    │
│                                 ├──────────────────┤                    │
│                                 │ Daily Refresh    │                    │
│                                 │ Weekly Review    │                    │
│                                 │ Monthly Summary  │                    │
│                                 └──────────────────┘                    │
│                                          │                               │
│                                          v                               │
│  ┌─────────────────────────────────────────────────────┐               │
│  │               Lakeview Dashboards                    │               │
│  ├─────────────────────────────────────────────────────┤               │
│  │  • Contract Burndown (8 visualizations)             │               │
│  │  • Account Overview (5 visualizations)              │               │
│  │  • Usage Analytics (4 visualizations)               │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
System Tables              Unity Catalog              Dashboards
─────────────             ──────────────             ──────────

usage records  ──┐
                 ├──> refresh_dashboard_data  ──>  dashboard_data  ──>  Lakeview
list_prices   ──┘        (SQL job)                                      Queries
                                                                        (17 queries)
                                                                           │
contracts     ────────>  refresh_contract_burndown  contract_burndown ────┤
                         (SQL job)                                         │
                                                                           v
account_metadata  ──────────────────────────────────────────────────>  Visualizations
```

### Components Deployed

| Component | Type | Purpose |
|-----------|------|---------|
| **Notebooks** | `.py` / `.sql` | Analytics and query library |
| **SQL Scripts** | `.sql` | Schema setup and data refresh |
| **Jobs** | Scheduled | Automated data updates |
| **Tables** | Unity Catalog | Contract and cost data storage |

---

## Prerequisites

### 1. Databricks Environment

✅ **Workspace Requirements:**
- Databricks workspace (AWS, Azure, or GCP)
- Unity Catalog enabled
- System Tables enabled (for `system.billing.usage` and `system.billing.list_prices`)

✅ **User Permissions:**
- `CREATE SCHEMA` on Unity Catalog
- `CREATE TABLE` on Unity Catalog
- `CREATE JOB` on workspace
- `READ` access to `system.billing.usage` and `system.billing.list_prices`
- `USE CATALOG` and `USE SCHEMA` permissions

✅ **Compute Resources:**
- SQL Warehouse (Serverless or Provisioned)
- Or: Cluster with Databricks Runtime 13.0+

### 2. Local Development Environment

```bash
# Required tools
✅ Git
✅ Databricks CLI (v0.200.0+)
✅ Python 3.8+ (for validation scripts)

# Install Databricks CLI
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Verify installation
databricks --version
```

### 3. Authentication Setup

```bash
# Option 1: OAuth (Recommended for interactive use)
databricks auth login --host <workspace-url>

# Option 2: Personal Access Token
# Create .databrickscfg file
cat > ~/.databrickscfg << EOF
[DEFAULT]
host = <workspace-url>
token = <your-personal-access-token>
EOF

# Test authentication
databricks current-user me
```

---

## Step-by-Step Deployment

### Step 1: Clone the Repository ⏱️ 2 minutes

```bash
# Clone from GitHub
git clone https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard.git
cd ACME_Workspace_Usage_Dashboard

# Or: Download and extract ZIP
# unzip ACME_Workspace_Usage_Dashboard.zip
# cd ACME_Workspace_Usage_Dashboard
```

**✅ Verification:**
```bash
ls -la
# Should see: databricks.yml, notebooks/, sql/, docs/
```

---

### Step 2: Configure Databricks Asset Bundle ⏱️ 5 minutes

Edit `databricks.yml` to customize for your environment:

```yaml
# databricks.yml

bundle:
  name: account_monitor

workspace:
  profile: DEFAULT  # ← Change to your CLI profile name

variables:
  catalog:
    default: main  # ← Change to your catalog name

  schema:
    default: account_monitoring  # ← Change to your schema name

  warehouse_id:
    default: "YOUR_WAREHOUSE_ID"  # ← Get from workspace SQL Warehouses page

targets:
  dev:
    mode: development
    default: true
    variables:
      schema: account_monitoring_dev  # Dev schema name

  prod:
    mode: production
    variables:
      schema: account_monitoring  # Prod schema name
```

**How to find your Warehouse ID:**
```bash
# List available warehouses
databricks warehouses list --output json | jq '.[] | {id, name}'

# Or: Get from Databricks UI
# SQL Warehouses → Click warehouse → Copy ID from URL
# URL: /sql/warehouses/<WAREHOUSE_ID>
```

**✅ Verification:**
```bash
# Test CLI profile
databricks current-user me

# Test warehouse access
databricks warehouses get <YOUR_WAREHOUSE_ID>
```

---

### Step 3: Validate Bundle Configuration ⏱️ 1 minute

```bash
# Check for syntax errors and validate configuration
databricks bundle validate -t dev

# Expected output:
# ✓ Configuration is valid
```

**Common validation errors:**

| Error | Solution |
|-------|----------|
| ❌ Invalid warehouse_id | Run `databricks warehouses list` to find valid ID |
| ❌ Catalog not found | Check Unity Catalog name in workspace |
| ❌ Authentication error | Run `databricks auth login` again |

---

### Step 4: Deploy to Development Environment ⏱️ 3 minutes

```bash
# Deploy to dev environment (creates all resources)
databricks bundle deploy -t dev

# Expected output:
# Uploading bundle files to /Workspace/Users/<your-email>/account_monitor/files...
# Deploying resources...
# ✓ Notebooks synced
# ✓ SQL scripts uploaded
# ✓ Jobs created
# Deployment complete!
```

**What gets deployed:**
```
/Workspace/Users/<your-email>/account_monitor/
├── files/
│   ├── notebooks/
│   │   ├── account_monitor_notebook.py
│   │   ├── post_deployment_validation.py
│   │   ├── lakeview_dashboard_queries.sql
│   │   └── verify_contract_burndown.sql
│   ├── sql/
│   │   ├── setup_schema.sql
│   │   ├── refresh_dashboard_data.sql
│   │   ├── refresh_contract_burndown.sql
│   │   ├── check_data_freshness.sql
│   │   └── optimize_tables.sql
│   └── docs/
│       └── (all documentation)
└── state.json  # Deployment state
```

**✅ Verification:**
```bash
# Verify notebooks deployed
databricks workspace list /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/

# Expected: List of 4 notebooks
```

---

### Step 5: Create Schema and Tables ⏱️ 5 minutes

**Option A: Using Databricks SQL Editor (Recommended)**

1. Open Databricks workspace
2. Navigate to **SQL Editor**
3. Select your SQL Warehouse
4. Copy and paste contents of `sql/setup_schema.sql`
5. Click **Run**
6. Verify tables created:

```sql
SHOW TABLES IN main.account_monitoring_dev;

-- Expected output:
-- contracts
-- account_metadata
-- dashboard_data
-- daily_summary
-- contract_burndown
```

**Option B: Using Databricks CLI**

```bash
# Get your warehouse ID
WAREHOUSE_ID=$(databricks warehouses list --output json | jq -r '.[0].id')

# Run setup script
cat sql/setup_schema.sql | databricks sql query \
  -w $WAREHOUSE_ID \
  --query "$(cat sql/setup_schema.sql)"
```

**✅ Verification:**
```sql
-- Count tables created
SELECT COUNT(*) as table_count
FROM main.information_schema.tables
WHERE table_schema = 'account_monitoring_dev';

-- Expected: 5 tables
```

---

### Step 6: Verify System Tables Access ⏱️ 3 minutes

**Test system tables connectivity:**

```sql
-- In Databricks SQL Editor or notebook

-- Test 1: Access system.billing.usage
SELECT COUNT(*) as row_count,
       MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);

-- ✅ Expected: row_count > 0, latest_date within last 2 days

-- Test 2: Access system.billing.list_prices
SELECT COUNT(*) as price_count,
       COUNT(DISTINCT sku_name) as unique_skus
FROM system.billing.list_prices;

-- ✅ Expected: price_count > 0, unique_skus > 10

-- Test 3: Cost calculation (JOIN test)
SELECT u.cloud,
       SUM(u.usage_quantity) as total_dbu,
       SUM(u.usage_quantity * CAST(lp.pricing.default AS DECIMAL(20,10))) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 7)
GROUP BY u.cloud;

-- ✅ Expected: total_cost > 0 for each cloud provider
```

**If any test fails:**
- ❌ Access denied → Contact Databricks admin to enable System Tables
- ❌ Table not found → System Tables not enabled for your workspace
- ❌ Cost is NULL → Check pricing join conditions

---

### Step 7: Run Post-Deployment Validation ⏱️ 5 minutes

**In Databricks Workspace:**

1. Navigate to `/Workspace/Users/<your-email>/account_monitor/files/notebooks/`
2. Open `post_deployment_validation.py`
3. Attach to SQL Warehouse
4. Click **Run All**

**Expected validation results:**
```
✅ Test 1: System Tables Access - PASSED
✅ Test 2: Unity Catalog Schema - PASSED
✅ Test 3: Contracts Table - PASSED
✅ Test 4: Account Metadata Table - PASSED
✅ Test 5: Dashboard Data Table - PASSED
✅ Test 6: Cost Calculation - PASSED
✅ Test 7: Date Range Check - PASSED
✅ Test 8: Cloud Provider Coverage - PASSED
✅ Test 9: Data Freshness - WARNING (no data yet - expected)
✅ Test 10: Jobs Deployed - PASSED

Summary: 9/10 tests passed (1 warning)
```

---

## Contract Data Setup

### Understanding Contract Tables

⚠️ **IMPORTANT:** Contract data is **YOUR DATA** that you must provide.

The solution provides the schema and calculations, but you populate the actual contract details.

### Contract Table Schema

```sql
-- main.account_monitoring_dev.contracts
CREATE TABLE contracts (
  contract_id STRING NOT NULL,           -- Unique ID (e.g., "CONTRACT-2026-001")
  account_id STRING NOT NULL,            -- Your Databricks account ID
  cloud_provider STRING NOT NULL,        -- "aws", "azure", or "gcp"
  start_date DATE NOT NULL,              -- Contract start date
  end_date DATE NOT NULL,                -- Contract end date
  total_value DECIMAL(18,2) NOT NULL,    -- Total commitment (e.g., 100000.00)
  currency STRING,                       -- "USD", "EUR", etc.
  commitment_type STRING,                -- "SPEND" or "DBU"
  status STRING,                         -- "ACTIVE", "EXPIRED", "PENDING"
  notes STRING,                          -- Optional notes
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Step 1: Gather Your Contract Information ⏱️ 15 minutes

**Required Information:**

1. **Contract ID** - Your internal contract reference number
2. **Account ID** - Your Databricks account ID
   ```bash
   # Get from CLI
   databricks account list --output json | jq '.[].account_id'

   # Or from workspace URL
   # https://<account>.cloud.databricks.com
   ```

3. **Cloud Provider** - Where contract applies (aws/azure/gcp)
4. **Dates** - Start and end dates of contract period
5. **Total Value** - Committed spend amount
6. **Commitment Type** - SPEND (dollar commitment) or DBU (unit commitment)

### Step 2: Insert Contract Data ⏱️ 5 minutes

**Example: Single Contract**

```sql
-- Insert your first contract
INSERT INTO main.account_monitoring_dev.contracts VALUES (
  'CONTRACT-2026-001',                    -- contract_id
  '<YOUR_ACCOUNT_ID>',                    -- account_id (from step 1)
  'aws',                                  -- cloud_provider
  DATE('2026-01-01'),                     -- start_date
  DATE('2026-12-31'),                     -- end_date
  100000.00,                              -- total_value (e.g., $100,000)
  'USD',                                  -- currency
  'SPEND',                                -- commitment_type
  'ACTIVE',                               -- status
  'Annual enterprise commitment',         -- notes
  CURRENT_TIMESTAMP(),                    -- created_at
  CURRENT_TIMESTAMP()                     -- updated_at
);

-- ✅ Verify insertion
SELECT * FROM main.account_monitoring_dev.contracts;
```

**Example: Multiple Contracts**

```sql
-- Insert multiple contracts at once
INSERT INTO main.account_monitoring_dev.contracts VALUES
  ('CONTRACT-AWS-2026', '<YOUR_ACCOUNT_ID>', 'aws',
   DATE('2026-01-01'), DATE('2026-12-31'), 150000.00,
   'USD', 'SPEND', 'ACTIVE', 'AWS annual commitment',
   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

  ('CONTRACT-AZURE-2026', '<YOUR_ACCOUNT_ID>', 'azure',
   DATE('2026-01-01'), DATE('2026-12-31'), 75000.00,
   'USD', 'SPEND', 'ACTIVE', 'Azure annual commitment',
   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),

  ('CONTRACT-GCP-2025', '<YOUR_ACCOUNT_ID>', 'gcp',
   DATE('2025-07-01'), DATE('2026-06-30'), 50000.00,
   'USD', 'SPEND', 'ACTIVE', 'GCP mid-year commitment',
   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
```

### Step 3: Add Account Metadata ⏱️ 5 minutes

```sql
-- Insert your organization's metadata
INSERT INTO main.account_monitoring_dev.account_metadata VALUES (
  '<YOUR_ACCOUNT_ID>',                    -- account_id
  'Your Company Name',                    -- customer_name
  '<SALESFORCE_ACCOUNT_ID>',              -- salesforce_id (if applicable)
  'North America',                        -- business_unit_l0
  'US West',                              -- business_unit_l1
  'Engineering',                          -- business_unit_l2
  'Data Platform',                        -- business_unit_l3
  'Jane Doe',                             -- account_executive
  'John Smith',                           -- solutions_architect
  'Alice Johnson',                        -- delivery_solutions_architect
  'US-West',                              -- region
  'Technology',                           -- industry
  CURRENT_TIMESTAMP(),                    -- created_at
  CURRENT_TIMESTAMP()                     -- updated_at
);

-- ✅ Verify insertion
SELECT * FROM main.account_monitoring_dev.account_metadata;
```

### Step 4: Run Data Refresh Jobs ⏱️ 10 minutes

**Option A: Using Databricks UI**

1. Navigate to **Workflows** → **Jobs**
2. Find "account_monitor_daily_refresh"
3. Click **Run now**
4. Monitor execution status

**Option B: Using SQL Scripts Directly**

```sql
-- Step 1: Refresh dashboard data (aggregates usage with costs)
-- Copy and run: sql/refresh_dashboard_data.sql

-- Step 2: Refresh contract burndown (calculates consumption)
-- Copy and run: sql/refresh_contract_burndown.sql

-- Step 3: Verify data populated
SELECT COUNT(*) as rows,
       MIN(usage_date) as earliest,
       MAX(usage_date) as latest
FROM main.account_monitoring_dev.dashboard_data;
-- ✅ Expected: rows > 0, latest date recent

SELECT COUNT(*) as rows,
       MIN(usage_date) as earliest,
       MAX(usage_date) as latest
FROM main.account_monitoring_dev.contract_burndown;
-- ✅ Expected: rows > 0, date range covers contract period
```

**✅ Verification:**
```sql
-- Check contract burndown summary
SELECT * FROM main.account_monitoring_dev.contract_burndown_summary;

-- Expected columns populated:
-- - consumed_pct
-- - pace_status (ON PACE, ABOVE PACE, etc.)
-- - days_remaining
-- - projected_end_date
```

---

## Testing & Validation

### Test Suite Overview

The solution includes comprehensive validation tests:

| Test # | Name | Validates |
|--------|------|-----------|
| 1 | System Tables Access | Can read `system.billing.usage` and `list_prices` |
| 2 | Unity Catalog Schema | Schema `account_monitoring_dev` exists |
| 3 | Contracts Table | Contracts table exists and has data |
| 4 | Account Metadata | Metadata table exists and has data |
| 5 | Dashboard Data | Dashboard data table populated |
| 6 | Cost Calculation | Pricing JOIN works correctly |
| 7 | Date Range | Data covers expected time range |
| 8 | Cloud Coverage | All cloud providers represented |
| 9 | Data Freshness | Data within last 2 days |
| 10 | Jobs Deployed | Scheduled jobs exist |
| 11 | Contract Burndown | Burndown calculations work |

### Running All Tests ⏱️ 5 minutes

**In workspace:**
1. Open `notebooks/post_deployment_validation.py`
2. Click **Run All**
3. Review results

**Expected outcome:**
```
✅ 11/11 tests passed
   or
✅ 10/11 tests passed (1 warning acceptable if data is fresh)
```

### Individual Test Examples

```sql
-- Test: System Tables Access
SELECT COUNT(*) FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);
-- ✅ Expected: > 0

-- Test: Cost Calculation
SELECT
  SUM(u.usage_quantity * CAST(lp.pricing.default AS DECIMAL(20,10))) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 7);
-- ✅ Expected: > 0

-- Test: Contract Burndown
SELECT * FROM main.account_monitoring_dev.contract_burndown_summary;
-- ✅ Expected: 1+ rows with pace_status populated
```

### Success Criteria

✅ **All tests pass** in post_deployment_validation
✅ **Contract data** inserted and visible
✅ **Dashboard data table** populated with last 7+ days
✅ **Contract burndown** table shows cumulative costs
✅ **Jobs** are scheduled and can run successfully
✅ **Lakeview queries** return data (all 17 queries)

---

## Troubleshooting

### Issue 1: System Tables Access Denied

**Symptoms:**
```
Error: Cannot access system.billing.usage
Error: PERMISSION_DENIED
```

**Solutions:**
1. Check if System Tables are enabled in workspace
2. Contact your Databricks account admin
3. Verify you have necessary permissions (Account Admin or System Tables viewer)

**Workaround:**
If System Tables aren't available, integrate with cloud provider billing APIs as alternative.

---

### Issue 2: Cost Calculation Returns NULL

**Symptoms:**
```sql
SELECT SUM(cost) FROM dashboard_data;
-- Returns: NULL
```

**Solutions:**
```sql
-- Check pricing data exists
SELECT COUNT(*) FROM system.billing.list_prices;
-- Should return > 0

-- Verify JOIN conditions
SELECT
  u.sku_name,
  COUNT(*) as usage_records,
  SUM(CASE WHEN lp.sku_name IS NOT NULL THEN 1 ELSE 0 END) as matched_prices
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 7)
GROUP BY u.sku_name
HAVING matched_prices = 0;
-- Should return 0 rows (all SKUs should match)
```

---

### Issue 3: Contract Burndown Shows No Data

**Symptoms:**
```sql
SELECT * FROM contract_burndown;
-- Returns: 0 rows
```

**Solutions:**
```sql
-- Step 1: Check if contracts exist
SELECT * FROM main.account_monitoring_dev.contracts;
-- If empty: Insert contract data (see Contract Data Setup)

-- Step 2: Check if dashboard_data has records
SELECT COUNT(*), MIN(usage_date), MAX(usage_date)
FROM main.account_monitoring_dev.dashboard_data;
-- If empty: Run refresh_dashboard_data.sql first

-- Step 3: Run contract burndown refresh manually
-- Execute: sql/refresh_contract_burndown.sql

-- Step 4: Check date ranges align
SELECT
  c.contract_id,
  c.start_date,
  c.end_date,
  MIN(d.usage_date) as earliest_usage,
  MAX(d.usage_date) as latest_usage
FROM main.account_monitoring_dev.contracts c
LEFT JOIN main.account_monitoring_dev.dashboard_data d
  ON d.usage_date BETWEEN c.start_date AND c.end_date
GROUP BY c.contract_id, c.start_date, c.end_date;
-- Verify overlapping date ranges
```

---

### Getting Help

**Internal Resources:**
- 📖 [SCHEMA_REFERENCE.md](docs/SCHEMA_REFERENCE.md) - System tables documentation
- 📖 [OPERATIONS_GUIDE.md](docs/OPERATIONS_GUIDE.md) - Daily operations
- 📖 [CONTRACT_BURNDOWN_GUIDE.md](docs/CONTRACT_BURNDOWN_GUIDE.md) - Contract tracking

**External Resources:**
- 🌐 [Databricks System Tables Docs](https://docs.databricks.com/administration-guide/system-tables/index.html)
- 🌐 [Unity Catalog Guide](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- 🌐 [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)

**Support:**
- GitHub Issues: [Report a bug](https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard/issues)
- Databricks Community: [community.databricks.com](https://community.databricks.com)

---

## Maintenance

### Daily Operations (Automated)

```
Daily Refresh      → 2:00 AM UTC    → Updates dashboard_data and contract_burndown
Weekly Review      → Monday 8:00 AM → Analyzes trends and anomalies
Monthly Summary    → 1st @ 6:00 AM  → Generates monthly report
```

### Monthly Tasks

**Review Contract Status:**
```sql
-- Check contracts nearing completion
SELECT contract_id,
       ROUND(consumed_pct, 1) as pct_used,
       days_remaining,
       pace_status
FROM main.account_monitoring_dev.contract_burndown_summary
WHERE consumed_pct > 80 OR days_remaining < 30;
```

**Update Account Metadata:**
```sql
-- Update team assignments if changed
UPDATE main.account_monitoring_dev.account_metadata
SET account_executive = 'New AE Name',
    solutions_architect = 'New SA Name',
    updated_at = CURRENT_TIMESTAMP()
WHERE account_id = '<YOUR_ACCOUNT_ID>';
```

---

## Success Checklist

### Deployment Phase
- [ ] Repository cloned
- [ ] databricks.yml configured with your values
- [ ] Bundle validation passes
- [ ] Bundle deployed to dev environment
- [ ] Notebooks visible in workspace
- [ ] SQL scripts uploaded

### Setup Phase
- [ ] Schema created (account_monitoring_dev)
- [ ] All 5 tables created
- [ ] System tables accessible
- [ ] Cost calculation works

### Data Phase
- [ ] Contract data inserted (at least 1 contract)
- [ ] Account metadata inserted
- [ ] Dashboard data refresh completed
- [ ] Contract burndown calculated
- [ ] Data visible in all tables

### Validation Phase
- [ ] Post-deployment validation: 10+/11 tests pass
- [ ] All 17 Lakeview queries return data
- [ ] Jobs scheduled and run successfully
- [ ] Dashboard visualizations display correctly

---

**Deployment Time Estimate:**
- Initial setup: 30-45 minutes
- Contract data preparation: 15-30 minutes
- Testing and validation: 15-20 minutes
- Dashboard creation: 30-60 minutes
- **Total: 1.5 - 3 hours**

---

**Built with ❤️ for Databricks Users**
