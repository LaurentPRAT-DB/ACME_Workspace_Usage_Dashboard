# Databricks Asset Bundle - Account Monitor

## What is This?

This is a **Databricks Asset Bundle (DAB)** that deploys a complete cost and usage monitoring solution to your Databricks workspace using infrastructure-as-code.

## What Gets Deployed?

### 🗄️ Unity Catalog Objects
- Schema: `main.account_monitoring`
- Tables: `contracts`, `account_metadata`, `dashboard_data`, `daily_summary`

### ⚙️ Jobs (Workflows)
1. **Setup Job** - Creates schema and tables (run once)
2. **Daily Refresh** - Updates dashboard data daily at 2 AM UTC
3. **Weekly Review** - Contract and cost analysis every Monday at 8 AM UTC
4. **Monthly Summary** - Monthly reports on 1st of month at 6 AM UTC

### 📊 SQL Queries
- 9 production-ready SQL files for all analyses
- Contract consumption tracking
- Cost anomaly detection
- Top consumer identification
- Data archival automation

## Quick Start (3 Commands)

```bash
# 1. Configure your profile
databricks configure --profile LPT_FREE_EDITION

# 2. Deploy everything
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# 3. Run setup
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev
```

Done! Your account monitor is now deployed and running.

## What Makes DAB Different?

| Traditional Approach | Databricks Asset Bundle |
|---------------------|------------------------|
| Manual job creation in UI | Jobs defined as code |
| Copy-paste SQL files | SQL files auto-uploaded |
| Manual permission management | Permissions as code |
| Hard to replicate | Deploy to dev/prod instantly |
| No version control | Everything in Git |
| Error-prone | Validated before deployment |

## File Structure

```
databricks_conso_reports/
├── databricks.yml              # Main configuration
├── resources/
│   └── jobs.yml               # Job definitions
└── sql/
    ├── setup_schema.sql       # Creates tables
    ├── refresh_dashboard_data.sql
    ├── contract_analysis.sql
    ├── cost_anomalies.sql
    └── ... (9 SQL files total)
```

## Configuration

### Required: Warehouse ID

Get your SQL Warehouse ID:

```bash
# Method 1: CLI
databricks warehouses list --profile LPT_FREE_EDITION --output json | jq -r '.[0].id'

# Method 2: UI
# Go to SQL Warehouses → Click warehouse → Copy ID from URL
```

Update `databricks.yml`:

```yaml
variables:
  warehouse_id:
    default: "YOUR_WAREHOUSE_ID_HERE"

  notification_email:
    default: "your-email@company.com"
```

### Optional: Catalog Configuration

By default uses `main` catalog. To use a different catalog:

```yaml
variables:
  catalog:
    default: "your_catalog_name"
```

## Deployment Targets

### Development (default)

```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t dev
```

- Schema: `main.account_monitoring_dev`
- Jobs prefixed with `[dev]`
- Safe for testing

### Production

```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t prod
```

- Schema: `main.account_monitoring`
- Jobs prefixed with `[prod]`
- Runs as service principal (configured separately)

## Common Commands

```bash
# Validate configuration
databricks bundle validate --profile LPT_FREE_EDITION

# Deploy to dev
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# Run a specific job
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev

# View deployed resources
databricks bundle resources --profile LPT_FREE_EDITION -t dev

# Destroy deployment
databricks bundle destroy --profile LPT_FREE_EDITION -t dev
```

## Post-Deployment

### 1. Update Account Metadata

```sql
UPDATE main.account_monitoring_dev.account_metadata
SET
  customer_name = 'Your Org',
  salesforce_id = 'YOUR-ID',
  business_unit_l0 = 'REGION',
  account_executive = 'Name',
  solutions_architect = 'Name'
WHERE account_id = (SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1);
```

### 2. Add Contracts

```sql
INSERT INTO main.account_monitoring_dev.contracts
VALUES (
  'CONTRACT-001',
  (SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1),
  'aws',
  '2024-01-01',
  '2025-12-31',
  500000.00,
  'USD',
  'SPEND',
  'ACTIVE',
  'Your contract',
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
```

### 3. Run Initial Refresh

```bash
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

### 4. Enable Scheduled Jobs

Jobs are created but paused by default. Enable them in the UI or via CLI:

```bash
# Get job ID
JOB_ID=$(databricks jobs list --profile LPT_FREE_EDITION --output json | \
  jq -r '.jobs[] | select(.settings.name | contains("Daily Refresh")) | .job_id')

# Enable schedule
databricks jobs update $JOB_ID --pause-status UNPAUSED --profile LPT_FREE_EDITION
```

## Updating the Bundle

Make changes to any file and redeploy:

```bash
# 1. Edit files (SQL, YAML, etc.)
vim sql/refresh_dashboard_data.sql

# 2. Validate
databricks bundle validate --profile LPT_FREE_EDITION

# 3. Deploy updates
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# Changes are automatically applied
```

## Jobs Included

### 1. Setup Job (Run Once)
- Creates Unity Catalog schema
- Creates tables (contracts, account_metadata, dashboard_data)
- Inserts sample data
- **Schedule**: Manual (paused by default)

### 2. Daily Refresh Job
- Refreshes dashboard_data from system.billing.usage
- Optimizes tables
- Checks data freshness
- **Schedule**: Daily at 2:00 AM UTC

### 3. Weekly Review Job
- Contract consumption analysis
- Cost anomaly detection
- Top consumer identification
- **Schedule**: Every Monday at 8:00 AM UTC

### 4. Monthly Summary Job
- Monthly cost summary
- Month-over-month comparison
- Archives data older than 2 years
- **Schedule**: 1st of month at 6:00 AM UTC

## Monitoring

### View Job Runs

In workspace:
1. Go to **Workflows** → **Jobs**
2. Find jobs with `[dev]` or `[prod]` prefix
3. Click to view run history

Via CLI:
```bash
# List recent runs
databricks jobs runs list --profile LPT_FREE_EDITION --limit 10

# Get run details
databricks jobs get-run <run-id> --profile LPT_FREE_EDITION
```

### Check Table Data

```sql
-- Check latest data
SELECT
  MAX(usage_date) as latest_date,
  COUNT(*) as total_records,
  SUM(actual_cost) as total_cost
FROM main.account_monitoring_dev.dashboard_data;

-- View contracts
SELECT * FROM main.account_monitoring_dev.contracts;

-- Check daily summary
SELECT * FROM main.account_monitoring_dev.daily_summary
ORDER BY usage_date DESC
LIMIT 10;
```

## Troubleshooting

### "Profile not found"
```bash
databricks configure --profile LPT_FREE_EDITION
```

### "Warehouse not found"
Update `warehouse_id` in `databricks.yml` with a valid warehouse ID.

### "Permission denied"
Ensure your token has permissions to:
- Create jobs
- Create Unity Catalog objects
- Execute SQL

### Jobs not running
1. Check job is enabled (not paused)
2. Verify warehouse is running
3. Check SQL query syntax
4. View job run logs in UI

## Best Practices

1. ✅ Always validate before deploying
2. ✅ Test in dev before promoting to prod
3. ✅ Commit databricks.yml and SQL files to Git
4. ✅ Use meaningful commit messages
5. ✅ Set up email notifications
6. ✅ Monitor job success/failure
7. ✅ Regularly review and optimize queries

## Advanced Features

### Variable Templating

SQL files support Jinja templating:

```sql
-- In SQL file
SELECT * FROM {{catalog}}.{{schema}}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), {{retention_days}})
```

Define in `databricks.yml`:

```yaml
variables:
  retention_days:
    default: 365
```

### Multiple Environments

Add custom targets:

```yaml
targets:
  staging:
    workspace:
      root_path: ~/.bundle/${bundle.name}/staging
    variables:
      catalog: main
      schema: account_monitoring_staging
```

Deploy:
```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t staging
```

## Architecture

```
                                   ┌─────────────────┐
                                   │ Databricks CLI  │
                                   └────────┬────────┘
                                            │
                                   ┌────────▼────────┐
                                   │ databricks.yml  │
                                   │  (Configuration)│
                                   └────────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
           ┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
           │   Jobs (YAML)   │    │   SQL Files     │    │   Permissions   │
           └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                                   ┌────────▼────────┐
                                   │  Databricks     │
                                   │   Workspace     │
                                   └────────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
           ┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
           │  Unity Catalog  │    │   Workflows     │    │   Compute       │
           │    (Tables)     │    │    (Jobs)       │    │  (Warehouse)    │
           └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## What's Next?

1. ✅ Deploy bundle
2. ✅ Run setup job
3. ✅ Update metadata and contracts
4. ⬜ Create Lakeview dashboard (see README.md)
5. ⬜ Set up alerts
6. ⬜ Integrate with your CI/CD

## Documentation

- **Quick Commands**: `DAB_QUICK_COMMANDS.md`
- **Full Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Schema Reference**: `SCHEMA_REFERENCE.md`
- **SQL Queries**: `account_monitor_queries_CORRECTED.sql`

## Support

- DAB Documentation: https://docs.databricks.com/dev-tools/bundles/
- Databricks CLI: https://docs.databricks.com/dev-tools/cli/
- System Tables: https://docs.databricks.com/admin/system-tables/

---

**Quick Start**: `databricks bundle deploy --profile LPT_FREE_EDITION -t dev`

**Questions?** See `DEPLOYMENT_GUIDE.md` for detailed instructions.
