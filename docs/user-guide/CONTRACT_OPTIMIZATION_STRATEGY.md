# Contract Optimization Strategy - Business Summary

## What This System Does

The **Databricks Account Monitor** helps you answer one critical question: **"Are we getting the best value from our Databricks contract?"**

It tracks your actual cloud consumption, uses machine learning to predict future spending, and then simulates different contract scenarios to find the optimal deal.

---

## The Core Business Problem

Databricks contracts work like a **prepaid commitment**: you agree to spend a certain amount (e.g., $200,000) over a period (e.g., 1 year) in exchange for a discount off list prices. The challenge is:

| Scenario | What Happens | Risk |
|----------|--------------|------|
| **Over-commit** | You pay for consumption you never use | **Money lost** - unused commitment is forfeited |
| **Under-commit** | You consume more than planned at full price | **Overpay** - lost discount opportunity |
| **Right-size** | Consumption matches commitment | **Optimal** - maximum discount, full utilization |

---

## The Optimization Strategy

The system uses a **three-step approach**:

### 1. Track Historical Consumption
- Pulls actual spend data from Databricks billing tables
- Calculates daily burn rate and cumulative spend
- Shows how much of your contract you've used

### 2. Predict Future Consumption (Prophet ML)
- Uses Facebook's Prophet time-series forecasting model
- Predicts when your current contract will be exhausted
- Provides confidence intervals (optimistic, expected, conservative)

### 3. Simulate "What-If" Scenarios
This is the key strategic tool. The system asks: **"What if we had a different contract?"**

---

## How the Discount Tiers Work

Discounts are based on **two factors**:

| Factor | Impact |
|--------|--------|
| **Commitment Size** | Bigger commitment = bigger discount |
| **Contract Duration** | Longer term = bigger discount |

**Example Discount Table:**

| Annual Commitment | 1-Year | 2-Year | 3-Year |
|-------------------|--------|--------|--------|
| $50K - $100K | 5% | 8% | 10% |
| $100K - $250K | 10% | 15% | 18% |
| $250K - $500K | 15% | 20% | 25% |
| $500K - $1M | 20% | 25% | 30% |
| $1M - $5M | 25% | 30% | 35% |
| $5M+ | 30% | 35% | 40% |

> **Note:** These are illustrative tiers. Actual discount rates are configurable in `config/discount_tiers.yml` and should reflect your negotiated terms.

---

## The "Sweet Spot" Recommendation

The system finds the **optimal scenario** by balancing two goals:
1. **Maximize savings** (higher discount = more money saved)
2. **Maintain utilization >= 85%** (don't overpay for unused capacity)

The algorithm classifies each scenario:

| Status | Meaning | Recommendation |
|--------|---------|----------------|
| **ON TRACK** | Contract well-sized for consumption | Optimal - keep this structure |
| **EARLY EXHAUSTION** | Will use up commitment before contract ends | Consider longer duration for higher discount |
| **EXTENDED** | Won't use full commitment | Risk - reduce commitment or increase usage |

---

## Key Business Insights Provided

### 1. Exhaustion Date Prediction
> "At your current pace, you'll exhaust your $100K contract by July 29, 2026"

The Prophet ML model analyzes your historical consumption patterns and projects forward to predict exactly when your contract commitment will be fully consumed.

### 2. Savings Comparison
> "A 2-year contract would save $6,435 more than your current 1-year deal"

The What-If simulator calculates the dollar impact of different contract structures, showing you the incremental value of each option.

### 3. Duration Incentive Analysis
> "If you extend to 3 years, you unlock 18% discount instead of 10%"

Longer commitments unlock higher discount tiers. The system shows you exactly what additional discount you could earn by extending your contract term.

### 4. Break-Even Analysis
> "You need to consume at least $85,000 to justify your current commitment"

The break-even calculation tells you the minimum consumption required to make a commitment worthwhile:

```
Break-even Consumption = Commitment Amount / (1 - Discount Rate)
```

If your projected consumption falls below this threshold, you're paying for capacity you won't use.

---

## Strategic Decision Framework

The tool helps answer these critical business questions:

| Question | How the System Helps |
|----------|----------------------|
| "Should we increase our commitment?" | Compares savings at different commitment levels |
| "Should we sign a longer contract?" | Shows additional discount from 2-year or 3-year terms |
| "Are we over-committed?" | Predicts if you'll exhaust contract or leave money on the table |
| "What's our optimal contract size?" | Identifies the "sweet spot" where savings are maximized without waste |

---

## Understanding the Dashboard

### Executive Summary Page
- Total contract value and consumption to date
- Pace status (ahead/behind/on-track)
- Days remaining in contract

### Contract Burndown Page
- **Historical Consumption** (gold line): What you've actually spent
- **ML Forecast** (red line): Where Prophet predicts you're heading
- **Contract Commitment** (blue line): Your total commitment ceiling
- **Exhaustion Date** (white vertical line): When forecast crosses commitment

### What-If Analysis Page
- Scenario comparison table with all discount levels
- Savings projections for each scenario
- Sweet spot recommendation highlighted
- "Longer Duration Opportunities" showing incentive to extend

---

## Key Formulas

| Metric | Formula |
|--------|---------|
| **Effective Discount** | `1 - (actual_cost / list_cost)` |
| **Break-even Consumption** | `commitment / (1 - discount_rate)` |
| **Savings vs On-Demand** | `list_total - MAX(discounted_total, commitment)` |
| **Utilization %** | `discounted_consumption / commitment * 100` |
| **Sweet Spot** | `MAX(savings) WHERE utilization >= 85%` |

---

## Practical Example

**Current Situation:**
- Contract: $100,000 / 1-year
- Current discount: 10%
- Consumption pace: On track to exhaust by July 2026 (early)

**What-If Analysis Shows:**

| Scenario | Discount | Savings to Date | Exhaustion | Days Extended |
|----------|----------|-----------------|------------|---------------|
| Baseline (No Discount) | 0% | $0 | Jul 29, 2026 | - |
| 5% Discount | 5% | $2,145 | Aug 18, 2026 | +20 |
| 10% Discount (Current) | 10% | $4,290 | Sep 8, 2026 | +41 |
| **15% (If 2yr commit)** | 15% | $6,435 | Sep 29, 2026 | +62 |
| **18% (If 3yr commit)** | 18% | $7,722 | Oct 13, 2026 | +76 |

**Recommendation:** Since consumption will exhaust the contract early, consider a longer-term commitment to unlock higher discounts. A 2-year contract at 15% would save an additional $2,145 compared to the current 1-year deal.

---

## Bottom Line

This system transforms contract negotiation from guesswork into data-driven decision-making:

- **Historical data** tells you where you've been
- **ML forecasting** tells you where you're going
- **What-if simulation** tells you what deal you should negotiate

**The goal: maximize discount benefits while ensuring you actually use what you pay for.**

---

## Related Documentation

- [README.md](../README.md) - Full system documentation
- [USER_GUIDE.md](user-guide/USER_GUIDE.md) - Detailed usage instructions
- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - How to configure contracts and discount tiers

---

*Document generated: 2026-02-08*
*Version: 1.10.0*
