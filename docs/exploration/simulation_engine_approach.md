# Simulation Calculation Engine Design

## Overview

This document outlines the approach for calculating savings in "what-if" discount simulation scenarios for Databricks commit contracts. The goal is to help users compare their current consumption against hypothetical contract structures to identify potential savings.

## 1. Current Data Model Analysis

### Existing Tables and Key Fields

**contracts table:**
- `contract_id` - Unique identifier
- `total_value` (DECIMAL 18,2) - Contract commitment amount
- `start_date`, `end_date` - Contract duration
- `commitment_type` - DBU or SPEND commitment
- `cloud_provider` - aws, azure, gcp

**dashboard_data table:**
- `actual_cost` (DECIMAL 18,2) - Actual cost paid (with discount)
- `list_cost` (DECIMAL 18,2) - List price before discount
- `usage_quantity` (DECIMAL 18,6) - DBU consumption
- `price_per_unit` (DECIMAL 20,10) - Unit price

**contract_burndown table (derived):**
- `daily_cost` - Aggregated daily actual cost
- `cumulative_cost` - Running total consumption
- `commitment` - Contract total value (aliased from total_value)
- `remaining_budget` - Contract value minus cumulative cost

### Key Insight: List vs Actual Cost
The `dashboard_data` table already captures both:
- `list_cost` = On-demand/list pricing (no discount)
- `actual_cost` = What was actually paid (with current discount)

This means the **effective discount rate** can be derived:
```
effective_discount_rate = 1 - (actual_cost / list_cost)
```

---

## 2. Commitment Level Calculations

### 2.1 How Databricks Commit Discounts Work

Databricks typically offers tiered discounts based on commitment amount and duration:

| Commitment Tier | 1-Year Discount | 2-Year Discount | 3-Year Discount |
|-----------------|-----------------|-----------------|-----------------|
| $50K - $100K    | ~15%            | ~20%            | ~25%           |
| $100K - $250K   | ~20%            | ~25%            | ~30%           |
| $250K - $500K   | ~25%            | ~30%            | ~35%           |
| $500K - $1M     | ~30%            | ~35%            | ~40%           |
| $1M+            | ~35%            | ~40%            | ~45%           |

**Note:** These are illustrative tiers. Actual discount schedules should be configurable.

### 2.2 Core Formula: Savings Calculation

For any given scenario, the simulation needs to calculate:

```
Scenario Parameters:
- commitment_amount: Dollar value of contract (e.g., $200,000)
- duration_years: 1, 2, or 3 years
- discount_rate: Based on tier lookup

Calculations:
- list_price_total = SUM(list_cost) over contract period
- discounted_price = list_price_total * (1 - discount_rate)
- actual_commitment_cost = MIN(discounted_price, commitment_amount)
- savings_vs_ondemand = list_price_total - actual_commitment_cost
- savings_percentage = (savings_vs_ondemand / list_price_total) * 100

Under-consumption handling:
- If discounted_price < commitment_amount:
    effective_spend = commitment_amount (you pay for unused commit)
    wasted_commit = commitment_amount - discounted_price
```

### 2.3 SQL Implementation Approach

```sql
-- Simulation calculation CTE
WITH consumption_by_period AS (
    SELECT
        cloud_provider,
        SUM(list_cost) as total_list_cost,
        SUM(actual_cost) as total_actual_cost,
        MIN(usage_date) as period_start,
        MAX(usage_date) as period_end,
        DATEDIFF(MAX(usage_date), MIN(usage_date)) as days_covered
    FROM dashboard_data
    WHERE usage_date BETWEEN @sim_start AND @sim_end
    GROUP BY cloud_provider
),

-- Annualize consumption for projection
annualized_consumption AS (
    SELECT
        *,
        -- Scale up to full year if partial data
        total_list_cost * (365.0 / GREATEST(days_covered, 1)) as annual_list_cost
    FROM consumption_by_period
),

-- Apply discount tiers
scenario_results AS (
    SELECT
        cloud_provider,
        annual_list_cost,
        @commitment_amount as commitment,
        @duration_years as duration,

        -- Lookup discount rate based on commitment tier
        CASE
            WHEN @commitment_amount >= 1000000 THEN
                CASE @duration_years WHEN 1 THEN 0.35 WHEN 2 THEN 0.40 ELSE 0.45 END
            WHEN @commitment_amount >= 500000 THEN
                CASE @duration_years WHEN 1 THEN 0.30 WHEN 2 THEN 0.35 ELSE 0.40 END
            WHEN @commitment_amount >= 250000 THEN
                CASE @duration_years WHEN 1 THEN 0.25 WHEN 2 THEN 0.30 ELSE 0.35 END
            WHEN @commitment_amount >= 100000 THEN
                CASE @duration_years WHEN 1 THEN 0.20 WHEN 2 THEN 0.25 ELSE 0.30 END
            ELSE
                CASE @duration_years WHEN 1 THEN 0.15 WHEN 2 THEN 0.20 ELSE 0.25 END
        END as discount_rate,

        -- Calculate discounted cost
        annual_list_cost * (1 - discount_rate) as discounted_annual_cost
    FROM annualized_consumption
)

SELECT
    cloud_provider,
    annual_list_cost as on_demand_cost,
    commitment,
    duration,
    discount_rate,
    discounted_annual_cost,

    -- Total over contract duration
    annual_list_cost * duration as total_list_cost,
    GREATEST(discounted_annual_cost * duration, commitment) as total_effective_cost,

    -- Savings calculations
    (annual_list_cost * duration) - GREATEST(discounted_annual_cost * duration, commitment) as total_savings,

    -- Utilization
    ROUND((discounted_annual_cost * duration / commitment) * 100, 2) as commitment_utilization_pct,

    -- Status
    CASE
        WHEN discounted_annual_cost * duration >= commitment THEN 'FULLY UTILIZED'
        WHEN discounted_annual_cost * duration >= commitment * 0.8 THEN 'WELL UTILIZED'
        ELSE 'UNDER-UTILIZED'
    END as utilization_status
FROM scenario_results;
```

---

## 3. Handling Different Commitment Amounts

### 3.1 Multi-Scenario Comparison

To compare multiple commitment levels (e.g., $100K, $200K, $500K), generate scenarios in parallel:

```sql
-- Define commitment scenarios
WITH commitment_scenarios AS (
    SELECT 100000 as commitment, 1 as scenario_id UNION ALL
    SELECT 200000, 2 UNION ALL
    SELECT 300000, 3 UNION ALL
    SELECT 500000, 4 UNION ALL
    SELECT 750000, 5 UNION ALL
    SELECT 1000000, 6
),

-- Cross join with durations
scenario_matrix AS (
    SELECT
        c.commitment,
        d.duration,
        c.scenario_id * 10 + d.duration as matrix_id
    FROM commitment_scenarios c
    CROSS JOIN (SELECT 1 as duration UNION ALL SELECT 2 UNION ALL SELECT 3) d
)
-- ... apply discount calculations to each scenario
```

### 3.2 Break-Even Analysis

Calculate the minimum consumption needed to justify each commitment level:

```
break_even_consumption = commitment_amount / (1 - discount_rate)
```

For example:
- $200K commitment with 25% discount
- Break-even = $200K / 0.75 = $266,667 list price consumption
- If your list price consumption < $266,667, you're overpaying for unused commit

---

## 4. Handling Different Durations

### 4.1 Duration Impact on Discount

Longer commitments get deeper discounts but have risks:
- **1-Year:** Lower discount, more flexibility, lower risk of over-commitment
- **2-Year:** Better discount, moderate lock-in
- **3-Year:** Best discount, highest lock-in risk

### 4.2 Time Value Consideration

For multi-year comparisons, consider present value:

```sql
-- Net Present Value calculation (simplified, 5% discount rate)
SELECT
    commitment,
    duration,
    total_savings,
    -- NPV of savings
    CASE duration
        WHEN 1 THEN total_savings
        WHEN 2 THEN total_savings / 1.05  -- Year 2 discount
        WHEN 3 THEN total_savings / 1.1025  -- Year 3 discount (1.05^2)
    END as npv_savings
FROM scenario_results;
```

### 4.3 Growth Projections

Use Prophet forecasts to project consumption growth:

```sql
-- Combine historical growth with commit scenarios
WITH growth_analysis AS (
    SELECT
        contract_id,
        AVG(predicted_daily_cost) as avg_daily_forecast,
        AVG(predicted_daily_cost) * 365 as annual_forecast
    FROM contract_forecast
    WHERE forecast_date BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, 365)
    GROUP BY contract_id
)
-- Apply scenarios to forecasted consumption
```

---

## 5. Finding the "Sweet Spot"

### 5.1 Optimization Objective

The "sweet spot" is where:
```
maximize(savings_vs_ondemand) while maintaining utilization >= 85%
```

### 5.2 Sweet Spot Detection Algorithm

```python
def find_sweet_spot(annual_consumption_list, discount_tiers):
    """
    Find the optimal commitment level.

    Parameters:
    - annual_consumption_list: Expected annual list-price consumption
    - discount_tiers: Dict of {commitment: {1: rate, 2: rate, 3: rate}}

    Returns:
    - optimal_commitment, optimal_duration, expected_savings
    """
    results = []

    for commitment, rates in discount_tiers.items():
        for duration, discount_rate in rates.items():
            # Calculate effective cost under this scenario
            discounted_consumption = annual_consumption_list * (1 - discount_rate)

            # You pay MAX of (commitment, discounted consumption)
            effective_annual_cost = max(commitment, discounted_consumption)
            total_cost = effective_annual_cost * duration

            # Savings vs on-demand
            on_demand_total = annual_consumption_list * duration
            savings = on_demand_total - total_cost

            # Utilization
            utilization = discounted_consumption / commitment

            results.append({
                'commitment': commitment,
                'duration': duration,
                'discount_rate': discount_rate,
                'total_savings': savings,
                'utilization': utilization,
                'savings_per_dollar_committed': savings / (commitment * duration)
            })

    # Filter for acceptable utilization (>= 85%)
    valid = [r for r in results if r['utilization'] >= 0.85]

    # Find max savings
    if valid:
        return max(valid, key=lambda x: x['total_savings'])
    else:
        # If no scenario meets utilization, recommend lowest commit
        return min(results, key=lambda x: x['commitment'])
```

### 5.3 SQL Implementation for Sweet Spot

```sql
-- Generate all scenario combinations and rank them
WITH all_scenarios AS (
    -- ... scenario matrix generation ...
),

ranked_scenarios AS (
    SELECT
        *,
        -- Rank by savings, but penalize under-utilization
        RANK() OVER (
            ORDER BY
                CASE WHEN utilization >= 0.85 THEN total_savings ELSE -1000000 END DESC
        ) as savings_rank,

        -- Flag the sweet spot
        ROW_NUMBER() OVER (
            PARTITION BY 1
            ORDER BY
                CASE WHEN utilization >= 0.85 THEN total_savings ELSE -1000000 END DESC
        ) as is_optimal
    FROM all_scenarios
)

SELECT
    *,
    CASE WHEN is_optimal = 1 THEN 'RECOMMENDED' ELSE '' END as recommendation
FROM ranked_scenarios
ORDER BY savings_rank;
```

---

## 6. Calculation Accuracy Considerations

### 6.1 Data Quality Checks

Before running simulations, validate:
```sql
-- Check for list_cost availability
SELECT
    COUNT(*) as total_records,
    COUNT(list_cost) as with_list_cost,
    COUNT(actual_cost) as with_actual_cost,
    ROUND(COUNT(list_cost) * 100.0 / COUNT(*), 2) as list_cost_coverage_pct
FROM dashboard_data;
```

### 6.2 Handling Missing List Prices

If `list_cost` is NULL, estimate from DBU consumption:
```sql
COALESCE(
    list_cost,
    usage_quantity * COALESCE(price_per_unit, 0.22)  -- Default DBU rate
) as estimated_list_cost
```

### 6.3 Seasonality Adjustment

Use Prophet predictions to account for seasonal variation:
```sql
-- Seasonal adjustment factor
WITH seasonal_factors AS (
    SELECT
        MONTH(forecast_date) as month,
        AVG(predicted_daily_cost) /
            (SUM(AVG(predicted_daily_cost)) OVER () / 12) as seasonal_factor
    FROM contract_forecast
    GROUP BY MONTH(forecast_date)
)
```

---

## 7. Proposed Table Schema for Simulations

### 7.1 Discount Tiers Configuration Table

```sql
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.discount_tiers (
    tier_id STRING NOT NULL,
    min_commitment DECIMAL(18,2) NOT NULL,
    max_commitment DECIMAL(18,2),
    duration_years INT NOT NULL,
    discount_rate DECIMAL(5,4) NOT NULL,
    cloud_provider STRING,  -- NULL means all providers
    effective_date DATE,
    expiration_date DATE,
    notes STRING,
    CONSTRAINT pk_discount_tiers PRIMARY KEY (tier_id)
);

-- Sample data
INSERT INTO main.account_monitoring_dev.discount_tiers VALUES
('TIER_50K_1Y', 50000, 99999, 1, 0.15, NULL, '2024-01-01', '2025-12-31', 'Entry tier'),
('TIER_100K_1Y', 100000, 249999, 1, 0.20, NULL, '2024-01-01', '2025-12-31', 'Standard tier'),
('TIER_100K_2Y', 100000, 249999, 2, 0.25, NULL, '2024-01-01', '2025-12-31', 'Standard tier'),
('TIER_100K_3Y', 100000, 249999, 3, 0.30, NULL, '2024-01-01', '2025-12-31', 'Standard tier'),
-- ... additional tiers ...
```

### 7.2 Simulation Results Table

```sql
CREATE TABLE IF NOT EXISTS main.account_monitoring_dev.simulation_results (
    simulation_id STRING NOT NULL,
    contract_id STRING NOT NULL,
    created_at TIMESTAMP,
    created_by STRING,

    -- Simulation parameters
    simulation_name STRING,
    simulation_period_start DATE,
    simulation_period_end DATE,

    -- Scenario details
    scenario_commitment DECIMAL(18,2),
    scenario_duration INT,
    scenario_discount_rate DECIMAL(5,4),

    -- Input consumption
    historical_list_cost DECIMAL(18,2),
    historical_actual_cost DECIMAL(18,2),
    projected_annual_consumption DECIMAL(18,2),

    -- Results
    scenario_total_cost DECIMAL(18,2),
    on_demand_total_cost DECIMAL(18,2),
    total_savings DECIMAL(18,2),
    savings_percentage DECIMAL(5,2),
    commitment_utilization DECIMAL(5,2),

    -- Recommendation
    is_sweet_spot BOOLEAN,
    recommendation_notes STRING,

    CONSTRAINT pk_simulation PRIMARY KEY (simulation_id)
);
```

---

## 8. Integration with Existing Forecaster

### 8.1 Leveraging Prophet Predictions

The existing `consumption_forecaster.py` provides:
- `predicted_daily_cost` - Daily consumption forecast
- `predicted_cumulative` - Running total
- `exhaustion_date_p50` - When current contract exhausts

For simulations, use these forecasts to project future consumption:

```python
def project_consumption_for_simulation(contract_id, duration_years):
    """
    Use Prophet forecasts to project consumption for simulation scenarios.
    """
    # Get forecasted daily consumption
    forecast_df = spark.sql(f"""
        SELECT
            forecast_date,
            predicted_daily_cost,
            lower_bound,
            upper_bound
        FROM contract_forecast
        WHERE contract_id = '{contract_id}'
          AND forecast_date >= CURRENT_DATE()
          AND forecast_date < DATE_ADD(CURRENT_DATE(), {duration_years * 365})
    """).toPandas()

    # Aggregate to get annual projections
    annual_projection = forecast_df['predicted_daily_cost'].sum() * (365 / len(forecast_df))
    annual_upper = forecast_df['upper_bound'].sum() * (365 / len(forecast_df))
    annual_lower = forecast_df['lower_bound'].sum() * (365 / len(forecast_df))

    return {
        'median': annual_projection * duration_years,
        'optimistic': annual_lower * duration_years,
        'conservative': annual_upper * duration_years
    }
```

### 8.2 Probabilistic Scenario Analysis

Instead of single-point estimates, provide ranges:
- **Optimistic (p10):** Low consumption scenario
- **Median (p50):** Expected consumption
- **Conservative (p90):** High consumption scenario

```sql
-- Three-scenario simulation
SELECT
    scenario_name,
    commitment,
    duration,

    -- Optimistic case (low consumption)
    consumption_p10 * duration as total_consumption_low,
    GREATEST(consumption_p10 * duration * (1 - discount_rate), commitment * duration) as cost_low,

    -- Median case
    consumption_p50 * duration as total_consumption_med,
    GREATEST(consumption_p50 * duration * (1 - discount_rate), commitment * duration) as cost_med,

    -- Conservative case (high consumption)
    consumption_p90 * duration as total_consumption_high,
    consumption_p90 * duration * (1 - discount_rate) as cost_high  -- Likely exceeds commit

FROM simulation_inputs;
```

---

## 9. Summary: Recommended Implementation Approach

### Phase 1: Core Calculation Engine
1. Create `discount_tiers` configuration table (admin-managed)
2. Implement scenario calculation SQL/Python functions
3. Add `simulation_results` table for storing comparisons

### Phase 2: Integration with Forecaster
1. Use Prophet `predicted_cumulative` for consumption projections
2. Generate probabilistic scenarios (p10/p50/p90)
3. Add "What-If" section to forecaster notebook

### Phase 3: Dashboard Integration
1. Add simulation parameter widgets (commitment slider, duration selector)
2. Create comparison charts (scenarios side-by-side)
3. Highlight "sweet spot" recommendation

### Key Formulas Summary

| Metric | Formula |
|--------|---------|
| Effective Discount | `1 - (actual_cost / list_cost)` |
| Break-even Consumption | `commitment / (1 - discount_rate)` |
| Savings vs On-Demand | `list_total - MAX(discounted_total, commitment)` |
| Utilization % | `discounted_consumption / commitment * 100` |
| Sweet Spot | `MAX(savings) WHERE utilization >= 85%` |

---

## 10. References

- `/Users/laurent.prat/Documents/lpdev/databricks_conso_reports/notebooks/consumption_forecaster.py` - Prophet model implementation
- `/Users/laurent.prat/Documents/lpdev/databricks_conso_reports/sql/refresh_contract_burndown.sql` - Consumption calculations
- `/Users/laurent.prat/Documents/lpdev/databricks_conso_reports/sql/create_forecast_schema.sql` - Forecast table schema
