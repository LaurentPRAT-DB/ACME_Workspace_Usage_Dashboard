# Databricks Asset Bundle - Deployment Guide

## Overview

This guide explains how to deploy the Account Monitor using Databricks Asset Bundles (DAB) to your LPT_FREE_EDITION workspace.

## Prerequisites

### 1. Install Databricks CLI

```bash
# Using pip
pip install databricks-cli

# Or using Homebrew (macOS)
brew tap databricks/tap
brew install databricks
```

Verify installation:
```bash
databricks --version
```

### 2. Configure CLI Profile

You need to configure the `LPT_FREE_EDITION` profile. Run:

```bash
databricks configure --profile LPT_FREE_EDITION
```

You'll be prompted for:
- **Databricks Host**: Your workspace URL (e.g., `https://dbc-xxxxx.cloud.databricks.com`)
- **Token**: Your personal access token

#### How to Get Your Personal Access Token

1. Log into your Databricks workspace
2. Go to **User Settings** (click your email in top right)
3. Navigate to **Developer** → **Access tokens**
4. Click **Generate new token**
5. Give it a name (e.g., "CLI Access") and set expiration
6. Copy the token immediately (you won't see it again)

Your profile will be saved to `~/.databrickscfg`:

```ini
[LPT_FREE_EDITION]
host = https://dbc-xxxxx.cloud.databricks.com
token = dapi...
```

### 3. Verify Profile Configuration

Test your profile:

```bash
databricks workspace list --profile LPT_FREE_EDITION /
```

If this works, you're ready to deploy!

## Quick Deploy (5 Minutes)

### Step 1: Configure Variables

Before deploying, you need to set some variables. Edit `databricks.yml` and update:

```yaml
variables:
  warehouse_id:
    default: "YOUR_WAREHOUSE_ID"  # Get from SQL Warehouses page

  notification_email:
    default: "your-email@company.com"  # For job notifications
```

#### How to Find Your Warehouse ID

1. Go to **SQL Warehouses** in your workspace
2. Click on your warehouse name
3. Look at the URL: `https://.../#setting/clusters/.../configuration`
4. The ID is the part after `/clusters/` (e.g., `a1b2c3d4e5f6g7h8`)

Or use CLI:
```bash
databricks warehouses list --profile LPT_FREE_EDITION --output json | jq -r '.[0].id'
```

### Step 2: Validate Bundle

From the project directory:

```bash
cd /Users/laurent.prat/Documents/lpdev/databricks_conso_reports

# Validate the bundle configuration
databricks bundle validate --profile LPT_FREE_EDITION
```

You should see:
```
✓ Bundle configuration is valid
```

### Step 3: Deploy to Development

Deploy to the dev environment:

```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t dev
```

This will:
1. Upload all files to workspace
2. Create schema and tables
3. Create jobs (setup, daily refresh, weekly review, monthly summary)
4. Set up permissions

### Step 4: Run Setup Job

After deployment, run the setup job once:

```bash
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev
```

This creates:
- Unity Catalog schema: `main.account_monitoring_dev`
- Tables: `contracts`, `account_metadata`, `dashboard_data`, `daily_summary`
- Sample data

### Step 5: Verify Deployment

Check that everything is created:

```bash
# List deployed jobs
databricks bundle resources --profile LPT_FREE_EDITION -t dev

# Check schema
databricks workspace get-status ~/.bundle/account_monitor/dev --profile LPT_FREE_EDITION
```

Or in SQL Editor:

```sql
-- Check schema exists
SHOW SCHEMAS IN main LIKE 'account_monitoring%';

-- Check tables exist
SHOW TABLES IN main.account_monitoring_dev;

-- Verify sample data
SELECT * FROM main.account_monitoring_dev.account_metadata;
```

## Production Deployment

### Step 1: Update Production Variables

Create a production configuration. Edit `databricks.yml`:

```yaml
targets:
  prod:
    mode: production
    workspace:
      root_path: ~/.bundle/${bundle.name}/${bundle.target}
    variables:
      catalog: main
      schema: account_monitoring  # No _dev suffix
      warehouse_id: "YOUR_PROD_WAREHOUSE_ID"
      notification_email: "team@company.com"
```

### Step 2: Deploy to Production

```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t prod
```

### Step 3: Run Setup Job

```bash
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t prod
```

## Post-Deployment Tasks

### 1. Update Account Metadata

Replace sample data with your actual information:

```sql
-- Update account metadata
UPDATE main.account_monitoring.account_metadata
SET
  customer_name = 'Your Organization',
  salesforce_id = 'YOUR-SFDC-ID',
  business_unit_l0 = 'YOUR-REGION',
  business_unit_l1 = 'YOUR-SUB-REGION',
  account_executive = 'AE Name',
  solutions_architect = 'SA Name',
  updated_at = CURRENT_TIMESTAMP()
WHERE account_id = (
  SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1
);
```

### 2. Add Contracts

```sql
-- Add your actual contracts
INSERT INTO main.account_monitoring.contracts VALUES
  ('YOUR-CONTRACT-ID', 'YOUR-ACCOUNT-ID', 'aws',
   '2024-01-01', '2025-12-31', 500000.00,
   'USD', 'SPEND', 'ACTIVE', 'Your contract notes',
   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
```

### 3. Run Initial Data Refresh

```bash
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t prod
```

### 4. Enable Scheduled Jobs

By default, jobs are created but paused. Enable them:

```bash
# In your workspace, go to Workflows > Jobs
# Find each job and click "Enable"
```

Or via CLI:

```bash
# Get job IDs
databricks jobs list --profile LPT_FREE_EDITION --output json | \
  jq -r '.jobs[] | select(.settings.name | contains("Account Monitor")) | .job_id'

# Enable each job
databricks jobs update <job-id> --pause-status UNPAUSED --profile LPT_FREE_EDITION
```

## Bundle Commands Reference

### Deploy Commands

```bash
# Validate bundle
databricks bundle validate --profile LPT_FREE_EDITION

# Deploy to dev
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# Deploy to prod
databricks bundle deploy --profile LPT_FREE_EDITION -t prod

# Deploy with force flag (overwrite)
databricks bundle deploy --profile LPT_FREE_EDITION -t dev --force
```

### Run Commands

```bash
# Run setup job
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev

# Run daily refresh
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev

# Run weekly review
databricks bundle run account_monitor_weekly_review --profile LPT_FREE_EDITION -t dev

# Run monthly summary
databricks bundle run account_monitor_monthly_summary --profile LPT_FREE_EDITION -t dev
```

### Management Commands

```bash
# List all resources in bundle
databricks bundle resources --profile LPT_FREE_EDITION -t dev

# Destroy bundle (careful!)
databricks bundle destroy --profile LPT_FREE_EDITION -t dev

# View bundle summary
databricks bundle summary --profile LPT_FREE_EDITION -t dev
```

## Directory Structure

After deployment, your bundle structure:

```
databricks_conso_reports/
├── databricks.yml              # Main bundle configuration
├── resources/
│   └── jobs.yml               # Job definitions
├── sql/
│   ├── setup_schema.sql       # Schema creation
│   ├── insert_sample_data.sql # Sample data
│   ├── refresh_dashboard_data.sql
│   ├── check_data_freshness.sql
│   ├── contract_analysis.sql
│   ├── cost_anomalies.sql
│   ├── top_consumers.sql
│   ├── monthly_summary.sql
│   └── archive_old_data.sql
└── .databricks/               # Created during deployment
    └── bundle/
```

In your workspace:

```
/Users/<your-email>/.bundle/account_monitor/
├── dev/
│   ├── files/
│   │   └── sql/              # Uploaded SQL files
│   └── state.json            # Deployment state
└── prod/
    ├── files/
    └── state.json
```

## Customization

### Add Custom Variables

Edit `databricks.yml`:

```yaml
variables:
  custom_tag_team:
    description: Team name for tagging
    default: "data-engineering"

  retention_days:
    description: Days to retain detailed data
    default: 730
```

Use in SQL files:

```sql
WHERE custom_tags['team'] = '{{custom_tag_team}}'
```

### Add Custom Jobs

Create `resources/custom_jobs.yml`:

```yaml
resources:
  jobs:
    my_custom_job:
      name: "[${bundle.target}] My Custom Job"
      tasks:
        - task_key: my_task
          sql_task:
            warehouse_id: ${var.warehouse_id}
            query: |
              SELECT * FROM main.account_monitoring.dashboard_data
              WHERE usage_date = CURRENT_DATE() - 1
```

### Modify SQL Queries

Edit any file in the `sql/` directory. Changes will be deployed on next `bundle deploy`.

## Troubleshooting

### Error: "Profile LPT_FREE_EDITION not found"

**Solution**: Configure the profile:
```bash
databricks configure --profile LPT_FREE_EDITION
```

### Error: "Warehouse not found"

**Solution**: Update the `warehouse_id` in `databricks.yml` with a valid warehouse ID.

### Error: "Permission denied"

**Solution**: Ensure your token has permissions to:
- Create jobs
- Create Unity Catalog schemas and tables
- Execute SQL commands

### Error: "Table already exists"

**Solution**: This is OK if deploying over existing installation. Use `--force` flag if needed.

### Jobs Not Running

**Check**:
1. Jobs are enabled (not paused)
2. Warehouse is running
3. Permissions are correct
4. SQL queries are valid

View job run details:
```bash
databricks jobs get-run <run-id> --profile LPT_FREE_EDITION
```

## Monitoring

### View Job Status

```bash
# List recent job runs
databricks jobs runs list --profile LPT_FREE_EDITION --output json | \
  jq '.runs[] | {job_id, run_id, state: .state.life_cycle_state}'

# Get specific run details
databricks jobs get-run <run-id> --profile LPT_FREE_EDITION
```

### Check Logs

In workspace:
1. Go to **Workflows** → **Jobs**
2. Click on job name
3. Click on a run
4. View output and logs

Or via CLI:
```bash
databricks jobs get-run-output <run-id> --profile LPT_FREE_EDITION
```

## Clean Up

### Remove Dev Deployment

```bash
# Destroy all resources
databricks bundle destroy --profile LPT_FREE_EDITION -t dev

# Manual cleanup if needed
databricks workspace rm -r ~/.bundle/account_monitor/dev --profile LPT_FREE_EDITION
```

### Remove Tables

```sql
-- Drop schema and all tables
DROP SCHEMA main.account_monitoring_dev CASCADE;
```

## Best Practices

1. **Use Dev First**: Always test in dev before prod
2. **Version Control**: Commit `databricks.yml` and SQL files to git
3. **Secrets Management**: Use Databricks secrets for sensitive data
4. **Incremental Updates**: Use `bundle deploy` for updates (no need to destroy)
5. **Monitor Jobs**: Set up email notifications for job failures
6. **Regular Optimization**: Run OPTIMIZE on tables weekly

## Next Steps

1. ✅ Deploy bundle
2. ✅ Run setup job
3. ✅ Update metadata and contracts
4. ✅ Run daily refresh job
5. ⬜ Create Lakeview dashboard
6. ⬜ Set up alerts
7. ⬜ Schedule regular reviews

## Support

- Bundle documentation: https://docs.databricks.com/dev-tools/bundles/
- CLI reference: https://docs.databricks.com/dev-tools/cli/
- System tables: https://docs.databricks.com/admin/system-tables/

For issues with this bundle, check:
- `START_HERE.md` - Getting started guide
- `SCHEMA_REFERENCE.md` - System table schemas
- `CORRECTIONS_SUMMARY.md` - Common issues
