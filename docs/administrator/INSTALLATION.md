# Account Monitor - Installation Guide

**For: System Administrators, DevOps**

---

## Prerequisites

### Required Access

| Requirement | How to Verify |
|-------------|---------------|
| Databricks workspace | Can log in to workspace UI |
| Unity Catalog enabled | Catalog browser shows catalogs |
| system.billing access | `SELECT * FROM system.billing.usage LIMIT 1` works |
| SQL Warehouse | At least one warehouse available |
| Databricks CLI installed | `databricks --version` returns version |

### CLI Installation

```bash
# macOS
brew install databricks

# pip (any OS)
pip install databricks-cli

# Verify
databricks --version
```

### Authentication Setup

```bash
# Configure profile
databricks configure --profile YOUR_PROFILE

# Enter:
# - Databricks Host: https://your-workspace.cloud.databricks.com
# - Personal Access Token: dapi...

# Test
databricks clusters list --profile YOUR_PROFILE
```

---

## Quick Installation (5 minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/databricks_conso_reports.git
cd databricks_conso_reports
```

### Step 2: Configure Contracts

Edit `config/contracts.yml`:

```yaml
account_metadata:
  account_id: "auto"  # Auto-detect from system tables
  customer_name: "Your Company Name"

contracts:
  - contract_id: "CONTRACT-2026-001"
    cloud_provider: "auto"  # auto, AWS, AZURE, or GCP
    start_date: "2026-01-01"
    end_date: "2026-12-31"
    total_value: 500000.00
    currency: "USD"
    status: "ACTIVE"
```

### Step 3: Deploy

```bash
# Validate configuration
databricks bundle validate --profile YOUR_PROFILE

# Deploy resources
databricks bundle deploy --profile YOUR_PROFILE
```

### Step 4: Run First Install

```bash
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

This creates all tables, loads contracts, trains the ML model, and generates What-If scenarios.

### Step 5: Verify

Open the dashboard URL printed at the end, or run:

```bash
# Check tables exist
databricks sql execute --profile YOUR_PROFILE \
  "SELECT COUNT(*) FROM main.account_monitoring_dev.contract_burndown"
```

---

## Configuration Options

### Environment Targets

| Target | Schema | Use Case |
|--------|--------|----------|
| `dev` (default) | `account_monitoring_dev` | Development/testing |
| `prod` | `account_monitoring` | Production |

Deploy to production:
```bash
databricks bundle deploy --target prod --profile PROD_PROFILE
```

### Bundle Variables

Edit `databricks.yml` to customize:

```yaml
variables:
  catalog:
    default: "main"
  schema:
    default: "account_monitoring_dev"
  warehouse_id:
    default: "your-warehouse-id"
  config_files:
    default: "config/contracts.yml"
```

### Multiple Contract Files

Use multiple YAML files for different customers or regions:

```bash
# At deploy time
databricks bundle deploy --profile YOUR_PROFILE

# At runtime
databricks bundle run account_monitor_first_install \
  --param config_files="config/contracts.yml,config/contracts_emea.yml" \
  --profile YOUR_PROFILE
```

---

## Detailed Installation Steps

### 1. Verify System Table Access

```sql
-- Run in SQL Editor
SELECT COUNT(*) FROM system.billing.usage;
SELECT COUNT(*) FROM system.billing.list_prices;
```

If these fail, contact your Databricks account admin to grant access.

### 2. Choose SQL Warehouse

The system needs a SQL warehouse. Options:

| Type | Best For |
|------|----------|
| Serverless | Recommended - auto-scales, no management |
| Pro | Existing warehouse, fine for most cases |
| Classic | Legacy, may have restrictions |

Get warehouse ID:
```bash
databricks warehouses list --profile YOUR_PROFILE
```

### 3. Configure databricks.yml

Key settings:

```yaml
bundle:
  name: account_monitor

targets:
  dev:
    mode: development
    default: true
    variables:
      warehouse_id: "abc123def456"  # Your warehouse ID
```

### 4. Deploy Bundle

```bash
# First deployment
databricks bundle deploy --profile YOUR_PROFILE

# Force overwrite if dashboard exists
databricks bundle deploy --force --profile YOUR_PROFILE
```

### 5. Run First Install Job

The first install job:
1. Creates all tables and views
2. Loads contracts from YAML
3. Pulls billing data from system tables
4. Trains Prophet ML model
5. Generates What-If scenarios
6. Validates everything works

```bash
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

Monitor progress in Databricks UI under Workflows > Jobs.

### 6. Access Dashboard

After successful installation:

1. Go to Databricks workspace
2. Click **Dashboards** in left sidebar
3. Find **Contract Consumption Monitor**
4. Bookmark for easy access

---

## Post-Installation

### Enable Scheduled Jobs

After first install, enable the scheduled jobs:

| Job | Action |
|-----|--------|
| Daily Refresh | Auto-enabled (2 AM UTC) |
| Weekly Training | Auto-enabled (Sunday 8 AM UTC) |
| Weekly Review | Auto-enabled (Monday 8 AM UTC) |
| Monthly Summary | Auto-enabled (1st of month 6 AM UTC) |

### Grant User Access

```sql
-- Grant dashboard access
GRANT USE CATALOG ON CATALOG main TO `user@company.com`;
GRANT USE SCHEMA ON SCHEMA main.account_monitoring_dev TO `user@company.com`;
GRANT SELECT ON SCHEMA main.account_monitoring_dev TO `user@company.com`;

-- For system tables (requires account admin)
GRANT SELECT ON TABLE system.billing.usage TO `user@company.com`;
```

### Set Up Alerts (Optional)

Create SQL alerts for:
- Data staleness > 3 days
- Contract exhaustion within 30 days
- Cost spikes > 100%

See [ADMIN_GUIDE.md](ADMIN_GUIDE.md#alerting-setup) for queries.

---

## Troubleshooting Installation

### Bundle Validation Fails

```
Error: Invalid configuration
```

**Fix**: Check YAML syntax in `databricks.yml` and `config/contracts.yml`.

### Warehouse Not Found

```
Error: SQL warehouse not found
```

**Fix**: Update `warehouse_id` in `databricks.yml` with correct ID from:
```bash
databricks warehouses list --profile YOUR_PROFILE
```

### Permission Denied on System Tables

```
Error: Permission denied: system.billing.usage
```

**Fix**: Contact account admin to grant:
```sql
GRANT SELECT ON TABLE system.billing.usage TO `user@company.com`;
```

### Dashboard Already Exists

```
Error: Dashboard with name already exists
```

**Fix**: Use `--force` flag:
```bash
databricks bundle deploy --force --profile YOUR_PROFILE
```

### First Install Job Fails

Check the job run in Databricks UI:
1. Go to Workflows > Jobs
2. Click on failed run
3. Check task outputs for specific error

Common issues:
- Wrong catalog/schema
- Missing permissions
- SQL warehouse stopped

---

## Uninstallation

To remove all resources:

```bash
# Run cleanup job (if available)
databricks bundle run account_monitor_cleanup --profile YOUR_PROFILE

# Or manually drop schema
databricks sql execute --profile YOUR_PROFILE \
  "DROP SCHEMA IF EXISTS main.account_monitoring_dev CASCADE"

# Destroy bundle resources
databricks bundle destroy --profile YOUR_PROFILE
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [ADMIN_GUIDE.md](ADMIN_GUIDE.md) | Administrator overview |
| [SCHEDULED_JOBS.md](SCHEDULED_JOBS.md) | Job descriptions |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues |

---

*Last updated: February 2026*
