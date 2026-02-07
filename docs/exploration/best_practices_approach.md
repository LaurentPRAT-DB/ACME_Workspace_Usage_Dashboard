# What-If Discount Simulation: Best Practices Research

## Executive Summary

This document captures industry best practices for financial what-if simulations in cloud consumption contexts, focusing on commit discount comparisons, scenario modeling, and ROI analysis approaches.

---

## 1. Cloud Vendor Commit Discount Structures

### 1.1 AWS Savings Plans

**Commitment Types:**
- **Compute Savings Plans**: Flexible across EC2, Fargate, Lambda
- **EC2 Instance Savings Plans**: Specific instance family/region
- **SageMaker Savings Plans**: ML workload specific

**Typical Discount Tiers:**
| Term Length | Payment Option | Typical Discount |
|------------|----------------|------------------|
| 1 Year | No Upfront | 20-30% |
| 1 Year | Partial Upfront | 30-40% |
| 1 Year | All Upfront | 35-42% |
| 3 Year | No Upfront | 40-50% |
| 3 Year | Partial Upfront | 50-60% |
| 3 Year | All Upfront | 55-72% |

**Key Pattern**: Discounts scale with commitment length and upfront payment.

### 1.2 Azure Reserved Instances

**Commitment Types:**
- **Reserved Virtual Machine Instances**: VM-specific
- **Reserved Capacity**: SQL, Cosmos DB, Storage
- **Azure Savings Plan**: Flexible compute (newer model)

**Typical Discount Tiers:**
| Term | Scope | Typical Discount |
|------|-------|------------------|
| 1 Year | Single Subscription | 20-35% |
| 1 Year | Shared/Management Group | 25-40% |
| 3 Year | Single Subscription | 45-60% |
| 3 Year | Shared/Management Group | 50-72% |

### 1.3 Google Cloud Committed Use Discounts (CUDs)

**Commitment Types:**
- **Resource-based CUDs**: vCPUs and memory
- **Spend-based CUDs**: Flexible dollar commitment

**Typical Discount Tiers:**
| Term | Commitment Type | Typical Discount |
|------|-----------------|------------------|
| 1 Year | Resource-based | 20-37% |
| 1 Year | Spend-based | 20-28% |
| 3 Year | Resource-based | 52-70% |
| 3 Year | Spend-based | 40-52% |

### 1.4 Databricks Commit Discounts

**Commitment Structure:**
- Annual or multi-year dollar commitments
- Tiered discounts based on total commitment value
- Custom enterprise agreements

**Typical Discount Tiers (Industry Estimates):**
| Annual Commitment | Typical Discount |
|-------------------|------------------|
| $100K - $250K | 5-10% |
| $250K - $500K | 10-15% |
| $500K - $1M | 15-25% |
| $1M - $5M | 25-35% |
| $5M+ | 35-45%+ |

**Note**: Actual Databricks discounts vary by negotiation, region, and relationship.

---

## 2. Scenario Modeling Best Practices

### 2.1 Core Scenario Types

**Standard Scenarios to Model:**

1. **Baseline (Current State)**
   - Pay-as-you-go pricing
   - No commitment
   - Full flexibility, zero discount

2. **Conservative Commit**
   - 70-80% of projected usage
   - Lower risk of over-commitment
   - Moderate savings

3. **Aggressive Commit**
   - 90-100% of projected usage
   - Higher risk if usage drops
   - Maximum savings

4. **Custom Scenario**
   - User-defined commitment level
   - Allows exploration of specific proposals

### 2.2 Key Variables to Model

| Variable | Description | Impact |
|----------|-------------|--------|
| **Commitment Amount** | Total dollar commitment | Primary driver |
| **Term Length** | 1, 2, or 3 years | Affects discount tier |
| **Usage Variability** | Historical std deviation | Risk factor |
| **Growth Rate** | Projected usage growth | Future cost impact |
| **Discount Tier** | Based on commitment level | Savings calculation |

### 2.3 Time-Series Considerations

**Best Practice**: Project scenarios over the full commitment term

```
Month 1-12:  Show monthly projected costs vs. commitment
Month 13-24: (for multi-year) Show compounding effects
Month 25-36: (for 3-year) Show long-term value
```

**Visualization Pattern**:
- X-axis: Time (months)
- Y-axis: Cumulative cost
- Lines: Each scenario as separate series

---

## 3. Sensitivity Analysis Techniques

### 3.1 Key Sensitivity Parameters

**Usage Variance Scenarios:**
| Scenario | Usage Level | Description |
|----------|-------------|-------------|
| Pessimistic | -20% | Usage significantly below forecast |
| Conservative | -10% | Slight underutilization |
| Expected | 0% | Forecast accuracy |
| Optimistic | +10% | Slight growth beyond forecast |
| Aggressive | +20% | Significant growth |

### 3.2 Tornado Diagram Approach

Show which variables have the most impact on savings:

```
Variable Impact on Savings (High to Low):
1. Commitment Level     |===============================|
2. Discount Tier        |=========================|
3. Usage Growth Rate    |===================|
4. Term Length          |================|
5. Payment Timing       |==========|
```

### 3.3 Monte Carlo Simulation (Advanced)

For sophisticated users, simulate thousands of scenarios:
- Randomly vary usage within historical bounds
- Calculate savings distribution
- Show confidence intervals (P10, P50, P90)

**Simplified Alternative**: Show best/expected/worst case scenarios

---

## 4. Breakeven Analysis Presentation

### 4.1 Key Metrics to Display

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Breakeven Point** | Usage level where commit equals PAYG | Commitment / Discount Rate |
| **Breakeven Utilization** | % of commitment that must be used | 1 - Discount Rate |
| **Risk Threshold** | Usage below which you lose money | Commitment * Breakeven Utilization |
| **Safety Margin** | Buffer above breakeven | Projected Usage - Breakeven Point |

### 4.2 Visual Breakeven Presentation

**Recommended Chart**: Breakeven waterfall or gauge

```
[================|====X====|================]
0%              60%       85%             120%
                 ^         ^
            Breakeven   Projected
               Point      Usage

Legend:
- Red Zone (0-60%): Overpaying vs PAYG
- Yellow Zone (60-85%): Savings but below projection
- Green Zone (85-120%): Expected savings realized
```

### 4.3 Breakeven Table Format

| Scenario | Commitment | Discount | Breakeven | Projected | Margin |
|----------|------------|----------|-----------|-----------|--------|
| Conservative | $500K | 15% | $425K | $650K | +$225K |
| Moderate | $700K | 22% | $546K | $650K | +$104K |
| Aggressive | $800K | 25% | $600K | $650K | +$50K |

---

## 5. ROI/Savings Analysis Presentation

### 5.1 Key Financial Metrics

**Primary Metrics:**
- **Total Savings**: PAYG Cost - Committed Cost
- **Savings Percentage**: Total Savings / PAYG Cost * 100
- **Effective Rate**: Committed Cost / Usage Units
- **ROI**: (Savings - Risk Cost) / Commitment

**Risk-Adjusted Metrics:**
- **Risk-Adjusted Savings**: Account for usage variability
- **Confidence Level**: Probability of achieving projected savings
- **Downside Risk**: Maximum potential loss if usage drops

### 5.2 Presentation Patterns

**Pattern 1: Side-by-Side Comparison Table**
```
                    | Pay-As-You-Go | Committed | Savings |
---------------------------------------------------------
Year 1 Cost         | $650,000      | $500,000  | $150,000 |
Year 2 Cost         | $715,000      | $500,000  | $215,000 |
Year 3 Cost         | $786,500      | $500,000  | $286,500 |
---------------------------------------------------------
3-Year Total        | $2,151,500    | $1,500,000| $651,500 |
3-Year Savings %    |               |           | 30.3%    |
```

**Pattern 2: Savings Waterfall Chart**
```
PAYG Cost: $650K
    |
    v
[-$97.5K] 15% Volume Discount
    |
    v
[-$32.5K] Annual Commit Bonus
    |
    v
[-$20K] Early Payment Credit
    |
    v
Final Cost: $500K (23% Total Savings)
```

**Pattern 3: Cumulative Comparison Over Time**
```
Cumulative Cost Over Time
^
|      PAYG .......*****
|           ....***
|       ....**
|    ..**
| ..**  Committed ----*****
|**----****
|----**
+-------------------------> Time
     Q1  Q2  Q3  Q4  Year 2
```

### 5.3 Risk Communication

**Best Practice**: Always show both upside and downside

| Scenario | Probability | Savings | Risk |
|----------|------------|---------|------|
| Best Case | 20% | $200K | $0 |
| Expected | 60% | $150K | $0 |
| Worst Case | 20% | $50K | $25K overpay |

---

## 6. User Interface Patterns

### 6.1 Interactive Simulation Controls

**Recommended Inputs:**
1. **Slider**: Commitment amount (min/max based on usage)
2. **Dropdown**: Term length (1, 2, 3 years)
3. **Toggle**: Show/hide risk scenarios
4. **Radio Buttons**: Pre-defined scenarios (Conservative/Moderate/Aggressive)

### 6.2 Progressive Disclosure

**Level 1 (Summary):**
- Total projected savings
- Recommended commitment level
- Key risk indicator

**Level 2 (Details):**
- Monthly breakdown
- Scenario comparison table
- Breakeven analysis

**Level 3 (Advanced):**
- Sensitivity analysis
- Custom scenario builder
- Export to spreadsheet

### 6.3 Visual Hierarchy

```
+--------------------------------------------------+
| HEADLINE: "Recommended: $500K commit saves $150K" |
+--------------------------------------------------+
|                                                  |
| [Chart: Scenario Comparison Over Time]           |
|                                                  |
+--------------------------------------------------+
| SUMMARY TABLE                                    |
| Scenario | Commit | Savings | Risk | Recommend  |
+--------------------------------------------------+
| [Show More Details] [Download Report]            |
+--------------------------------------------------+
```

---

## 7. Industry Tool Examples

### 7.1 AWS Cost Explorer Savings Plans Recommendations

**Features:**
- Historical usage analysis
- Automatic recommendation based on coverage target
- Hourly commitment granularity
- Before/after cost comparison

**Key Pattern**: Uses coverage % as primary input (e.g., "Cover 80% of usage")

### 7.2 Azure Cost Management + Billing

**Features:**
- Reservation recommendations by service
- Utilization tracking
- Cost anomaly detection
- Break-even calculator

**Key Pattern**: Shows utilization risk prominently

### 7.3 Third-Party Tools (CloudHealth, Spot.io, etc.)

**Common Features:**
- Multi-cloud support
- What-if scenario builder
- Automated recommendations
- Historical trend analysis

**Key Pattern**: Often include "confidence score" for recommendations

---

## 8. Recommendations for Databricks Implementation

### 8.1 Essential Features (MVP)

1. **Scenario Comparison View**
   - Current (no commit) vs. proposed commit
   - Show savings and risk clearly

2. **Breakeven Calculator**
   - Visual indicator of safety margin
   - Clear "risk zone" indication

3. **Time-Series Projection**
   - Monthly costs over commitment term
   - Cumulative savings visualization

### 8.2 Enhanced Features (Phase 2)

1. **Multiple Scenario Comparison**
   - Conservative/Moderate/Aggressive presets
   - Custom scenario builder

2. **Sensitivity Analysis**
   - Usage variance impact
   - Growth rate scenarios

3. **Risk Scoring**
   - Based on historical usage variance
   - Confidence interval display

### 8.3 Advanced Features (Phase 3)

1. **ML-Powered Recommendations**
   - Optimal commit level suggestion
   - Confidence scoring

2. **What-If History**
   - Save and compare scenarios
   - Track recommendation accuracy

3. **Alert Integration**
   - Notify when approaching commitment
   - Under-utilization warnings

---

## 9. Key Takeaways

### Design Principles

1. **Lead with Savings**: Show potential value prominently
2. **Quantify Risk**: Never hide downside scenarios
3. **Enable Exploration**: Let users adjust parameters interactively
4. **Show Confidence**: Indicate certainty of projections
5. **Progressive Disclosure**: Don't overwhelm with details upfront

### Common Discount Tier Structure

Most cloud vendors follow similar patterns:
- **5-15%**: Entry-level commits ($100K-$500K)
- **15-25%**: Mid-tier commits ($500K-$2M)
- **25-35%**: Enterprise commits ($2M-$10M)
- **35%+**: Strategic partnerships ($10M+)

### Breakeven Rule of Thumb

For a discount of X%, breakeven utilization is approximately (100-X)%:
- 20% discount = 80% utilization to break even
- 30% discount = 70% utilization to break even
- 40% discount = 60% utilization to break even

---

## 10. References and Further Reading

### Cloud Provider Documentation
- AWS Savings Plans: https://aws.amazon.com/savingsplans/
- Azure Reserved Instances: https://learn.microsoft.com/azure/cost-management-billing/reservations/
- GCP Committed Use Discounts: https://cloud.google.com/docs/cuds

### Industry Resources
- FinOps Foundation: https://www.finops.org/
- Cloud Cost Optimization Patterns: Industry best practices
- SaaS Financial Modeling: Scenario analysis frameworks

---

*Document created: 2026-02-07*
*Research focus: Cloud commit discount simulations for Databricks contract monitoring*
