# Stop Leaving Money on the Table: How We Built an ML-Powered Databricks Cost Monitor

*A practical guide to tracking consumption, predicting contract exhaustion, and optimizing your Databricks spend*

---

## The $125K Problem Nobody Talks About

Last year, our finance team got an unpleasant surprise: we'd exhausted our $500K Databricks contract three months early. The result? $50K in overage charges at list price, plus a rushed contract renewal without leverage to negotiate.

Sound familiar?

On the flip side, I've seen teams leave 20-30% of their Databricks commitment unused — money that simply evaporates at contract end.

**The root cause?** Most organizations have zero visibility into their Databricks consumption patterns until it's too late.

![The Problem and Solution](medium_article_images/problem_solution.png)
*From no visibility to data-driven contract management*

This article shows you how we solved this problem by building an **ML-powered Account Monitor** that:
- Tracks consumption in real-time across all workspaces
- Uses Prophet ML to predict contract exhaustion dates
- Recommends optimal discount levels for renewals
- Costs nothing to run (it uses Databricks system tables)

The best part? **You can deploy it in 15 minutes.**

---

## What You'll Learn

| Section | For Whom | Time |
|---------|----------|------|
| The Business Problem | Executives, Finance | 5 min |
| Architecture Overview | Technical Leads | 5 min |
| Quick Start Installation | Administrators | 15 min |
| Deep Dive: The SQL | Developers | 20 min |
| What-If Analysis | FinOps, Procurement | 10 min |

---

## The Business Problem: Flying Blind

When you sign a Databricks contract, you commit to spending a certain amount (say $500K over 12 months). Two scenarios spell trouble:

| Scenario | What Happens | Impact |
|----------|--------------|--------|
| **OVERSPENDING** | Contract: $500K → Used: $550K | $50K overage at LIST PRICE + lost negotiating power |
| **UNDERSPENDING** | Contract: $500K → Used: $350K | $150K wasted commitment — money gone forever |

### The Goal: Hit the Sweet Spot

```
Optimal Outcome = Consume 95-100% of commitment by contract end
```

This seems simple, but requires:
1. **Real-time tracking** — Know where you stand today
2. **ML forecasting** — Predict where you'll be in 6 months
3. **Scenario modeling** — Understand discount trade-offs

That's exactly what we built.

---

## For Executives: The 2-Minute Summary

The Account Monitor is a **Lakeview dashboard** that tells you:

| Question | Answer |
|----------|--------|
| How much have we spent? | Real-time consumption tracking |
| When will we run out? | ML-predicted exhaustion date |
| Are we on track? | Pace status (under/on/over) |
| What discount should we negotiate? | Sweet spot analysis |

![Dashboard Pages Overview](medium_article_images/dashboard_pages.png)
*Five dashboard pages organized by persona: Executive, Operations, and Finance views*

### ROI Example

| Without Monitor | With Monitor |
|-----------------|--------------|
| Discovered over-pace 60 days late | Alerted within 7 days |
| Paid $50K overage at list price | Adjusted usage, stayed in contract |
| Renewed at same 10% discount | Negotiated 15% with usage data |
| **Total Cost: $550K** | **Total Cost: $425K** |
| | **Savings: $125K** |

> **Executive Action Item:** Bookmark the dashboard. Check the Executive Summary page weekly. Use What-If Analysis before any contract renewal discussion.

---

## For Administrators: 15-Minute Installation

### Prerequisites Checklist

```sql
-- Run this in your Databricks SQL Editor to verify access:

-- Test 1: System tables access
SELECT COUNT(*) as record_count, MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);

-- Test 2: Pricing access (required for cost calculation)
SELECT COUNT(*) FROM system.billing.list_prices;
```

If both queries succeed, you're ready to install.

### One-Command Installation

```bash
# 1. Clone the repository
git clone https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard.git
cd ACME_Workspace_Usage_Dashboard

# 2. Configure your contracts (edit this file!)
vi config/contracts.yml

# 3. Deploy with Databricks Asset Bundles
databricks bundle deploy --profile YOUR_PROFILE

# 4. Run the first install job (creates everything)
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

That's it. The job creates all tables, loads your contracts, populates historical data, and trains the ML model.

### What Gets Created

| Component | Purpose |
|-----------|---------|
| Unity Catalog Schema | `main.account_monitoring` |
| 7 Delta Tables | Contracts, burndown, forecasts, scenarios |
| 4 Scheduled Jobs | Daily refresh, weekly training, monthly reports |
| 5-Page Dashboard | Executive, Burndown, Operations, Monthly, What-If |

### Scheduled Jobs (Automated)

| Job | Schedule | Purpose |
|-----|----------|---------|
| Daily Refresh | 2 AM daily | Pull new billing data |
| Weekly Training | Sunday 3 AM | Retrain Prophet ML model |
| Weekly Review | Monday 8 AM | Generate operational reports |
| Monthly Summary | 1st of month | Archive and executive summary |

> **Admin Action Item:** After installation, verify the daily refresh job completes successfully. Set up alerts for job failures.

---

## For Developers: The SQL Patterns That Power It

Here's where it gets interesting. The core insight is that **Databricks provides everything you need in system tables** — you just need to join them correctly.

### Architecture: Data Flow

![Data Flow Architecture](medium_article_images/architecture.png)
*Complete data flow from system tables through ML forecasting to the dashboard*

The architecture shows:
- **Data Sources**: System billing tables + YAML configuration files
- **Processing Layer**: Aggregated billing data and cumulative burndown
- **ML Layer**: Prophet model training and forecasting
- **Output**: Lakeview Dashboard with What-If scenarios

### The Critical Pattern: Cost Calculation

The `system.billing.usage` table has quantities, but **not costs**. You must join with `system.billing.list_prices`:

```sql
-- THE CORRECT WAY TO CALCULATE COSTS
SELECT
  u.usage_date,
  u.workspace_id,
  u.sku_name,
  u.usage_quantity,
  -- The actual cost calculation:
  ROUND(
    SUM(u.usage_quantity *
        CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
    ), 2
  ) as dollar_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.record_type = 'ORIGINAL'  -- Important: exclude corrections
GROUP BY u.usage_date, u.workspace_id, u.sku_name, u.usage_quantity;
```

**Common Mistake:** There is no `usage_metadata.total_price` column. Every tutorial that uses it is wrong. You must use the join pattern above.

### The Contract Burndown Visualization

The heart of the system is the burndown chart — showing historical consumption, ML forecast, and the predicted exhaustion date:

![Contract Burndown with ML Forecast](medium_article_images/contract_burndown_predict.png)
*Actual dashboard output: Historical consumption (blue), Prophet ML forecast (cyan), and contract commitment line (dashed). The model predicts contract exhaustion on 2027-01-30.*

### The Contract Burndown Query

This is the SQL that powers the visualization — cumulative cost over time, compared to commitment:

```sql
-- DAILY CUMULATIVE CONSUMPTION VS COMMITMENT
WITH daily_costs AS (
  SELECT
    usage_date,
    SUM(u.usage_quantity *
        CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name
    AND u.cloud = lp.cloud
    AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.record_type = 'ORIGINAL'
  GROUP BY usage_date
)
SELECT
  c.contract_id,
  d.usage_date,
  d.daily_cost,
  SUM(d.daily_cost) OVER (
    PARTITION BY c.contract_id
    ORDER BY d.usage_date
  ) as cumulative_cost,
  c.total_value as commitment,
  -- Calculate pace status
  CASE
    WHEN cumulative_cost / commitment * 100 >
         DATEDIFF(d.usage_date, c.start_date) /
         DATEDIFF(c.end_date, c.start_date) * 100 * 1.2
    THEN 'OVER_PACE'
    WHEN cumulative_cost / commitment * 100 <
         DATEDIFF(d.usage_date, c.start_date) /
         DATEDIFF(c.end_date, c.start_date) * 100 * 0.8
    THEN 'UNDER_PACE'
    ELSE 'ON_PACE'
  END as pace_status
FROM contracts c
CROSS JOIN daily_costs d
WHERE d.usage_date BETWEEN c.start_date AND c.end_date;
```

### ML Forecasting with Prophet

The system uses Facebook Prophet for time-series forecasting. Here's the simplified training logic:

```python
from prophet import Prophet
import pandas as pd

def train_consumption_forecast(burndown_df: pd.DataFrame) -> pd.DataFrame:
    """Train Prophet model on historical consumption."""

    # Prophet requires columns named 'ds' (date) and 'y' (value)
    prophet_df = burndown_df.rename(columns={
        'usage_date': 'ds',
        'daily_cost': 'y'
    })

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05  # Conservative trend changes
    )
    model.fit(prophet_df)

    # Forecast until contract end
    future = model.make_future_dataframe(periods=180)
    forecast = model.predict(future)

    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

The forecast is then used to calculate predicted exhaustion dates with confidence intervals.

> **Developer Action Item:** Review `developer/TECHNICAL_REFERENCE.md` in the repo for schema details, SQL patterns, and debugging approaches.

---

## For FinOps: The What-If Analysis

This is where the real value lives: **optimizing your next contract renewal**.

### Understanding Discount Tiers

Databricks offers volume discounts based on commitment size and duration:

| Commitment | 1 Year | 2 Year | 3 Year |
|------------|--------|--------|--------|
| $100K-250K | 10% | 12% | 15% |
| $250K-500K | 12% | 15% | 18% |
| $500K-1M | 15% | 18% | 20% |
| $1M+ | 18% | 20% | 22% |

*Actual rates vary — negotiate!*

### Finding the Sweet Spot

The "sweet spot" is the discount level that:
- **Maximizes savings** (higher discount = better)
- **Ensures full utilization** (≥85% of commitment used)

![Sweet Spot Analysis](medium_article_images/sweet_spot.png)
*Visual comparison of discount scenarios: Scenario A (green) provides the best balance of savings and utilization risk*

Here's a real scenario analysis:

```
Historical Usage: $400K/year

Scenario A: $450K commitment @ 15% discount
├─ Effective cost: $382,500
├─ Predicted usage: $400K
├─ Utilization: 89% ✓
└─ Net savings: $67,500

Scenario B: $500K commitment @ 18% discount
├─ Effective cost: $410,000
├─ Predicted usage: $400K
├─ Utilization: 80% ⚠️ (risky)
└─ Net savings: $90K if fully used, or $8K waste if not

Scenario C: $400K commitment @ 12% discount
├─ Effective cost: $352,000
├─ Predicted usage: $400K
├─ Utilization: 100% ✓
└─ Net savings: $48,000

RECOMMENDATION: Scenario A (Sweet Spot)
- Good savings ($67.5K)
- Reasonable utilization risk
- Room for 10-15% growth
```

### The What-If Dashboard Page

The dashboard lets you explore these scenarios interactively:

1. **See your current consumption trend**
2. **Compare 4-5 discount scenarios visually**
3. **Get a strategy recommendation** based on your pattern

> **FinOps Action Item:** Before any renewal, run the What-If Analysis with your actual usage patterns. Bring the data to negotiations.

---

## Try It Yourself: 3 Paths

### Path 1: Quick Exploration (5 minutes)

Just want to understand your current spending?

```sql
-- YESTERDAY'S SPEND
SELECT ROUND(
  SUM(u.usage_quantity *
      CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
  ), 2) as yesterday_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL';

-- MONTH-TO-DATE SPEND
SELECT ROUND(
  SUM(u.usage_quantity *
      CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
  ), 2) as mtd_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
  AND u.record_type = 'ORIGINAL';
```

### Path 2: Full Installation (15 minutes)

Deploy the complete solution with ML forecasting:

```bash
git clone https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard.git
cd ACME_Workspace_Usage_Dashboard
vi config/contracts.yml  # Add your contracts!
databricks bundle deploy --profile YOUR_PROFILE
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

### Path 3: Deep Dive into the Code

The repo includes comprehensive documentation for each persona:

| Persona | Start Here |
|---------|------------|
| Executive | `docs/executive/EXECUTIVE_SUMMARY.md` |
| Administrator | `docs/administrator/ADMIN_GUIDE.md` |
| Developer | `docs/developer/TECHNICAL_REFERENCE.md` |
| FinOps | `docs/executive/CONTRACT_OPTIMIZATION_STRATEGY.md` |

---

## Common Gotchas (Save Yourself Hours)

### Gotcha 1: "Column not found: usage_metadata.total_price"

**Cause:** This column doesn't exist. Many tutorials reference it incorrectly.

**Solution:** Use the `list_prices` JOIN pattern shown throughout this article.

### Gotcha 2: "Table not found: account_monitoring.contracts"

**Cause:** Missing Unity Catalog prefix.

**Solution:** Always use full path: `main.account_monitoring.contracts`

### Gotcha 3: "Costs are NULL"

**Cause:** Incorrect pricing join or missing type cast.

**Solution:** Use the complete JOIN pattern with `CAST(...AS DECIMAL(20,10))`.

### Gotcha 4: "No data returned"

**Cause:** System tables have 24-48 hour lag.

**Solution:** Check freshness: `SELECT MAX(usage_date) FROM system.billing.usage`

---

## What's Next?

Once you have the monitor running:

1. **Week 1:** Review the dashboard daily, understand your patterns
2. **Week 2:** Set up Slack/email alerts for cost spikes
3. **Month 1:** Use What-If Analysis for any contract discussions
4. **Ongoing:** Let the system run — it updates automatically

---

## Resources

- **GitHub Repository:** [github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard](https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard)
- **Databricks System Tables Docs:** [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- **Prophet ML Documentation:** [facebook.github.io/prophet](https://facebook.github.io/prophet/)

---

## About the Author

*I'm a Solutions Architect at Databricks who got tired of seeing customers surprised by their cloud bills. This project started as a hackathon idea and evolved into a production-grade solution that's saved our customers significant money.*

*Questions? Feedback? Open an issue on GitHub or connect on [LinkedIn].*

---

**Did this help?** Give it a clap and follow for more practical Databricks content.

*Tags: #Databricks #DataEngineering #CloudCost #FinOps #MachineLearning #Prophet*
