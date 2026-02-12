# 🚀 Databricks Asset Bundle - Complete Package

## ✅ Ready to Deploy!

Your Account Monitor is now packaged as a **Databricks Asset Bundle (DAB)** and ready to deploy to your **LPT_FREE_EDITION** workspace.

## 📦 What Was Created

### Bundle Configuration
- ✅ `databricks.yml` - Main bundle configuration with LPT_FREE_EDITION profile
- ✅ `resources/jobs.yml` - 4 automated jobs defined
- ✅ `.gitignore` - Git ignore configuration

### SQL Files (9 production-ready queries)
- ✅ `sql/setup_schema.sql` - Creates Unity Catalog schema and tables
- ✅ `sql/insert_sample_data.sql` - Inserts sample data
- ✅ `sql/refresh_dashboard_data.sql` - Daily data refresh
- ✅ `sql/check_data_freshness.sql` - Data quality validation
- ✅ `sql/contract_analysis.sql` - Contract consumption analysis
- ✅ `sql/cost_anomalies.sql` - Anomaly detection
- ✅ `sql/top_consumers.sql` - Top resource consumers
- ✅ `sql/monthly_summary.sql` - Monthly reporting
- ✅ `sql/archive_old_data.sql` - Data archival

### Documentation
- ✅ `DAB_README.md` - Bundle overview
- ✅ `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- ✅ `DAB_QUICK_COMMANDS.md` - Command reference card

### Jobs That Will Be Deployed

#### 1. Setup Job (Run Once)
- Creates Unity Catalog schema: `main.account_monitoring`
- Creates 4 tables: contracts, account_metadata, dashboard_data, daily_summary
- Inserts sample data
- **Schedule**: Manual (you trigger it)

#### 2. Daily Refresh Job
- Refreshes dashboard data from system.billing.usage
- Optimizes tables for performance
- Validates data freshness
- **Schedule**: Daily at 2:00 AM UTC (auto-scheduled)

#### 3. Weekly Review Job
- Analyzes contract consumption vs. pace
- Detects cost anomalies and spikes
- Identifies top consumers
- **Schedule**: Every Monday at 8:00 AM UTC

#### 4. Monthly Summary Job
- Generates monthly cost summary
- Month-over-month comparison
- Archives data older than 2 years
- **Schedule**: 1st of month at 6:00 AM UTC

## 🎯 Quick Deploy (3 Steps)

### Step 1: Configure CLI Profile

```bash
databricks configure --profile LPT_FREE_EDITION
```

You'll need:
- **Host**: Your workspace URL (e.g., `https://dbc-xxxxx.cloud.databricks.com`)
- **Token**: Your personal access token

### Step 2: Update Warehouse ID

Edit `databricks.yml` and set your warehouse ID:

```yaml
variables:
  warehouse_id:
    default: "YOUR_WAREHOUSE_ID"  # ← Change this
```

Get your warehouse ID:
```bash
databricks warehouses list --profile LPT_FREE_EDITION
```

### Step 3: Deploy

```bash
# Validate
databricks bundle validate --profile LPT_FREE_EDITION

# Deploy to dev
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# Run setup
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev
```

Done! ✨

## 📊 What Gets Created in Your Workspace

### Unity Catalog Objects
```
main.account_monitoring_dev/
├── contracts                  (Contract tracking)
├── account_metadata          (Customer information)
├── dashboard_data           (Main dashboard data - 365 days)
└── daily_summary            (Fast aggregated queries)
```

### Workflows (Jobs)
```
[dev] Account Monitor - Setup
[dev] Account Monitor - Daily Refresh
[dev] Account Monitor - Weekly Review
[dev] Account Monitor - Monthly Summary
```

### Workspace Files
```
/Users/<your-email>/.bundle/account_monitor/dev/
└── files/
    └── sql/                 (All SQL files uploaded)
```

## 🔧 Configuration Options

### Environment Targets

**Development (default)**
```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t dev
```
- Schema: `main.account_monitoring_dev`
- Jobs prefixed: `[dev]`
- Safe for testing

**Production**
```bash
databricks bundle deploy --profile LPT_FREE_EDITION -t prod
```
- Schema: `main.account_monitoring`
- Jobs prefixed: `[prod]`
- For production use

### Configurable Variables

In `databricks.yml`:

```yaml
variables:
  catalog:
    default: main              # Change catalog if needed

  schema:
    default: account_monitoring  # Change schema name

  warehouse_id:
    default: ""                # REQUIRED: Your warehouse ID

  notification_email:
    default: ""                # Email for job alerts
```

## 📈 Post-Deployment Steps

### 1. Update Account Metadata

```sql
UPDATE main.account_monitoring_dev.account_metadata
SET
  customer_name = 'Your Organization',
  salesforce_id = 'SF-123456',
  business_unit_l0 = 'REGION',
  account_executive = 'John Doe',
  solutions_architect = 'Jane Smith'
WHERE account_id = (
  SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1
);
```

### 2. Add Your Contracts

```sql
INSERT INTO main.account_monitoring_dev.contracts VALUES
  ('CONTRACT-001',
   (SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1),
   'aws',
   DATE'2024-01-01',
   DATE'2025-12-31',
   500000.00,
   'USD',
   'SPEND',
   'ACTIVE',
   'AWS contract',
   CURRENT_TIMESTAMP(),
   CURRENT_TIMESTAMP());
```

### 3. Run Initial Data Refresh

```bash
databricks bundle run account_monitor_daily_refresh \
  --profile LPT_FREE_EDITION -t dev
```

### 4. Verify Data

```sql
-- Check dashboard data
SELECT
  MAX(usage_date) as latest_date,
  COUNT(*) as records,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data;

-- View contracts
SELECT * FROM main.account_monitoring_dev.contracts;
```

## 🎨 Common Operations

### View Deployed Resources

```bash
databricks bundle resources --profile LPT_FREE_EDITION -t dev
```

### Run Any Job

```bash
databricks bundle run <job_name> --profile LPT_FREE_EDITION -t dev
```

Job names:
- `account_monitor_setup`
- `account_monitor_daily_refresh`
- `account_monitor_weekly_review`
- `account_monitor_monthly_summary`

### Update and Redeploy

```bash
# 1. Edit any SQL file
vim sql/refresh_dashboard_data.sql

# 2. Validate changes
databricks bundle validate --profile LPT_FREE_EDITION

# 3. Deploy updates
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# Changes take effect immediately
```

### Monitor Job Runs

```bash
# List recent runs
databricks jobs runs list --profile LPT_FREE_EDITION --limit 10

# Get run details
databricks jobs get-run <run-id> --profile LPT_FREE_EDITION
```

## 🔍 Monitoring & Validation

### Check System Tables Access

```bash
databricks sql-query create \
  --warehouse-id <warehouse-id> \
  --query "SELECT MAX(usage_date) FROM system.billing.usage" \
  --profile LPT_FREE_EDITION
```

### View Job Status in UI

1. Go to **Workflows** → **Jobs**
2. Look for jobs with `[dev]` prefix
3. Click to view runs and logs

### Query Dashboard Data

```sql
-- Today's cost
SELECT
  cloud_provider,
  ROUND(SUM(actual_cost), 2) as cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date = CURRENT_DATE() - 1
GROUP BY cloud_provider;

-- Top 10 workspaces
SELECT
  workspace_id,
  ROUND(SUM(actual_cost), 2) as cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id
ORDER BY cost DESC
LIMIT 10;
```

## 🚨 Troubleshooting

### "Profile not found"
```bash
# Reconfigure profile
databricks configure --profile LPT_FREE_EDITION
```

### "Warehouse not found"
```bash
# List warehouses
databricks warehouses list --profile LPT_FREE_EDITION

# Update databricks.yml with correct ID
```

### "Permission denied"
Check that your token has:
- Workspace access permissions
- Unity Catalog CREATE permissions
- Workflow creation permissions

### Jobs not running
1. Verify jobs are enabled (not paused)
2. Check warehouse is running
3. Review job run logs in UI
4. Validate SQL syntax

## 📚 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| **DAB_README.md** | Bundle overview and quick start |
| **DEPLOYMENT_GUIDE.md** | Complete deployment instructions |
| **DAB_QUICK_COMMANDS.md** | Command reference card |
| **SCHEMA_REFERENCE.md** | System table schemas |
| **CORRECTIONS_SUMMARY.md** | Schema corrections and fixes |

## 💡 Best Practices

1. ✅ Always test in `dev` before deploying to `prod`
2. ✅ Use `databricks bundle validate` before every deploy
3. ✅ Commit `databricks.yml` and SQL files to Git
4. ✅ Set up email notifications for job failures
5. ✅ Monitor job runs regularly
6. ✅ Keep SQL queries optimized
7. ✅ Review and update contracts and metadata regularly

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Account Monitor

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Databricks CLI
        run: pip install databricks-cli

      - name: Validate Bundle
        run: databricks bundle validate --profile LPT_FREE_EDITION
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}

      - name: Deploy to Dev
        run: databricks bundle deploy --profile LPT_FREE_EDITION -t dev
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

## 🎯 Success Checklist

After deployment, verify:

- [ ] Bundle validated without errors
- [ ] All jobs created in workspace
- [ ] Unity Catalog schema exists
- [ ] All 4 tables created
- [ ] Sample data inserted
- [ ] Dashboard data refreshed
- [ ] Jobs scheduled correctly
- [ ] Email notifications configured
- [ ] Account metadata updated
- [ ] Contracts added

## 🔗 External References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/)
- [System Tables Documentation](https://docs.databricks.com/admin/system-tables/)
- [Unity Catalog Guide](https://docs.databricks.com/data-governance/unity-catalog/)

## 📞 Support

### For Bundle Issues
- Check `DEPLOYMENT_GUIDE.md`
- Review `DAB_QUICK_COMMANDS.md`
- Validate configuration

### For Schema Issues
- See `SCHEMA_REFERENCE.md`
- Check `CORRECTIONS_SUMMARY.md`

### For SQL Queries
- Review `account_monitor_queries_CORRECTED.sql`
- Check `QUICK_REFERENCE.md`

---

## 🚀 Ready to Deploy?

```bash
# Quick Start
databricks configure --profile LPT_FREE_EDITION
databricks bundle validate --profile LPT_FREE_EDITION
databricks bundle deploy --profile LPT_FREE_EDITION -t dev
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev
```

**Next Steps**: See `DAB_README.md` for detailed instructions!
