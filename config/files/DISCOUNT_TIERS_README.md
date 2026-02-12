# Databricks Discount Tier Alternatives

This directory contains three alternative discount tier configurations based on real-world Databricks pricing research and customer negotiation data from 2024-2025.

## Quick Comparison

| Tier Structure | Best For | Total Discount Range | Complexity |
|---|---|---|---|
| **Alternative 1: Market-Aligned** | Default/Realistic scenarios | 10% - 50% | Simple |
| **Alternative 2: Aggressive** | Competitive displacement | 12% - 55% | Simple |
| **Alternative 3: Stackable** | Complex negotiations | 8% - 68%+ | Moderate |

---

## Alternative 1: Market-Aligned Tiers (RECOMMENDED DEFAULT)

**File:** `discount_tiers_alternative1_market_aligned.yml`

### Overview
Conservative but realistic discount structure based on documented Azure Databricks discounts and verified customer reports from Vendr negotiation database.

### Discount Ranges
| Commitment | 1-Year | 2-Year | 3-Year |
|---|---|---|---|
| $50K - $100K | 10% | 15% | 20% |
| $100K - $250K | 15% | 20% | 25% |
| $250K - $500K | 20% | 27% | 33% |
| $500K - $1M | 25% | 32% | 37% |
| $1M - $5M | 30% | 37% | 42% |
| $5M+ | 35% | 42% | 50% |

### When to Use
- Default configuration for most organizations
- Conservative budgeting and forecasting
- Standard enterprise negotiations
- Aligns with Azure's documented 33-37% discounts

### Key Features
- Entry-level at 10% (more realistic than 5%)
- Mid-tiers match documented Azure discounts
- Top tier reaches 50% for mega-deals ($5M+, 3-year)
- Based on real customer reports showing 14-32% cross-SKU discounts

---

## Alternative 2: Aggressive/Competitive Tiers

**File:** `discount_tiers_alternative2_aggressive.yml`

### Overview
Higher baseline discounts for organizations with strong negotiating leverage, competitive displacement scenarios, or strategic partnerships.

### Discount Ranges
| Commitment | 1-Year | 2-Year | 3-Year |
|---|---|---|---|
| $50K - $100K | 12% | 18% | 22% |
| $100K - $250K | 18% | 25% | 30% |
| $250K - $500K | 25% | 32% | 38% |
| $500K - $1M | 30% | 37% | 43% |
| $1M - $5M | 35% | 42% | 48% |
| $5M+ | 40% | 47% | 55% |

### When to Use
- Competitive displacement (switching from Snowflake, AWS EMR)
- High-growth commitments (2x+ year-over-year)
- Multi-cloud strategies (AWS + Azure + GCP)
- Strategic partnership negotiations
- Organizations with significant bargaining power

### Key Features
- Reflects 15-20% competitive displacement bonuses
- Accounts for growth incentives
- Suitable for multi-cloud commitments
- Top tier reaches 55% with all levers pulled

---

## Alternative 3: Base Tiers + Stackable Incentives

**File:** `discount_tiers_alternative3_stackable.yml`

### Overview
Modular approach with conservative base rates plus documented stackable incentive programs. Mimics real Databricks sales processes.

### Base Discount Ranges
| Commitment | 1-Year | 2-Year | 3-Year |
|---|---|---|---|
| $50K - $100K | 8% | 12% | 15% |
| $100K - $250K | 12% | 18% | 22% |
| $250K - $500K | 18% | 24% | 30% |
| $500K - $1M | 22% | 30% | 35% |
| $1M - $5M | 28% | 35% | 40% |
| $5M+ | 33% | 40% | 45% |

### Stackable Incentive Programs

Add these bonuses ON TOP OF base rates:

| Incentive Program | Bonus | Requirements |
|---|---|---|
| **Multi-Cloud Commitment** | +5% to +10% | Commit to 2-3 cloud providers |
| **Competitive Displacement** | +10% to +20% | Switch from Snowflake, AWS EMR, etc. |
| **High Growth Commitment** | +5% to +8% | 2x-3x+ year-over-year growth |
| **Annual Prepayment** | +3% to +5% | Pay annually vs quarterly |
| **Support Fee Reduction** | +5% to +10% | Reduce from 15% to 10-12% |
| **New Use Case Expansion** | +5% to +20% | Add SQL, DLT, ML workloads |

### Example Calculations

**Example 1:** $750K, 2-year, competitive displacement
- Base: 30% + Competitive: 15% + Prepay: 4% = **49% total**

**Example 2:** $2M, 3-year, multi-cloud + growth
- Base: 40% + Multi-cloud: 10% + Growth: 8% = **58% total**

**Example 3:** $8M, 3-year, strategic mega-deal
- Base: 45% + Multi-cloud: 10% + Competitive: 20% + Growth: 8% = **83% total** (capped at ~70% realistic maximum)

### When to Use
- Complex multi-faceted negotiations
- Need to model different incentive combinations
- Want to show "what if we add X incentive?"
- Educational purposes (show how discounts are built)
- Organizations that qualify for multiple programs

### Key Features
- Most flexible configuration
- Reflects real negotiation processes
- Based on actual customer reports with stacked incentives
- Can model realistic scenarios from 15% to 68%+
- Includes non-discount perks (credits, tickets, services)

---

## Data Sources

All three alternatives are based on:

1. **Azure Databricks Official Documentation**
   - Documented 33-37% discounts for 1-3 year commits
   - Source: cloudzero.com, Azure pricing pages

2. **Vendr Customer Negotiation Database (2024-2025)**
   - Real customer reports: "14% cross-SKU discount achieved"
   - "By adding new use cases, increased SQL/DLT from 0% to 20%"
   - "3-year agreement increased discount by ~15%"
   - Support costs reduced from 15% to 10-12%

3. **Industry Pricing Analysis**
   - CloudChipr: "12-month commitment might yield 20% discount"
   - ChaosGenius: "Commitment-based discounts available"
   - Multiple sources confirming 20-40% standard range

4. **Customer-Reported Deals**
   - "$100K in free AWS credits" for strategic deals
   - "Free Data + AI Summit tickets" as negotiation value-add
   - "Significant growth over term increased discount by ~15%"

---

## Recommendation by Use Case

### For Demo/Testing Projects
→ Use **Alternative 1** (Market-Aligned)
- Most realistic default
- Easy to explain
- Conservative budgeting

### For Sales Teams / What-If Analysis
→ Use **Alternative 2** (Aggressive) or **Alternative 3** (Stackable)
- Alternative 2: Simple comparison of standard vs competitive rates
- Alternative 3: Show how discounts build up through negotiation

### For Enterprise Procurement
→ Use **Alternative 3** (Stackable)
- Most accurate model of real negotiations
- Can test different incentive combinations
- Educational for stakeholders

### For Academic/Research
→ Use all three for comparison
- Show range of possible outcomes
- Demonstrate negotiation leverage impact

---

## Implementation

Replace the default `discount_tiers.yml` in your config directory:

```bash
# Option 1: Use Market-Aligned (recommended default)
cp discount_tiers_alternative1_market_aligned.yml config/discount_tiers.yml

# Option 2: Use Aggressive/Competitive
cp discount_tiers_alternative2_aggressive.yml config/discount_tiers.yml

# Option 3: Use Base + Stackable
cp discount_tiers_alternative3_stackable.yml config/discount_tiers.yml
```

Then redeploy and re-run setup:
```bash
databricks bundle deploy --profile YOUR_PROFILE
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

---

## Additional Notes

### Realistic Maximum Discounts
While Alternative 3 shows theoretical totals of 68%+, realistic maximum achieved discounts typically cap at:
- **Standard deals:** 20-40%
- **Competitive deals:** 35-50%
- **Strategic mega-deals:** 50-70%

### Support Fee Considerations
Support fees (typically 15% of usage commitment) are separate from DBU discounts but can be negotiated:
- Standard: 15%
- Negotiated: 12% (common)
- Strategic: 10% (achievable for large deals)
- Reduction represents 3-5% effective additional savings

### Non-Discount Value
Don't overlook non-discount negotiation value:
- AWS/Azure/GCP credits: $50K-$100K reported
- Professional services: $25K-$50K
- Training and certification
- Conference tickets ($2K-$5K value)
- Dedicated account team

---

## Questions?

For questions about these discount structures or help customizing for your organization, please refer to:
- Databricks official pricing: https://www.databricks.com/product/pricing
- Vendr marketplace data: https://www.vendr.com/marketplace/databricks
- Cloud provider specific docs (Azure, AWS, GCP)
