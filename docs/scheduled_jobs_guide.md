# Account Monitor - Scheduled Jobs Guide

This guide explains what each scheduled job does in plain English, why it matters, and what to expect from the outputs.

---

## Overview

The Account Monitor runs four scheduled jobs to keep your contract consumption data fresh and actionable:

| Job | When It Runs | What It Does | Dashboard Page |
|-----|--------------|--------------|----------------|
| Daily Refresh | Every day at 2 AM | Pulls new usage data | Executive Summary, Contract Burndown |
| Weekly Training | Every Sunday at 8 AM | Retrains the forecasting model | Contract Burndown, What-If Analysis |
| Weekly Review | Every Monday at 8 AM | Generates operational reports | Weekly Operations |
| Monthly Summary | 1st of each month at 6 AM | Creates executive summary | Monthly Summary |

All times are in UTC.

---

## The Dashboard

All job outputs are visualized in the **Contract Consumption Monitor** dashboard with 5 pages:

```
Contract Consumption Monitor
├── Executive Summary      ← KPIs, overall status
├── Contract Burndown      ← Prophet forecasts, exhaustion dates
├── Weekly Operations      ← Anomalies, pace, top consumers
├── Monthly Summary        ← Trends, MoM comparison
└── What-If Analysis       ← Discount scenarios
```

### Page 1: Executive Summary
High-level KPIs at a glance:
- Total contract value
- Total consumed
- Remaining budget
- Contracts at risk

### Page 2: Contract Burndown
Forecasting and contract health:
- Historical consumption vs. commitment line
- Prophet ML forecast (365 days ahead)
- Exhaustion date prediction
- Contract details table

### Page 3: Weekly Operations
Operational health check (from Weekly Review job):
- Cost Spikes counter (anomalies >50% change)
- Weekend Alerts counter
- Contract Pace Analysis table
- Daily Cost Spikes table
- Weekend Usage table
- Top 10 Workspaces bar chart
- Top 10 Jobs table

### Page 4: Monthly Summary
Executive reporting (from Monthly Summary job):
- Month-over-Month % Change
- Month-over-Month $ Change
- Current Month Cost
- Monthly Cost Trend (12 months)
- Cost by Product Category
- MoM by Cloud Provider table
- Monthly Statistics table (6 months)

### Page 5: What-If Analysis
Contract optimization scenarios:
- Discount scenario comparison chart
- Sweet spot recommendations
- Strategy explanation

---

## Weekly Training Job

### What It Does

This job teaches the system to predict future consumption by learning from past patterns.

Think of it like a weather forecast: just as meteorologists look at historical weather data to predict tomorrow's temperature, this job looks at your past spending to predict future costs.

### The Process

1. **Prepare the data** - Gathers your daily consumption history for each contract
2. **Train the model** - Uses Facebook's Prophet algorithm to learn patterns like:
   - Weekly cycles (higher usage on weekdays vs weekends)
   - Monthly patterns (end-of-month reporting spikes)
   - Overall trends (growing or shrinking usage)
3. **Generate forecasts** - Predicts daily costs for the next 365 days
4. **Run "What-If" scenarios** - Calculates what would happen with different discount levels

### Why Weekly?

Training a machine learning model is computationally expensive. Running it daily would be wasteful since consumption patterns don't change that fast. Weekly retraining balances accuracy with efficiency.

### Dashboard Visualization

Results appear on two dashboard pages:

**Contract Burndown page:**
- Line chart showing historical consumption + Prophet forecast
- Exhaustion date prediction table

**What-If Analysis page:**
- Discount scenario comparison chart
- Sweet spot recommendations

### Example Output

After running, you'll see forecasts like:

```
Contract: AWS-ENTERPRISE-2026
Current consumption: $180,000 (36% of $500,000 commitment)
Predicted exhaustion: August 15, 2026

Forecast confidence:
- Best case (90%): Contract lasts until September 30
- Most likely (50%): Contract exhausted August 15
- Worst case (10%): Contract exhausted July 20
```

---

## Weekly Review Job

### What It Does

This job is your weekly "health check" for contract consumption. It answers three key questions:

1. **Are we on pace?** - Are we spending at the right rate to use our commitment?
2. **Anything unusual?** - Did any costs spike unexpectedly?
3. **Who's spending?** - Which teams, workspaces, or jobs cost the most?

### Dashboard Visualization

Results appear on the **Weekly Operations** dashboard page with 7 widgets:

| Widget | What It Shows |
|--------|---------------|
| Cost Spikes (14 days) | Count of daily anomalies >50% change |
| Weekend Alerts (30 days) | Count of significant weekend usage |
| Contract Pace Analysis | Table with pace status per contract |
| Daily Cost Spikes | Table of day-over-day cost jumps |
| Weekend Usage | Table of Saturday/Sunday costs |
| Top 10 Workspaces | Bar chart of highest-spending workspaces |
| Top 10 Jobs | Table of most expensive jobs |

### The Three Reports

#### Report 1: Contract Pace Analysis

Compares how much you've consumed vs. how much time has passed.

**Example scenario:**
- Contract value: $500,000
- Contract duration: 12 months (Jan 1 - Dec 31)
- Today: July 1 (50% of time elapsed)
- Amount consumed: $320,000 (64% of contract)

**Status: OVER PACE** - You're 14 percentage points ahead of schedule. At this rate, you'll exhaust the contract in mid-October instead of December.

**What the pace indicators mean:**

| Status | What It Means | Action Needed |
|--------|---------------|---------------|
| ON PACE | Consumption matches time elapsed (within 10%) | None - you're on track |
| ABOVE PACE | Consuming 10-20% faster than expected | Monitor closely |
| OVER PACE | Consuming >20% faster than expected | Consider reducing usage or negotiating more credits |
| UNDER PACE | Consuming >20% slower than expected | You may waste unused commitment - find ways to use it |

#### Report 2: Cost Anomalies

Flags unusual spending patterns that deserve investigation.

**Types of anomalies detected:**

**Daily Spikes** - When costs jump more than 50% from one day to the next.

```
Example alert:
Workspace: prod-analytics
Yesterday: $450
Today: $1,230
Change: +173%

Likely cause: Large Spark job or forgotten cluster
Action: Check cluster activity in that workspace
```

**Weekend Usage** - Significant costs on Saturday or Sunday (often unexpected).

```
Example alert:
Saturday, Feb 8: $680 in workspace dev-sandbox

Question: Should anything be running on weekends?
Common causes:
- Scheduled job that should be weekday-only
- Developer left interactive cluster running Friday night
```

#### Report 3: Top Consumers

Shows who and what is spending the most money over the last 30 days.

**Top Workspaces:**
```
Rank | Workspace        | 30-Day Cost | Daily Average
-----|------------------|-------------|---------------
1    | prod-etl         | $45,230     | $1,507
2    | prod-analytics   | $28,100     | $936
3    | dev-sandbox      | $12,400     | $413
```

**Top Jobs:**
```
Rank | Job Name              | 30-Day Cost | Runs | Cost per Run
-----|----------------------|-------------|------|-------------
1    | daily_etl_pipeline   | $18,500     | 30   | $617
2    | weekly_ml_training   | $8,400      | 4    | $2,100
3    | hourly_aggregations  | $6,200      | 720  | $8.60
```

### When to Use This Report

Check the **Weekly Operations** dashboard page every Monday morning to:
- Catch overspending contracts before it's too late
- Investigate any cost spikes from the previous week
- Identify optimization opportunities in your top consumers

---

## Monthly Summary Job

### What It Does

This job creates an executive-level summary of the previous month's consumption. It's designed for monthly business reviews and FinOps reporting.

### Dashboard Visualization

Results appear on the **Monthly Summary** dashboard page with 7 widgets:

| Widget | What It Shows |
|--------|---------------|
| MoM Change (%) | Percentage change vs last month |
| MoM Change ($) | Dollar change vs last month |
| Current Month Cost | This month's total spending |
| Monthly Cost Trend | Bar chart of 12-month history |
| Cost by Product Category | Breakdown by compute, SQL, storage |
| MoM by Cloud Provider | This vs last month by AWS/Azure/GCP |
| Monthly Statistics | 6-month table with workspaces, DBUs, cost |

### The Two Tasks

#### Task 1: Monthly Summary Report

Generates a comprehensive view of last month's spending.

**Section A: Overall Statistics**
```
Month: January 2026

Cloud Provider | Total Cost | Active Workspaces | Unique SKUs | Total DBUs
---------------|------------|-------------------|-------------|------------
AWS            | $142,500   | 12                | 8           | 1,850,000
Azure          | $38,200    | 5                 | 6           | 520,000
```

**Section B: Cost by Product Category**
```
Product Category    | Cost      | % of Total
--------------------|-----------|------------
Jobs Compute        | $78,400   | 43%
SQL Serverless      | $52,300   | 29%
All-Purpose Compute | $31,200   | 17%
Storage             | $12,800   | 7%
Other               | $6,000    | 4%
```

**Section C: Month-over-Month Comparison**
```
                  | December | January | Change  | % Change
------------------|----------|---------|---------|----------
Total Cost        | $168,200 | $180,700| +$12,500| +7.4%
Jobs Compute      | $72,100  | $78,400 | +$6,300 | +8.7%
SQL Serverless    | $48,900  | $52,300 | +$3,400 | +6.9%
```

#### Task 2: Archive Old Data

Moves data older than 2 years to an archive table. This keeps your main tables fast and responsive.

```
Archive Summary:
Records archived: 45,230
Date range: Jan 2024 - Jan 2024
Total cost archived: $892,400

Main table optimized.
```

### When to Use This Report

Check the **Monthly Summary** dashboard page at the start of each month to:
- Report monthly spending to finance/leadership
- Track month-over-month cost trends
- Identify which products are driving cost growth

---

## Real-World Example: A Month in the Life

Here's how these jobs and dashboard pages work together in practice:

**Week 1 (Monday, Feb 3):**
- Weekly Review runs at 8 AM
- Check **Weekly Operations** page
- You notice: Contract is 58% consumed with only 50% time elapsed (ABOVE PACE)
- Action: Alert the team to reduce non-essential workloads

**Week 1 (Sunday, Feb 9):**
- Weekly Training runs at 8 AM
- Check **Contract Burndown** page
- Prophet model updates forecast: Contract will exhaust March 15 (was March 30)
- Check **What-If Analysis** page: 10% discount would extend to April 5

**Week 2 (Monday, Feb 10):**
- Weekly Review runs
- Check **Weekly Operations** page
- You notice: Daily spike of +180% in prod-analytics workspace on Feb 7
- Investigation: Data scientist ran an unoptimized query on a 10TB table
- Action: Optimize the query, saving $400/day going forward

**Month End (Saturday, Mar 1):**
- Monthly Summary runs at 6 AM
- Check **Monthly Summary** page
- February total: $165,000 (up 8% from January)
- Top growth area: SQL Serverless (+15%)
- Action: Review SQL warehouse sizing for optimization opportunities

---

## Quick Reference

### Job Schedules

| Job | Cron Expression | Human Readable |
|-----|-----------------|----------------|
| Daily Refresh | `0 0 2 * * ?` | Every day at 2:00 AM UTC |
| Weekly Training | `0 0 8 ? * SUN` | Every Sunday at 8:00 AM UTC |
| Weekly Review | `0 0 8 ? * MON` | Every Monday at 8:00 AM UTC |
| Monthly Summary | `0 0 6 1 * ?` | 1st of month at 6:00 AM UTC |

### Key Tables Updated

| Job | Tables Written |
|-----|----------------|
| Daily Refresh | `dashboard_data`, `contract_burndown`, `contract_forecast` |
| Weekly Training | `contract_forecast`, `scenario_*` (What-If tables) |
| Weekly Review | None (read-only reports) |
| Monthly Summary | `dashboard_data_archive` |

### Dashboard Pages

| Page | Primary Data Source | Refresh Frequency |
|------|--------------------|--------------------|
| Executive Summary | `contract_burndown_summary` | Real-time |
| Contract Burndown | `contract_burndown`, `contract_forecast` | Daily + Weekly |
| Weekly Operations | `dashboard_data`, `contract_burndown_summary` | Real-time |
| Monthly Summary | `dashboard_data` | Real-time |
| What-If Analysis | `scenario_*` tables | Weekly |

### Manual Execution

You can run any job manually using the Databricks CLI:

```bash
# Run weekly training
databricks bundle run account_monitor_weekly_training

# Run weekly review
databricks bundle run account_monitor_weekly_review

# Run monthly summary
databricks bundle run account_monitor_monthly_summary
```

---

## Troubleshooting

### "No data returned" in reports

**Cause:** No consumption data exists for the time period being analyzed.

**Solution:** Ensure the Daily Refresh job has run successfully and populated `dashboard_data`.

### Forecasts show "linear_fallback" instead of "prophet"

**Cause:** Not enough historical data to train Prophet (needs 30+ days).

**Solution:** Wait until you have at least 30 days of consumption data, then run Weekly Training.

### Contract shows wrong pace status

**Cause:** Contract dates or total value may be incorrect in configuration.

**Solution:** Check `config/contracts.yml` and verify start_date, end_date, and total_value match your actual contract terms.

### Dashboard page shows errors

**Cause:** Dashboard may not have been published after updates.

**Solution:** Re-deploy with `databricks bundle deploy --force` and verify the dashboard is published.

---

*Last updated: February 2026*
*Version: 1.11.0*
