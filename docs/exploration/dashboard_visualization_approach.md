# Dashboard Visualization Approach for What-If Discount Simulations

## Research Summary

**Date:** 2026-02-07
**Purpose:** Explore how to present what-if discount simulation results in the Lakeview dashboard
**Status:** Research / Exploration Only

---

## 1. Current Dashboard Structure Analysis

The existing Contract Consumption Monitor dashboard uses:

### Widget Types in Use
| Widget Type | Count | Use Case |
|-------------|-------|----------|
| Counter     | 3     | KPIs (Total Value, Consumed, Remaining) |
| Pie Chart   | 1     | Pace Distribution |
| Line Chart  | 4     | Burndown trends, forecasts |
| Table       | 2     | Contract details, exhaustion prediction |

### Layout System
- **6-column grid** with flexible height
- Counters: width 2, height 2
- Charts: width 3-6, height 4-5
- Tables: width 6, height 3-5

### Color Conventions
- Historical Consumption: Gold (#FFD700)
- ML Forecast (Prophet): Red (#FF0000)
- Contract Commitment: Dark Blue (#00008B)
- Exhaustion marker: White vertical line

---

## 2. Chart Types for Scenario Comparison

### Recommended: Multi-Series Line Chart

**Best for:** Showing baseline vs. discounted scenarios over time

```
Cumulative Cost ($)
    ^
    |     __________________ Contract Commitment
    |    /
    |   / -------- Baseline (No Discount)
    |  /
    | /  ........ With 5% Discount
    |/   -------- With 10% Discount
    +---------------------------------> Date
```

**Implementation Pattern (from existing ds_prophet_combined):**
```sql
WITH scenarios AS (
  SELECT
    contract_id,
    forecast_date as date,
    predicted_cumulative as value,
    'Baseline (No Discount)' as scenario
  FROM contract_forecast

  UNION ALL

  SELECT
    contract_id,
    forecast_date as date,
    predicted_cumulative * (1 - discount_rate) as value,
    CONCAT(CAST(discount_rate * 100 AS INT), '% Discount') as scenario
  FROM contract_forecast
  CROSS JOIN (SELECT 0.05 as discount_rate UNION SELECT 0.10)
)
SELECT * FROM scenarios ORDER BY contract_id, date, scenario
```

**Lakeview Widget Spec:**
```json
{
  "spec": {
    "version": 3,
    "widgetType": "line",
    "encodings": {
      "x": {"fieldName": "date", "scale": {"type": "temporal"}},
      "y": {"fieldName": "value", "scale": {"type": "quantitative"}},
      "color": {
        "fieldName": "scenario",
        "scale": {
          "type": "categorical",
          "mappings": [
            {"value": "Baseline (No Discount)", "color": "#FF0000"},
            {"value": "5% Discount", "color": "#00A972"},
            {"value": "10% Discount", "color": "#0078D4"}
          ]
        }
      }
    }
  }
}
```

### Alternative: Grouped Bar Chart

**Best for:** Comparing total savings across discount levels

```
Total Remaining Budget ($)
    ^
    |  [====]
    |  [======]
    |  [========]
    +-------------------> Discount %
       0%   5%   10%
```

---

## 3. Savings Comparison Tables

### Design Pattern 1: Summary Comparison Table

| Contract ID | Commitment | Baseline Exhaustion | 5% Discount | 10% Discount | Max Savings |
|-------------|------------|---------------------|-------------|--------------|-------------|
| CONTRACT-001 | $500,000 | Jul 29, 2026 | Aug 15, 2026 | Sep 1, 2026 | $50,000 |
| CONTRACT-002 | $250,000 | Dec 15, 2026 | Jan 10, 2027 | Feb 5, 2027 | $25,000 |

**Lakeview Table Widget Spec:**
```json
{
  "spec": {
    "version": 2,
    "widgetType": "table",
    "encodings": {
      "columns": [
        {"fieldName": "contract_id", "displayName": "Contract", "type": "string"},
        {"fieldName": "commitment", "displayName": "Commitment ($)", "type": "number", "numberFormat": "#,##0"},
        {"fieldName": "baseline_exhaustion", "displayName": "Baseline Exhaustion", "type": "datetime"},
        {"fieldName": "discount_5_exhaustion", "displayName": "5% Discount", "type": "datetime"},
        {"fieldName": "discount_10_exhaustion", "displayName": "10% Discount", "type": "datetime"},
        {"fieldName": "max_savings", "displayName": "Max Annual Savings", "type": "number", "numberFormat": "$#,##0"}
      ]
    }
  }
}
```

### Design Pattern 2: Detailed Breakdown Table

| Discount Level | Projected End Date | Days Extended | Monthly Savings | Annual Savings | ROI vs Baseline |
|----------------|-------------------|---------------|-----------------|----------------|-----------------|
| 0% (Baseline)  | Jul 29, 2026      | -             | $0              | $0             | -               |
| 5%             | Aug 15, 2026      | +17 days      | $2,083          | $25,000        | 5%              |
| 10%            | Sep 1, 2026       | +34 days      | $4,167          | $50,000        | 10%             |

---

## 4. Sensitivity Analysis Visualization

### Option A: Stepped Line/Area Chart

Shows how small changes in discount % affect outcomes:

```
Days Until Exhaustion
    ^
    |              _______
    |         ____/
    |    ____/
    |___/
    +---------------------------------> Discount %
    0%   2%   4%   6%   8%   10%
```

**Implementation:** Generate a dataset with discount increments (0.5% or 1% steps)

### Option B: Counter Widgets with Delta

Show KPI counters with comparison to baseline:

```
+------------------+  +------------------+  +------------------+
| Days Extended    |  | Monthly Savings  |  | Annual Savings   |
|       +34        |  |     $4,167       |  |    $50,000       |
| vs baseline      |  | at 10% discount  |  | at 10% discount  |
+------------------+  +------------------+  +------------------+
```

### Option C: Heatmap/Matrix (Limited in Lakeview)

Lakeview does not natively support heatmaps. Alternative: Use conditional formatting in tables if available, or use a scatter plot with color encoding for intensity.

---

## 5. Interactive Parameter Selection - Lakeview Capabilities

### Available Filter Widgets

| Filter Type | Widget Type | Use Case |
|-------------|-------------|----------|
| Single Select Dropdown | `filter-single-select` | Select one discount level |
| Multi-Select | `filter-multi-select` | Compare multiple scenarios |
| Date Range | `filter-date-range-picker` | Focus on specific period |

### Single Select for Discount Level

```json
{
  "spec": {
    "version": 2,
    "widgetType": "filter-single-select",
    "encodings": {
      "fields": [{
        "fieldName": "discount_level",
        "displayName": "Select Discount Level"
      }]
    }
  }
}
```

**Limitation:** Filter values must exist in the dataset. Pre-compute scenarios (0%, 5%, 10%, etc.) rather than allowing arbitrary input.

### Multi-Select for Scenario Comparison

```json
{
  "spec": {
    "version": 2,
    "widgetType": "filter-multi-select",
    "encodings": {
      "fields": [{
        "fieldName": "scenario_name",
        "displayName": "Compare Scenarios"
      }]
    }
  }
}
```

### Lakeview Limitations for What-If

| Requirement | Lakeview Support | Workaround |
|-------------|------------------|------------|
| Arbitrary discount % input | No (no text input widget) | Pre-compute discrete levels |
| Slider widget | No | Use dropdown with preset values |
| Real-time calculation | No (static SQL) | Pre-compute all scenarios |
| Dynamic parameter passing | Limited (dataset params) | Use dataset parameters |

---

## 6. Proposed Dashboard Page Structure

### Option A: Dedicated What-If Page (Recommended)

```
+================================================================+
|                  What-If Discount Simulation                    |
+================================================================+
|                                                                  |
| [Filter: Contract] [Filter: Discount Levels to Compare]         |
|                                                                  |
+-------------------------------+----------------------------------+
| Scenario Comparison Chart     | Savings Summary                  |
| (Multi-line burndown)         | +----------+----------+          |
|                               | | Days     | Annual   |          |
|                               | | Extended | Savings  |          |
|                               | |  +34     | $50,000  |          |
|                               | +----------+----------+          |
+-------------------------------+----------------------------------+
| Detailed Comparison Table                                        |
| Contract | Baseline | 5% | 10% | Max Savings | Best Scenario    |
+-------------------------------+----------------------------------+
| Sensitivity Chart                                                |
| (Days extended vs discount %)                                    |
+================================================================+
```

**Layout Positions:**
- Filters: x=0, y=0, width=6, height=1
- Scenario Chart: x=0, y=1, width=4, height=5
- Savings Counters: x=4, y=1, width=2, height=5
- Comparison Table: x=0, y=6, width=6, height=4
- Sensitivity Chart: x=0, y=10, width=6, height=4

### Option B: Integrated into Contract Burndown Page

Add what-if elements to existing Contract Burndown page:

```
+================================================================+
|                     Contract Burndown                           |
+================================================================+
| [Existing widgets...]                                           |
+-------------------------------+----------------------------------+
| Prophet Forecast + Scenarios  | Discount Impact Summary         |
| (Add scenario lines to        | (New counter widget)            |
|  existing chart)              |                                 |
+-------------------------------+----------------------------------+
```

**Pros:** Less navigation, context preserved
**Cons:** Page becomes crowded, harder to maintain

### Option C: Drill-Down Approach

- Main dashboard shows baseline
- Link to separate "What-If Analysis" dashboard for deeper exploration

---

## 7. Data Requirements for Visualization

### Required Datasets

1. **ds_whatif_scenarios** - Pre-computed discount scenarios
```sql
SELECT
  contract_id,
  forecast_date,
  discount_rate,
  CONCAT(CAST(discount_rate * 100 AS INT), '% Discount') as scenario_name,
  original_predicted_cumulative,
  discounted_predicted_cumulative,
  savings_amount
FROM what_if_simulations
```

2. **ds_whatif_summary** - Summary statistics per scenario
```sql
SELECT
  contract_id,
  discount_rate,
  exhaustion_date,
  days_extended,
  monthly_savings,
  annual_savings
FROM what_if_summary
```

3. **ds_whatif_sensitivity** - Fine-grained sensitivity data
```sql
SELECT
  contract_id,
  discount_rate,  -- 0.00, 0.01, 0.02, ..., 0.20
  days_until_exhaustion,
  total_savings
FROM what_if_sensitivity
```

---

## 8. Recommendations

### Best Approach for MVP

1. **Add new dashboard page** named "What-If Analysis"
2. **Pre-compute 5 discount levels**: 0%, 5%, 10%, 15%, 20%
3. **Use multi-select filter** to choose which scenarios to display
4. **Primary visualization**: Multi-series line chart showing burndown for each scenario
5. **Secondary visualization**: Summary table with exhaustion dates and savings
6. **Counter widgets**: Show max potential savings at highest discount level

### Chart Color Scheme for Scenarios

| Scenario | Color | Hex |
|----------|-------|-----|
| Baseline (0%) | Red | #FF0000 |
| 5% Discount | Light Green | #90EE90 |
| 10% Discount | Green | #00A972 |
| 15% Discount | Blue | #0078D4 |
| 20% Discount | Dark Blue | #00008B |

### User Experience Considerations

1. **Default view**: Show baseline + 10% discount (most common negotiation target)
2. **Clear labeling**: Always show discount % in legend and tooltips
3. **Savings emphasis**: Use counters to highlight dollar impact
4. **Contract commitment line**: Keep visible in all scenarios for reference

---

## 9. Technical Constraints

### Lakeview Limitations to Note

1. **No real-time calculations** - All scenarios must be pre-computed in SQL/tables
2. **No input widgets** - Cannot let users enter arbitrary discount percentages
3. **No conditional formatting** - Cannot highlight cells based on values
4. **Limited interactivity** - Filters work, but no drill-through or linking
5. **6-column grid only** - Layout flexibility is constrained

### Performance Considerations

- Pre-computed scenarios add rows to result sets (5x for 5 discount levels)
- Consider limiting historical data range for what-if charts
- Use materialized views for complex scenario calculations

---

## 10. Next Steps (If Implementation Approved)

1. Design what-if simulation calculation logic (SQL or Python)
2. Create `what_if_simulations` table schema
3. Build pre-computation job to generate scenarios
4. Add datasets to dashboard JSON
5. Create new "What-If Analysis" page with proposed layout
6. Test with sample data
7. Document user guide for interpretation

---

**Document Author:** Research Agent
**Review Status:** Pending team lead review
