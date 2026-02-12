# Account Monitor - Executive Summary

**For: Business Stakeholders, Finance, Executives**

---

## What Is This?

The Account Monitor is a tool that helps you **get the best value from your Databricks contract**. It tracks how much you're spending, predicts when your contract will run out, and recommends the optimal discount level for your next renewal.

---

## The Business Problem

When you sign a Databricks contract, you commit to spending a certain amount (e.g., $500,000 over 2 years). Two things can go wrong:

| Problem | Impact |
|---------|--------|
| **Overspending** | You exhaust your contract early and pay higher on-demand rates |
| **Underspending** | You waste unused commitment - money left on the table |

**The Goal:** Consume exactly 100% of your contract by the end date - no waste, no overage.

---

## What the System Does

### 1. Tracks Consumption in Real-Time

See exactly how much of your contract you've used:

```
Contract: $500,000 (Jan 2026 - Dec 2026)
Consumed: $180,000 (36%)
Remaining: $320,000
Days Left: 245
```

### 2. Predicts When You'll Run Out

Using machine learning, the system forecasts your future spending and tells you:

- **When** your contract will be exhausted
- **How confident** that prediction is
- **Whether you're on track** or need to adjust

```
Prediction: Contract exhausts August 15, 2026
Status: OVER PACE - consuming 20% faster than expected
Action: Consider reducing usage or adding credits
```

### 3. Recommends Optimal Discounts

The What-If simulator shows you:

- What discount levels are available based on your commitment size
- How much you'd save with each discount level
- Whether extending your contract term unlocks better rates

```
Current: 1-year contract, 10% discount
Option: Extend to 3-year, get 18% discount
Savings: $45,000 over contract term
```

---

## The Dashboard

The system provides a 5-page dashboard for different perspectives:

| Page | What You See | When to Use |
|------|--------------|-------------|
| **Executive Summary** | Total contract value, consumption, remaining budget | Quick status check |
| **Contract Burndown** | Consumption trend with ML forecast | Monthly reviews |
| **Weekly Operations** | Anomalies, top spenders, pace status | Weekly meetings |
| **Monthly Summary** | MoM trends, product breakdown | Monthly reporting |
| **What-If Analysis** | Discount scenarios and recommendations | Contract renewals |

---

## Key Metrics Explained

### Pace Status

| Status | Meaning | Action |
|--------|---------|--------|
| **ON PACE** | Consumption matches time elapsed | None needed |
| **ABOVE PACE** | Consuming 10-20% faster | Monitor closely |
| **OVER PACE** | Consuming >20% faster | Reduce usage or add credits |
| **UNDER PACE** | Consuming >20% slower | Find ways to use commitment |

### Exhaustion Date

The predicted date when your contract will be fully consumed based on current spending patterns.

- **Before contract end date** = You're overspending
- **After contract end date** = You're underspending

### Sweet Spot

The discount level that provides maximum savings while still consuming your full commitment. Higher discounts = more savings, but only if you actually use the capacity.

---

## Business Outcomes

### Without Account Monitor

- Contracts exhaust unexpectedly, causing budget surprises
- Unused commitment is lost at contract end
- Renewal negotiations lack data-driven insights
- Cost spikes go unnoticed until month-end reports

### With Account Monitor

- **Real-time visibility** into contract consumption
- **Predictive alerts** before problems occur
- **Data-driven negotiations** with exact usage patterns
- **Automated monitoring** catches anomalies immediately

---

## Typical Use Cases

### Monthly Business Review

1. Open **Executive Summary** page
2. Check total consumed vs. budget remaining
3. Review pace status (on track?)
4. Note any contracts flagged for attention

### Contract Renewal Planning

1. Open **What-If Analysis** page
2. Review current consumption pattern
3. Compare discount scenarios
4. Identify optimal contract structure
5. Present data to vendor negotiations

### Weekly Operations Check

1. Open **Weekly Operations** page
2. Review any cost spikes (anomalies)
3. Check which teams/workspaces are top spenders
4. Ensure no runaway costs

---

## ROI Example

**Scenario:** $500,000 annual contract

| Without Monitor | With Monitor |
|-----------------|--------------|
| Discovered over-pace 60 days late | Alerted within 7 days |
| Paid $50,000 overage at list price | Adjusted early, stayed within contract |
| Renewed at same 10% discount | Negotiated 15% based on usage data |
| **Cost: $550,000** | **Cost: $425,000** |
| | **Savings: $125,000** |

---

## Getting Started

### For Business Users

1. **Bookmark the dashboard** - Ask your admin for the URL
2. **Check it weekly** - Review the Executive Summary page
3. **Before renewals** - Review What-If Analysis for negotiation data

### For Finance Teams

1. **Set up monthly reports** - Use Monthly Summary page for reporting
2. **Configure alerts** - Ask admin to set up exhaustion warnings
3. **Export data** - Dashboard data can be exported for financial systems

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Contract Optimization Strategy](CONTRACT_OPTIMIZATION_STRATEGY.md) | Detailed business strategy guide |
| [Dashboard Overview](DASHBOARD_OVERVIEW.md) | Visual guide to each dashboard page |

---

*Last updated: February 2026*
