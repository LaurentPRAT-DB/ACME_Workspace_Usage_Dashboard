# Account Monitor - Contract Optimization Strategy

**For: FinOps, Procurement, Finance**

How to use the Account Monitor to optimize your Databricks contracts.

---

## The Goal

Get the best value from your Databricks investment:

```
Optimal Contract = Maximum Discount + Full Utilization
```

**Overspending:** Exhaust contract early → Pay on-demand rates (0% discount)
**Underspending:** Unused commitment → Wasted money
**Optimal:** Use 95-100% of commitment → Full discount benefit

---

## Understanding Databricks Pricing

### How It Works

1. **On-Demand:** Pay list price, no commitment, no discount
2. **Committed:** Upfront commitment, volume discount

### Discount Factors

| Factor | Impact |
|--------|--------|
| Commitment Size | Larger = higher discount |
| Duration | Longer = higher discount |
| Cloud Provider | May vary by provider |
| Negotiation | Additional discounts possible |

### Typical Discount Ranges

| Commitment | 1 Year | 2 Year | 3 Year |
|------------|--------|--------|--------|
| $100K-250K | 8-12% | 10-15% | 12-18% |
| $250K-500K | 10-15% | 13-18% | 15-20% |
| $500K-1M | 13-18% | 16-20% | 18-22% |
| $1M+ | 15-20% | 18-22% | 20-25% |

*Actual rates vary. Use What-If Analysis for your specific scenarios.*

---

## Using Account Monitor for Optimization

### Step 1: Understand Current State

Open **Executive Summary** page:

| Metric | What It Tells You |
|--------|-------------------|
| Total Consumed | Actual spending to date |
| Consumed % | Pace of consumption |
| Days Remaining | Time left in contract |
| Pace Status | On track or not |

**Key Question:** Are you on track to use your full commitment?

### Step 2: Review Historical Patterns

Open **Contract Burndown** page:

- Look at the gold line (historical consumption)
- Is it steady, growing, or declining?
- Any seasonal patterns?

**Key Question:** Is consumption predictable or volatile?

### Step 3: Analyze Forecast

On **Contract Burndown** page:

- Look at the red line (ML forecast)
- When does it cross the commitment line?
- What's the confidence range?

**Key Question:** Will you under-spend or over-spend?

### Step 4: Explore Scenarios

Open **What-If Analysis** page:

- Compare different discount levels
- Find the sweet spot
- Consider duration extensions

**Key Question:** What's the optimal discount for your usage pattern?

---

## Scenario Analysis Framework

### Scenario 1: Under-Consumption

**Situation:** Forecast shows you'll use only 70% of commitment

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| Reduce next commitment | Right-size to actual usage | May lose discount tier |
| Increase usage | Get value from existing commitment | May not be feasible |
| Use for new projects | Full utilization | Requires planning |

**Recommendation:** If consistent under-consumption, consider smaller commitment with shorter duration for flexibility.

### Scenario 2: Over-Consumption

**Situation:** Forecast shows exhaustion 3 months early

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| Add credits mid-term | Cover shortfall | May not get best rate |
| Negotiate higher next contract | Better rate for higher volume | Larger commitment |
| Optimize usage | Reduce spending | May impact productivity |

**Recommendation:** If growth is genuine, negotiate larger commitment with better discount.

### Scenario 3: Perfect Tracking

**Situation:** On track for 95-100% utilization

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| Renew same commitment | Predictable, proven | May miss growth |
| Slight increase (10-20%) | Room for growth | Slightly higher commitment |
| Lock longer term | Better discount | Less flexibility |

**Recommendation:** Consider 2-3 year term to lock in rates.

---

## The Sweet Spot Analysis

### What Is the Sweet Spot?

The discount level that maximizes savings while ensuring you use at least 85% of your commitment.

### Example Calculation

```
Current Usage Pattern: $400K/year

Scenario A: $450K commitment at 15% discount
- Effective cost: $382,500
- Predicted usage: $400K → Would need +5% growth
- Utilization: 89% (good)
- Savings: $67,500

Scenario B: $500K commitment at 18% discount
- Effective cost: $410,000
- Predicted usage: $400K
- Utilization: 80% (risky)
- Savings: $90,000 (if fully used)
- Waste if not used: ~$82,000

Scenario C: $400K commitment at 12% discount
- Effective cost: $352,000
- Predicted usage: $400K
- Utilization: 100% (perfect)
- Savings: $48,000

Sweet Spot: Scenario A
- Good savings ($67.5K)
- Reasonable utilization risk (89%)
- Room for moderate growth
```

### Sweet Spot Rules

1. **Minimum 85% utilization** - Don't commit more than you'll likely use
2. **Growth buffer** - If growing, allow 10-15% headroom
3. **Duration trade-off** - Longer term = better rate, but more lock-in risk

---

## Negotiation Preparation

### Data to Bring

1. **Historical consumption** - From Contract Burndown
2. **Consumption trend** - Growing, stable, or declining?
3. **Forecast accuracy** - Prophet predictions vs. actuals
4. **Utilization rate** - What % of past contracts used?

### Questions to Ask

1. What discount tiers are available for my commitment level?
2. What additional discount for multi-year terms?
3. Is there flexibility to add credits mid-term?
4. What happens to unused commitment at end of term?

### Leverage Points

| Your Situation | Leverage |
|----------------|----------|
| Growing rapidly | "I'll commit more if rate improves" |
| Consistent usage | "Low risk customer, predictable revenue" |
| Multi-cloud | "I could shift workloads to other provider" |
| Long-term partner | "Been with you X years, looking for loyalty pricing" |

---

## Red Flags to Watch

### In Your Data

| Red Flag | Concern |
|----------|---------|
| High variance in monthly spend | Hard to predict, risky to commit high |
| Declining trend | Don't over-commit |
| Many cost spikes | Unpredictable usage patterns |
| Low weekend usage | Potential to optimize further |

### In Contract Terms

| Red Flag | Concern |
|----------|---------|
| No mid-term adjustment | Stuck if needs change |
| Use-it-or-lose-it | Lose value of unused credits |
| Auto-renewal at same rate | May miss better deals |
| Price increase clauses | Budget uncertainty |

---

## Optimization Checklist

Before signing a new contract:

- [ ] Reviewed past 12 months consumption?
- [ ] Analyzed Prophet forecast for next 12 months?
- [ ] Explored What-If scenarios for different discounts?
- [ ] Identified sweet spot discount level?
- [ ] Considered multi-year vs. single year?
- [ ] Factored in known growth plans?
- [ ] Left appropriate buffer for uncertainty?
- [ ] Compared to on-demand alternative?
- [ ] Reviewed contract flexibility clauses?
- [ ] Documented rationale for final decision?

---

## ROI Calculation

### Example: Contract Optimization ROI

**Before Account Monitor:**
- $500K commitment, 10% discount
- Actual usage: $420K (84% utilization)
- Effective savings: $50K
- Wasted: $80K (unused commitment)

**With Account Monitor:**
- Identified true usage pattern: ~$420K
- Negotiated $450K commitment, 12% discount
- Actual usage: $420K (93% utilization)
- Effective savings: $54K
- Wasted: $30K

**Net Improvement:**
- Reduced waste: $50K
- Better rate on used amount: $4K
- **Total annual value: $54K**

---

## Related Documents

| Document | Description |
|----------|-------------|
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Business overview |
| [DASHBOARD_OVERVIEW.md](DASHBOARD_OVERVIEW.md) | Visual dashboard guide |

---

*Last updated: February 2026*
