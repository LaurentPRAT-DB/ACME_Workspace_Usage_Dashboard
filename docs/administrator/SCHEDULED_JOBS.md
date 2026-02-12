# Account Monitor - Scheduled Jobs Guide

**For: System Administrators, FinOps Engineers**

---

## Overview

The Account Monitor runs four automated jobs plus manual utility jobs.

### Scheduled Jobs

| Job | Schedule | Purpose | Duration |
|-----|----------|---------|----------|
| Daily Refresh | 2 AM UTC daily | Pull new billing data | ~5 min |
| Weekly Training | Sunday 3 AM UTC | Retrain ML model | ~15 min |
| Weekly Review | Monday 8 AM UTC | Generate operational reports | ~5 min |
| Monthly Summary | 1st of month 6 AM UTC | Executive summary & archive | ~10 min |

### Manual Jobs

| Job | Trigger | Purpose | Duration |
|-----|---------|---------|----------|
| First Install | Manual | Complete initial setup | ~20 min |
| Setup | Manual | Create schema & load contracts | ~2 min |
| Update Discount Tiers | Manual | MERGE discount tiers (incremental) | ~5 min |
| Cleanup | Manual | Drop all tables (reset) | ~1 min |

---

## Daily Refresh Job

### What It Does

Pulls the latest billing data from Databricks system tables and updates the dashboard.

### Tasks

1. **refresh_dashboard_data** - Aggregates `system.billing.usage` data
2. **refresh_contract_burndown** - Updates cumulative consumption per contract
3. **check_data_freshness** - Verifies data is current

### Tables Updated

| Table | What Changes |
|-------|-------------|
| `dashboard_data` | New rows for yesterday's usage |
| `contract_burndown` | New row with updated cumulative cost |

### Expected Output

After running, you should see:
- `dashboard_data` has records up to yesterday
- `contract_burndown.cumulative_cost` increased (if there was usage)

### Manual Run

```bash
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE
```

---

## Weekly Training Job

### What It Does

Retrains the Prophet ML model to improve consumption forecasts.

### Tasks

1. **build_forecast_features** - Prepare training data
2. **train_prophet_model** - Train Prophet on consumption history
3. **generate_forecasts** - Create 365-day predictions
4. **run_whatif_scenarios** - Update discount scenario analysis

### Tables Updated

| Table | What Changes |
|-------|-------------|
| `contract_forecast` | New predictions with updated exhaustion dates |
| `scenario_summary` | Refreshed What-If analysis |

### Why Weekly?

- ML training is computationally expensive
- Consumption patterns don't change daily
- Weekly balances accuracy with efficiency

### Expected Output

After running:
- `contract_forecast.forecast_model` should be "prophet" (or "linear_fallback" if < 30 days data)
- `contract_forecast.training_date` updated to today
- `scenario_summary` has fresh discount scenarios

### Manual Run

```bash
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE
```

---

## Weekly Review Job

### What It Does

Generates operational reports for Monday morning reviews.

### Tasks

1. **contract_analysis** - Calculate pace status for all contracts
2. **cost_anomalies** - Detect spending spikes
3. **top_consumers** - Identify highest-spending workspaces and jobs

### Dashboard Output

Results appear on the **Weekly Operations** page:
- Cost Spikes counter (anomalies detected)
- Weekend Alerts counter
- Contract Pace Analysis table
- Daily Cost Spikes table
- Top 10 Workspaces chart
- Top 10 Jobs table

### What "Pace" Means

| Status | Definition |
|--------|------------|
| ON PACE | Consumption within ±10% of expected |
| ABOVE PACE | 10-20% faster than expected |
| OVER PACE | >20% faster - will exhaust early |
| UNDER PACE | >20% slower - may waste commitment |

### Manual Run

```bash
databricks bundle run account_monitor_weekly_review --profile YOUR_PROFILE
```

---

## Monthly Summary Job

### What It Does

Creates executive-level summaries and archives old data.

### Tasks

1. **monthly_summary** - Generate month-over-month comparison
2. **archive_old_data** - Move data older than 2 years to archive

### Dashboard Output

Results appear on the **Monthly Summary** page:
- Month-over-Month % Change
- Month-over-Month $ Change
- Current Month Cost
- Monthly Cost Trend chart (12 months)
- Cost by Product Category chart
- MoM by Cloud Provider table
- Monthly Statistics table

### Tables Updated

| Table | What Changes |
|-------|-------------|
| `dashboard_data_archive` | Old records moved here |
| `dashboard_data` | Old records removed |

### Manual Run

```bash
databricks bundle run account_monitor_monthly_summary --profile YOUR_PROFILE
```

---

## Update Discount Tiers Job

### What It Does

Updates discount tier configuration using MERGE (incremental update) instead of DELETE+INSERT. This preserves existing tiers while adding or modifying tiers from the config file.

### Tasks

1. **update_tiers** - MERGE discount tiers from YAML config
2. **refresh_whatif** - Regenerate What-If scenarios with updated tiers

### Key Features

- **Non-destructive**: Preserves existing tiers not in config file
- **Incremental**: Only updates changed tiers
- **Automatic refresh**: Regenerates What-If scenarios after update

### Tables Updated

| Table | What Changes |
|-------|-------------|
| `discount_tiers` | New/updated tiers merged in |
| `discount_scenarios` | Regenerated with new tier rates |
| `scenario_summary` | Recalculated KPIs |

### Manual Run

```bash
# Using default discount_tiers.yml
databricks bundle run account_monitor_update_discount_tiers --profile YOUR_PROFILE

# Using an alternative config file
databricks bundle run account_monitor_update_discount_tiers \
  --profile YOUR_PROFILE \
  --notebook-params discount_tiers_file="config/files/discount_tiers_alternative2_aggressive.yml"
```

### When to Use

- After editing `config/discount_tiers.yml`
- When switching to an alternative tier configuration
- To add custom tiers for specific customers

See [CONFIG_UPDATES.md](CONFIG_UPDATES.md) for detailed instructions.

---

## Job Monitoring

### Check Job Status

```bash
# List recent runs
databricks runs list --limit 10 --profile YOUR_PROFILE

# Get specific run details
databricks runs get --run-id RUN_ID --profile YOUR_PROFILE
```

### In Databricks UI

1. Go to **Workflows** > **Jobs**
2. Find job by name (e.g., "Account Monitor - Daily Refresh")
3. Click to see run history
4. Click specific run for task details

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Job not running | Schedule disabled | Enable schedule in job settings |
| Job fails at warehouse | Warehouse stopped | Start the SQL warehouse |
| No data in dashboard | Daily refresh not run | Manually run daily refresh |
| Old forecast dates | Weekly training not run | Manually run weekly training |

---

## Customizing Schedules

### Modify Schedule

Edit `resources/jobs.yml`:

```yaml
schedule:
  quartz_cron_expression: "0 0 2 * * ?"  # 2 AM daily
  timezone_id: UTC
```

Cron format: `seconds minutes hours day-of-month month day-of-week`

Examples:
- `0 0 2 * * ?` - Every day at 2:00 AM
- `0 0 8 ? * SUN` - Every Sunday at 8:00 AM
- `0 0 6 1 * ?` - 1st of each month at 6:00 AM

### Disable a Job

In Databricks UI:
1. Go to **Workflows** > **Jobs**
2. Click job name
3. Toggle **Schedule** off

Or set `pause_status` in YAML:
```yaml
schedule:
  pause_status: PAUSED
```

---

## Data Freshness Expectations

After each job, expect these freshness levels:

| Table | After Daily | After Weekly | After Monthly |
|-------|-------------|--------------|---------------|
| `dashboard_data` | ≤ 1 day stale | ≤ 1 day | ≤ 1 day |
| `contract_burndown` | ≤ 1 day stale | ≤ 1 day | ≤ 1 day |
| `contract_forecast` | Unchanged | ≤ 7 days | ≤ 7 days |
| `scenario_summary` | Unchanged | ≤ 7 days | ≤ 7 days |

### Check Freshness

```sql
SELECT
  'dashboard_data' as table_name,
  MAX(usage_date) as latest_date,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_stale
FROM main.account_monitoring_dev.dashboard_data

UNION ALL

SELECT 'contract_forecast', MAX(forecast_date), DATEDIFF(CURRENT_DATE(), MAX(forecast_date))
FROM main.account_monitoring_dev.contract_forecast;
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [ADMIN_GUIDE.md](ADMIN_GUIDE.md) | Administrator overview |
| [scheduled_jobs_guide.md](../scheduled_jobs_guide.md) | Detailed explanations with examples |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues |

---

*Last updated: February 2026*
