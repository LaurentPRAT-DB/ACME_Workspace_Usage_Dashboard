# Account Monitor - Scheduled Jobs Guide

This guide explains what each scheduled job does in plain English, why it matters, and what to expect from the outputs.

---

## Overview

The Account Monitor runs four scheduled jobs to keep your contract consumption data fresh and actionable:

| Job | When It Runs | What It Does |
|-----|--------------|--------------|
| Daily Refresh | Every day at 2 AM | Pulls new usage data |
| Weekly Training | Every Sunday at 8 AM | Retrains the forecasting model |
| Weekly Review | Every Monday at 8 AM | Generates operational reports |
| Monthly Summary | 1st of each month at 6 AM | Creates executive summary |

All times are in UTC.

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

**New Workspaces** - First-time usage detected in the last 30 days.

```
Example alert:
New workspace: data-science-team
First seen: Feb 1, 2026
Cost so far: $4,200

Action: Verify this workspace is authorized and properly governed
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

**Top Users:**
```
Rank | User                    | 30-Day Cost | Workspaces Used
-----|-------------------------|-------------|----------------
1    | data-pipeline@company   | $32,000     | 3
2    | john.smith@company      | $8,500      | 2
3    | analytics-bot@company   | $6,200      | 1
```

### When to Use This Report

Run the weekly review report every Monday morning to:
- Catch overspending contracts before it's too late
- Investigate any cost spikes from the previous week
- Identify optimization opportunities in your top consumers

---

## Monthly Summary Job

### What It Does

This job creates an executive-level summary of the previous month's consumption. It's designed for monthly business reviews and FinOps reporting.

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

Main table optimized and vacuumed.
```

### When to Use This Report

Run at the start of each month (it's scheduled automatically for the 1st at 6 AM) to:
- Report monthly spending to finance/leadership
- Track month-over-month cost trends
- Identify which products are driving cost growth
- Maintain database performance by archiving old data

---

## Real-World Example: A Month in the Life

Here's how these jobs work together in practice:

**Week 1 (Monday, Feb 3):**
- Weekly Review runs at 8 AM
- You notice: Contract is 58% consumed with only 50% time elapsed (ABOVE PACE)
- Action: Alert the team to reduce non-essential workloads

**Week 1 (Sunday, Feb 9):**
- Weekly Training runs at 8 AM
- Prophet model updates forecast: Contract will exhaust March 15 (was March 30)
- What-If shows: 10% discount would extend to April 5

**Week 2 (Monday, Feb 10):**
- Weekly Review runs
- You notice: Daily spike of +180% in prod-analytics workspace on Feb 7
- Investigation: Data scientist ran an unoptimized query on a 10TB table
- Action: Optimize the query, saving $400/day going forward

**Month End (Saturday, Mar 1):**
- Monthly Summary runs at 6 AM
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

---

*Last updated: February 2026*
*Version: 1.10.0*
