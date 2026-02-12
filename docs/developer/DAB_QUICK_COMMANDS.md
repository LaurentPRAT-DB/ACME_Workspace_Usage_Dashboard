# Databricks Asset Bundle - Quick Command Reference

## 🚀 Essential Commands

### First Time Setup

```bash
# 1. Configure CLI profile
databricks configure --profile LPT_FREE_EDITION

# 2. Validate bundle
databricks bundle validate --profile LPT_FREE_EDITION

# 3. Deploy to dev
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# 4. Run setup job
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev

# 5. Run initial data refresh
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

## 📦 Deployment Commands

```bash
# Validate configuration
databricks bundle validate --profile LPT_FREE_EDITION

# Deploy to development
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# Deploy to production
databricks bundle deploy --profile LPT_FREE_EDITION -t prod

# Force redeploy (overwrite)
databricks bundle deploy --profile LPT_FREE_EDITION -t dev --force

# View what will be deployed (dry run)
databricks bundle deploy --profile LPT_FREE_EDITION -t dev --dry-run
```

## ▶️ Run Jobs

```bash
# Setup (run once)
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev

# Daily refresh
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev

# Weekly review
databricks bundle run account_monitor_weekly_review --profile LPT_FREE_EDITION -t dev

# Monthly summary
databricks bundle run account_monitor_monthly_summary --profile LPT_FREE_EDITION -t dev
```

## 📊 Management Commands

```bash
# List all bundle resources
databricks bundle resources --profile LPT_FREE_EDITION -t dev

# Show bundle summary
databricks bundle summary --profile LPT_FREE_EDITION -t dev

# View deployment state
cat ~/.databricks/bundle/account_monitor/dev/state.json | jq

# List deployed jobs
databricks jobs list --profile LPT_FREE_EDITION --output json | \
  jq -r '.jobs[] | select(.settings.name | contains("Account Monitor"))'

# List recent job runs
databricks jobs runs list --profile LPT_FREE_EDITION --limit 10
```

## 🔍 Monitoring & Debugging

```bash
# View job run status
databricks jobs get-run <run-id> --profile LPT_FREE_EDITION

# Get job run output
databricks jobs get-run-output <run-id> --profile LPT_FREE_EDITION

# List warehouses
databricks warehouses list --profile LPT_FREE_EDITION

# Test SQL query
databricks sql-query create --warehouse-id <id> --query "SELECT 1" --profile LPT_FREE_EDITION

# View workspace files
databricks workspace ls ~/.bundle/account_monitor/dev/files --profile LPT_FREE_EDITION
```

## 🧹 Cleanup

```bash
# Destroy dev deployment
databricks bundle destroy --profile LPT_FREE_EDITION -t dev

# Destroy prod deployment (careful!)
databricks bundle destroy --profile LPT_FREE_EDITION -t prod

# Remove workspace files
databricks workspace rm -r ~/.bundle/account_monitor/dev --profile LPT_FREE_EDITION
```

## 🔧 Configuration

```bash
# View current profile
databricks auth profiles --profile LPT_FREE_EDITION

# List all profiles
cat ~/.databrickscfg

# Test connection
databricks workspace list --profile LPT_FREE_EDITION /

# Get current user
databricks current-user me --profile LPT_FREE_EDITION

# Get warehouse ID
databricks warehouses list --profile LPT_FREE_EDITION --output json | jq -r '.[0].id'
```

## 📝 SQL Queries via CLI

```bash
# Run SQL file
databricks sql-query create \
  --warehouse-id <warehouse-id> \
  --query "$(cat sql/check_data_freshness.sql)" \
  --profile LPT_FREE_EDITION

# Quick query
databricks sql-query create \
  --warehouse-id <warehouse-id> \
  --query "SELECT MAX(usage_date) FROM system.billing.usage" \
  --profile LPT_FREE_EDITION
```

## 🎯 Common Workflows

### Update and Redeploy

```bash
# 1. Edit SQL files or databricks.yml
vim sql/refresh_dashboard_data.sql

# 2. Validate changes
databricks bundle validate --profile LPT_FREE_EDITION

# 3. Deploy updates
databricks bundle deploy --profile LPT_FREE_EDITION -t dev

# 4. Test the updated job
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

### Promote Dev to Prod

```bash
# 1. Test in dev
databricks bundle deploy --profile LPT_FREE_EDITION -t dev
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev

# 2. Validate prod config
databricks bundle validate --profile LPT_FREE_EDITION -t prod

# 3. Deploy to prod
databricks bundle deploy --profile LPT_FREE_EDITION -t prod

# 4. Run setup in prod
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t prod
```

### Check Job Status

```bash
# Get job ID
JOB_ID=$(databricks jobs list --profile LPT_FREE_EDITION --output json | \
  jq -r '.jobs[] | select(.settings.name | contains("Daily Refresh")) | .job_id')

# Get latest run
RUN_ID=$(databricks jobs runs list --profile LPT_FREE_EDITION --job-id $JOB_ID --limit 1 --output json | \
  jq -r '.runs[0].run_id')

# Check run status
databricks jobs get-run $RUN_ID --profile LPT_FREE_EDITION
```

### Enable/Disable Jobs

```bash
# Get job IDs
databricks jobs list --profile LPT_FREE_EDITION --output json | \
  jq -r '.jobs[] | select(.settings.name | contains("Account Monitor")) | "\(.job_id) \(.settings.name)"'

# Disable job
databricks jobs update <job-id> --pause-status PAUSED --profile LPT_FREE_EDITION

# Enable job
databricks jobs update <job-id> --pause-status UNPAUSED --profile LPT_FREE_EDITION
```

## 🐛 Troubleshooting

### Check Profile Configuration

```bash
# List profiles
databricks auth profiles

# View profile details
cat ~/.databrickscfg | grep -A 3 LPT_FREE_EDITION

# Test connection
databricks workspace list --profile LPT_FREE_EDITION / || echo "Connection failed"
```

### Verify Prerequisites

```bash
# Check Databricks CLI version
databricks --version

# Check system tables access
databricks sql-query create \
  --warehouse-id <warehouse-id> \
  --query "SELECT COUNT(*) FROM system.billing.usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)" \
  --profile LPT_FREE_EDITION
```

### View Deployment Logs

```bash
# View bundle state
cat ~/.databricks/bundle/account_monitor/dev/state.json | jq '.resources.jobs'

# Check workspace sync status
databricks sync status --profile LPT_FREE_EDITION
```

## 📚 Help Commands

```bash
# General help
databricks --help

# Bundle help
databricks bundle --help

# Job help
databricks jobs --help

# Specific command help
databricks bundle deploy --help
```

## 🔗 Quick Links

- **Bundle docs**: https://docs.databricks.com/dev-tools/bundles/
- **CLI docs**: https://docs.databricks.com/dev-tools/cli/
- **System tables**: https://docs.databricks.com/admin/system-tables/

## 💡 Tips

1. Always validate before deploying
2. Test in dev before prod
3. Use `--dry-run` to preview changes
4. Check job runs after deployment
5. Keep your CLI updated: `pip install --upgrade databricks-cli`
6. Use `--output json` with `jq` for parsing
7. Set up aliases for common commands

## 🎨 Bash Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias dab='databricks --profile LPT_FREE_EDITION'
alias dab-validate='databricks bundle validate --profile LPT_FREE_EDITION'
alias dab-deploy-dev='databricks bundle deploy --profile LPT_FREE_EDITION -t dev'
alias dab-deploy-prod='databricks bundle deploy --profile LPT_FREE_EDITION -t prod'
alias dab-run='databricks bundle run --profile LPT_FREE_EDITION -t dev'
alias dab-list='databricks bundle resources --profile LPT_FREE_EDITION -t dev'
```

Then use:
```bash
dab-validate
dab-deploy-dev
dab-run account_monitor_daily_refresh
```

---

**Quick Start**: `databricks bundle deploy --profile LPT_FREE_EDITION -t dev`

**Full Guide**: See `DEPLOYMENT_GUIDE.md`
