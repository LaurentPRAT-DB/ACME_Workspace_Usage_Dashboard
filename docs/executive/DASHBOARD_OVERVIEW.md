# Account Monitor - Dashboard Overview

**For: Business Stakeholders, Finance, Executives**

A visual guide to the Contract Consumption Monitor dashboard.

---

## Accessing the Dashboard

1. Log in to your Databricks workspace
2. Click **Dashboards** in the left sidebar
3. Find **Contract Consumption Monitor**
4. Bookmark for quick access

---

## Dashboard Pages

The dashboard has 5 pages, each serving a different purpose:

| Page | Purpose | When to Use |
|------|---------|-------------|
| Executive Summary | Overall contract status | Quick daily checks |
| Contract Burndown | Consumption trends & forecasts | Monthly reviews |
| Weekly Operations | Anomalies & operational health | Monday meetings |
| Monthly Summary | Month-over-month analysis | Monthly reporting |
| What-If Analysis | Discount scenarios | Contract negotiations |

---

## Page 1: Executive Summary

### What You'll See

**Key Metrics (Top Row):**
- **Total Contract Value** - Sum of all active commitments
- **Total Consumed** - How much you've spent so far
- **Remaining Budget** - What's left to spend
- **Contracts at Risk** - Contracts needing attention

**Contract Table:**
- All active contracts with status
- Consumption percentage
- Days remaining
- Quick health indicator

### Reading the Numbers

| Metric | Good | Warning | Alert |
|--------|------|---------|-------|
| Consumed % | Matches time elapsed | 10-20% off pace | >20% off pace |
| Remaining | Decreasing steadily | Decreasing too fast | Near zero |

### Example

```
Contract: AWS-ENTERPRISE-2026
Value: $500,000
Consumed: $180,000 (36%)
Remaining: $320,000
Days: 135 of 365 (37% elapsed)
Status: ON PACE ✓
```

This contract is consuming 36% with 37% of time elapsed - perfectly on track.

---

## Page 2: Contract Burndown

### What You'll See

**Chart: Contract Burndown**
A line chart showing:
- **Gold line** - Historical consumption (what you've spent)
- **Red line** - ML forecast (predicted future spending)
- **Blue line** - Contract commitment (your budget line)
- **White vertical line** - Predicted exhaustion date

**Tables:**
- Contract Details with start/end dates
- Exhaustion Predictions with dates and confidence

### Reading the Chart

```
                            Commitment Line ($500K)
                    ═══════════════════════════════════════
                                              ↗
                                         ↗     Forecast
                                    ↗
                               ↗
Historical ─────────────↗
                   ↗
              ↗
         ↗
    ↗
Jan    Feb    Mar    Apr    May    Jun    Jul    Aug
                                         ↑
                                    Exhaustion Date
```

- If forecast crosses commitment **before** contract end = Over-spending
- If forecast crosses commitment **after** contract end = Under-spending

### Example Interpretation

```
Exhaustion Date: August 15, 2026
Contract End: December 31, 2026
Status: EARLY EXHAUSTION

Action: You're spending faster than planned. You'll run out
of credits 4.5 months early. Consider reducing usage or
negotiating additional credits.
```

---

## Page 3: Weekly Operations

### What You'll See

**Counters (Top):**
- **Cost Spikes** - Days with >50% cost increase
- **Weekend Alerts** - Significant weekend activity

**Tables:**
- Contract Pace Analysis - How each contract is tracking
- Daily Cost Spikes - Which days had unusual spending
- Weekend Usage - Saturday/Sunday activity
- Top 10 Jobs - Most expensive jobs

**Chart:**
- Top 10 Workspaces by cost (bar chart)

### Understanding Pace Status

| Status | Meaning | Action |
|--------|---------|--------|
| ON PACE | Consumption matches time | None needed |
| ABOVE PACE | 10-20% faster | Monitor closely |
| OVER PACE | >20% faster | Reduce usage or add credits |
| UNDER PACE | >20% slower | Find ways to use commitment |

### Example Anomaly

```
Daily Cost Spike Detected:
Date: Feb 7, 2026
Workspace: prod-analytics
Previous Day: $450
Spike Day: $1,230
Change: +173%

Common Causes:
- Large Spark job ran
- Forgot to stop interactive cluster
- New scheduled job
```

---

## Page 4: Monthly Summary

### What You'll See

**Counters (Top):**
- **MoM % Change** - Percentage change vs last month
- **MoM $ Change** - Dollar change vs last month
- **Current Month Cost** - This month's total

**Charts:**
- Monthly Cost Trend (12 months)
- Cost by Product Category (pie/bar)

**Tables:**
- MoM by Cloud Provider
- Monthly Statistics (6 months of history)

### Understanding Trends

| Trend | Interpretation |
|-------|----------------|
| Steady increase | Growth in usage, may be expected |
| Sharp spike | New workload or anomaly |
| Decline | Reduced activity (planned?) |
| Seasonal pattern | Normal for some businesses |

### Example

```
January 2026: $165,000
February 2026: $180,000
Change: +$15,000 (+9%)

Breakdown:
- Jobs Compute: +$8,000 (new ETL pipeline)
- SQL Serverless: +$5,000 (more queries)
- Storage: +$2,000 (data growth)
```

---

## Page 5: What-If Analysis

### What You'll See

**Chart: Discount Scenarios**
Shows how different discount levels affect your contract:
- Current commitment line
- Various discount scenario lines (5%, 10%, 15%, 20%)

**Table: Scenario Recommendations**
- Discount rate options
- Savings at each level
- Utilization percentage
- Sweet spot indicator

**Strategy Section:**
- Recommended approach
- Reasoning for recommendation

### Understanding Discount Tiers

Databricks offers volume discounts based on:
1. **Commitment size** - Larger commitments = better rates
2. **Contract duration** - Longer terms = better rates

| Commitment | 1 Year | 2 Year | 3 Year |
|------------|--------|--------|--------|
| $100K-250K | 10% | 12% | 15% |
| $250K-500K | 12% | 15% | 18% |
| $500K-1M | 15% | 18% | 20% |
| $1M+ | 18% | 20% | 22% |

### Sweet Spot

The **sweet spot** is the discount level that:
- Maximizes your savings
- While ensuring you use at least 85% of commitment

```
Example Sweet Spot Analysis:

Current: 10% discount, $450K effective commitment
- Predicted consumption: $420K (93% utilization)
- Total savings: $50K
- Status: SWEET SPOT ✓

Alternative: 15% discount, $425K effective commitment
- Predicted consumption: $420K (99% utilization)
- Total savings: $75K
- Risk: May exceed commitment

Recommendation: Consider 15% if growth expected
```

---

## Tips for Using the Dashboard

### Daily (2 minutes)

1. Glance at **Executive Summary**
2. Note any contracts at risk
3. Check recent consumption numbers

### Weekly (10 minutes)

1. Review **Weekly Operations** page
2. Investigate any cost spikes
3. Check contract pace status

### Monthly (30 minutes)

1. Review **Monthly Summary** page
2. Note trends and changes
3. Prepare summary for leadership

### Before Contract Renewals

1. Review **Contract Burndown** for consumption patterns
2. Analyze **What-If Analysis** for optimal discount
3. Export data for negotiation discussions

---

## Related Documents

| Document | Description |
|----------|-------------|
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Business overview |
| [CONTRACT_OPTIMIZATION_STRATEGY.md](CONTRACT_OPTIMIZATION_STRATEGY.md) | Negotiation strategy guide |

---

*Last updated: February 2026*
