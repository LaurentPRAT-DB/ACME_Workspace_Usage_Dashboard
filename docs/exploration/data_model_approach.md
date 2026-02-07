# Data Model Approach: Discount Scenario Simulation

## Research Summary

This document explores the schema changes needed to support "what-if" discount scenario simulations for Databricks commit contracts.

---

## 1. Current Data Model Analysis

### Existing Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `contracts` | Core contract data | contract_id, total_value, start_date, end_date, status |
| `contract_burndown` | Daily consumption tracking | contract_id, usage_date, daily_cost, cumulative_cost, commitment |
| `contract_forecast` | Prophet ML predictions | contract_id, forecast_date, predicted_cumulative, exhaustion_date_p50 |
| `forecast_model_registry` | Trained model metadata | model_id, contract_id, mape, is_active |
| `dashboard_data` | Raw usage data | usage_date, account_id, actual_cost, sku_name |

### Key Relationships

```
contracts (1) ──────────────────────────────────► (N) contract_burndown
    │                                                      │
    │                                                      │
    └────────────────────────────► (N) contract_forecast   │
                                          │                │
                                          ▼                ▼
                                    (joins for dashboard visualization)
```

### Important Observations

1. **contract_burndown** is regenerated from `contracts` + `dashboard_data` via SQL
2. **contract_forecast** stores Prophet predictions with model versioning
3. Forecasts include confidence intervals (p10, p50, p90) for exhaustion dates
4. The `total_value` in contracts is aliased as `commitment` in burndown

---

## 2. Discount Scenario Requirements

### Parameters to Capture

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| **Discount Percentage** | % reduction on list price | 10%, 20%, 30% |
| **Discount Type** | How discount applies | overall, sku-specific, tier-based |
| **Amount Variation** | Alternative contract values | +/- 20% of base |
| **Duration Variation** | Extended/shortened contract | 12, 24, 36 months |
| **Effective Date** | When discount starts | contract start or renewal |

### Expected Outputs

1. Simulated burndown curves (how fast budget depletes with discount)
2. Adjusted exhaustion dates (when budget runs out)
3. Savings analysis ($ saved vs baseline)
4. Break-even analysis (discount % needed to hit target date)

---

## 3. Proposed Schema Design

### Option A: Scenario-Centric Model (Recommended)

This approach creates a clear separation between scenarios and their results.

#### New Table: `discount_scenarios`

```sql
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.discount_scenarios (
  scenario_id STRING NOT NULL COMMENT 'Unique scenario identifier (UUID)',
  contract_id STRING NOT NULL COMMENT 'Base contract for simulation',
  scenario_name STRING NOT NULL COMMENT 'User-friendly scenario name',
  description STRING COMMENT 'Detailed description of scenario',

  -- Discount parameters
  discount_pct DECIMAL(5,2) NOT NULL COMMENT 'Overall discount percentage (0-100)',
  discount_type STRING DEFAULT 'overall' COMMENT 'overall, sku_specific, tier_based',

  -- Contract variations
  adjusted_total_value DECIMAL(18,2) COMMENT 'Modified contract value (NULL = use base)',
  adjusted_start_date DATE COMMENT 'Modified start date (NULL = use base)',
  adjusted_end_date DATE COMMENT 'Modified end date (NULL = use base)',

  -- Scenario metadata
  is_baseline BOOLEAN DEFAULT FALSE COMMENT 'True if this is the baseline (0% discount)',
  status STRING DEFAULT 'DRAFT' COMMENT 'DRAFT, ACTIVE, ARCHIVED',
  created_by STRING COMMENT 'User who created scenario',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP,

  CONSTRAINT pk_scenarios PRIMARY KEY (scenario_id),
  CONSTRAINT fk_scenario_contract FOREIGN KEY (contract_id)
    REFERENCES main.account_monitoring_dev.contracts(contract_id)
)
USING DELTA
COMMENT 'What-if discount scenarios for contract simulation'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);
```

#### New Table: `scenario_burndown`

Stores simulated daily burndown for each scenario.

```sql
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.scenario_burndown (
  scenario_id STRING NOT NULL COMMENT 'Scenario this burndown belongs to',
  contract_id STRING NOT NULL COMMENT 'Base contract reference',
  usage_date DATE NOT NULL COMMENT 'Simulation date',

  -- Original values (from actual burndown)
  original_daily_cost DECIMAL(18,2) COMMENT 'Actual daily cost without discount',
  original_cumulative DECIMAL(18,2) COMMENT 'Actual cumulative cost',

  -- Simulated values (with discount applied)
  simulated_daily_cost DECIMAL(18,2) COMMENT 'Daily cost after discount',
  simulated_cumulative DECIMAL(18,2) COMMENT 'Cumulative cost after discount',

  -- Scenario commitment (may differ from base contract)
  scenario_commitment DECIMAL(18,2) COMMENT 'Contract value for this scenario',
  simulated_remaining DECIMAL(18,2) COMMENT 'Remaining budget in scenario',

  -- Savings metrics
  daily_savings DECIMAL(18,2) COMMENT 'Savings on this day',
  cumulative_savings DECIMAL(18,2) COMMENT 'Total savings to date',

  -- Metadata
  calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

  CONSTRAINT pk_scenario_burndown PRIMARY KEY (scenario_id, usage_date)
)
USING DELTA
PARTITIONED BY (scenario_id)
COMMENT 'Simulated burndown data for discount scenarios'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);
```

#### New Table: `scenario_forecast`

Stores Prophet-based predictions for each scenario.

```sql
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.scenario_forecast (
  scenario_id STRING NOT NULL COMMENT 'Scenario this forecast belongs to',
  contract_id STRING NOT NULL COMMENT 'Base contract reference',
  forecast_date DATE NOT NULL COMMENT 'Forecast date',

  -- Predictions (adjusted for discount)
  predicted_daily_cost DECIMAL(18,2) COMMENT 'Predicted daily cost with discount',
  predicted_cumulative DECIMAL(18,2) COMMENT 'Predicted cumulative with discount',
  lower_bound DECIMAL(18,2) COMMENT '10th percentile',
  upper_bound DECIMAL(18,2) COMMENT '90th percentile',

  -- Exhaustion predictions (adjusted for scenario commitment)
  exhaustion_date_p10 DATE COMMENT 'Optimistic exhaustion date',
  exhaustion_date_p50 DATE COMMENT 'Median exhaustion date',
  exhaustion_date_p90 DATE COMMENT 'Conservative exhaustion date',
  days_to_exhaustion INT COMMENT 'Days until median exhaustion',

  -- Comparison to baseline
  days_extended INT COMMENT 'Additional days vs baseline (positive = longer)',
  savings_at_exhaustion DECIMAL(18,2) COMMENT 'Total savings when baseline exhausts',

  -- Model info
  model_version STRING COMMENT 'prophet or linear_fallback',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

  CONSTRAINT pk_scenario_forecast PRIMARY KEY (scenario_id, forecast_date)
)
USING DELTA
PARTITIONED BY (scenario_id)
COMMENT 'Forecasts for discount scenarios'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);
```

#### New Table: `scenario_summary`

Denormalized summary for fast dashboard queries.

```sql
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.scenario_summary (
  scenario_id STRING NOT NULL,
  contract_id STRING NOT NULL,
  scenario_name STRING,
  discount_pct DECIMAL(5,2),

  -- Contract parameters
  base_commitment DECIMAL(18,2) COMMENT 'Original contract value',
  scenario_commitment DECIMAL(18,2) COMMENT 'Scenario contract value',
  contract_start DATE,
  contract_end DATE,

  -- Current state
  actual_cumulative DECIMAL(18,2) COMMENT 'Actual spend to date',
  simulated_cumulative DECIMAL(18,2) COMMENT 'Simulated spend to date',
  cumulative_savings DECIMAL(18,2) COMMENT 'Savings to date',

  -- Projections
  baseline_exhaustion_date DATE COMMENT 'When baseline runs out',
  scenario_exhaustion_date DATE COMMENT 'When scenario runs out',
  days_extended INT COMMENT 'Additional days gained',

  -- Status indicators
  exhaustion_status STRING COMMENT 'EARLY_EXHAUSTION, ON_TRACK, EXTENDED',
  pct_savings DECIMAL(5,2) COMMENT 'Savings as % of base',

  -- Timestamps
  last_calculated TIMESTAMP,

  CONSTRAINT pk_scenario_summary PRIMARY KEY (scenario_id)
)
USING DELTA
COMMENT 'Summary metrics for scenario comparison'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true'
);
```

---

## 4. Entity Relationship Diagram

```
                    ┌─────────────────────┐
                    │     contracts       │
                    │─────────────────────│
                    │ PK: contract_id     │
                    │     total_value     │
                    │     start_date      │
                    │     end_date        │
                    └─────────┬───────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│contract_burndown│  │contract_forecast│  │ discount_scenarios   │
│─────────────────│  │─────────────────│  │──────────────────────│
│ FK: contract_id │  │ FK: contract_id │  │ PK: scenario_id      │
│     usage_date  │  │   forecast_date │  │ FK: contract_id      │
│     daily_cost  │  │predicted_cumul. │  │     discount_pct     │
│cumulative_cost  │  │exhaustion_dates │  │ adjusted_total_value │
└─────────────────┘  └─────────────────┘  └──────────┬───────────┘
                                                     │
                         ┌───────────────────────────┼───────────────┐
                         │                           │               │
                         ▼                           ▼               ▼
              ┌───────────────────┐     ┌───────────────────┐  ┌───────────────┐
              │ scenario_burndown │     │ scenario_forecast │  │scenario_summ. │
              │───────────────────│     │───────────────────│  │───────────────│
              │ FK: scenario_id   │     │ FK: scenario_id   │  │PK: scenario_id│
              │     usage_date    │     │   forecast_date   │  │   metrics...  │
              │simulated_daily    │     │predicted_cumul.   │  └───────────────┘
              │simulated_cumul.   │     │days_extended      │
              │daily_savings      │     │savings_at_exhaust │
              └───────────────────┘     └───────────────────┘
```

---

## 5. Alternative Design: Inline Extension (Not Recommended)

An alternative would be adding scenario columns directly to existing tables:

```sql
-- Add to contract_forecast
ALTER TABLE contract_forecast ADD COLUMNS (
  scenario_id STRING DEFAULT 'baseline',
  discount_pct DECIMAL(5,2) DEFAULT 0,
  is_simulation BOOLEAN DEFAULT FALSE
);
```

**Why Not Recommended:**
- Mixes real data with simulations
- Complicates existing queries
- Risk of accidentally overwriting production forecasts
- Harder to clean up old scenarios

---

## 6. Data Flow for Scenario Simulation

```
User Creates Scenario
        │
        ▼
┌───────────────────────────────┐
│ 1. Store in discount_scenarios │
│    (scenario_id, discount_pct) │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│ 2. Calculate scenario_burndown            │
│    - Apply discount to historical data    │
│    - simulated_daily = original * (1-pct) │
│    - Recalculate cumulative               │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│ 3. Generate scenario_forecast             │
│    - Use Prophet model (same as baseline) │
│    - Scale predictions by (1-discount)    │
│    - Recalculate exhaustion dates         │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│ 4. Update scenario_summary                │
│    - Aggregate metrics                    │
│    - Calculate days_extended              │
│    - Compare to baseline                  │
└───────────────────────────────────────────┘
```

---

## 7. Key Implementation Considerations

### Discount Application Logic

```python
# Simple overall discount
simulated_cost = original_cost * (1 - discount_pct / 100)

# For forecasts, scale the Prophet prediction
predicted_with_discount = prophet_prediction * (1 - discount_pct / 100)
```

### Exhaustion Date Calculation

With a discount, the same consumption pattern extends the contract:

```python
# Days extended = (baseline_exhaustion - scenario_exhaustion)
# Or: days_extended = original_days * (discount_pct / (100 - discount_pct))
```

### Linking Scenarios to Contracts

- **scenario_id**: UUID for unique identification
- **contract_id**: Foreign key to base contract
- **is_baseline**: Flag to identify the 0% discount reference

### Scenario Lifecycle

```
DRAFT → ACTIVE → ARCHIVED
  │       │
  │       └─► Can be used in comparisons
  │
  └─► Editable, not yet calculated
```

---

## 8. Dashboard Query Patterns

### Compare Multiple Scenarios

```sql
SELECT
  s.scenario_name,
  s.discount_pct,
  sm.scenario_exhaustion_date,
  sm.days_extended,
  sm.cumulative_savings,
  sm.pct_savings
FROM discount_scenarios s
JOIN scenario_summary sm ON s.scenario_id = sm.scenario_id
WHERE s.contract_id = :contract_id
  AND s.status = 'ACTIVE'
ORDER BY s.discount_pct;
```

### Burndown Comparison Chart

```sql
-- Combines baseline and scenarios for multi-line chart
SELECT
  usage_date,
  'Baseline (0%)' as scenario,
  cumulative_cost as cumulative
FROM contract_burndown
WHERE contract_id = :contract_id

UNION ALL

SELECT
  usage_date,
  CONCAT(s.scenario_name, ' (', s.discount_pct, '%)') as scenario,
  sb.simulated_cumulative as cumulative
FROM scenario_burndown sb
JOIN discount_scenarios s ON sb.scenario_id = s.scenario_id
WHERE sb.contract_id = :contract_id
  AND s.status = 'ACTIVE';
```

---

## 9. Storage Estimates

| Table | Rows per Contract | Size per Contract |
|-------|-------------------|-------------------|
| discount_scenarios | 5-10 scenarios | ~1 KB |
| scenario_burndown | 365 days x 5 scenarios = 1,825 | ~100 KB |
| scenario_forecast | 365 days x 5 scenarios = 1,825 | ~100 KB |
| scenario_summary | 5 scenarios | ~1 KB |

**Total per contract:** ~200 KB
**For 100 contracts:** ~20 MB

Very manageable size, well within Delta Lake performance characteristics.

---

## 10. Recommendations

1. **Use Option A (Scenario-Centric)** - Clean separation, no risk to production data
2. **Start with simple overall discount** - Defer SKU-specific until validated
3. **Include baseline scenario** - Always create a 0% discount scenario for comparison
4. **Leverage existing Prophet model** - Just scale predictions, don't retrain
5. **Add UI for scenario management** - Allow create/edit/archive via dashboard

---

## Next Steps

- [ ] Review schema design with team
- [ ] Decide on MVP scope (overall discount only?)
- [ ] Determine UI approach (dashboard widget vs separate page)
- [ ] Plan simulation calculation notebook/job

---

*Document created: 2026-02-07*
*Author: Claude (Data Model Research Agent)*
