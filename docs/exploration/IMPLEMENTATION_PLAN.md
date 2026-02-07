# What-If Discount Simulation - Implementation Plan

## Executive Summary

This plan synthesizes findings from 4 parallel research agents to define the implementation approach for the What-If Discount Simulation feature. The feature enables users to model different contract discount scenarios and compare potential savings against their current consumption patterns.

**Date:** 2026-02-07
**Branch:** `feature/what-if-simulation`
**Target Version:** v2.0.0

---

## Research Synthesis

### Key Findings from Research Agents

| Agent | Key Recommendation |
|-------|-------------------|
| **Data Model** | Scenario-centric model with 4 new tables: `discount_scenarios`, `scenario_burndown`, `scenario_forecast`, `scenario_summary` |
| **Simulation Engine** | Use existing Prophet forecasts, scale by discount factor, include break-even and "sweet spot" analysis |
| **Dashboard** | New dedicated "What-If Analysis" page with pre-computed scenarios (0%, 5%, 10%, 15%, 20%) |
| **Best Practices** | Follow cloud vendor patterns: show savings prominently, quantify risk, enable exploration with guardrails |

### Recommended Approach: Scenario-Centric Model

**Rationale:**
1. Clean separation of simulation data from production data
2. Pre-computed scenarios for fast dashboard rendering
3. Leverages existing Prophet forecasts (no need to retrain models)
4. Aligns with industry best practices from AWS/Azure/GCP

---

## Architecture Overview

```
                    +---------------------+
                    |   User Interface    |
                    | (Lakeview Dashboard)|
                    +----------+----------+
                               |
                    +----------v----------+
                    |   Dashboard Datasets |
                    | (Pre-computed SQL)   |
                    +----------+----------+
                               |
         +---------------------+---------------------+
         |                     |                     |
+--------v--------+   +--------v--------+   +--------v--------+
| discount_scenarios|   | scenario_summary|   | scenario_forecast|
| (config)         |   | (KPIs)          |   | (time series)    |
+-----------------+   +-----------------+   +-----------------+
         |                     |                     |
         +---------------------+---------------------+
                               |
                    +----------v----------+
                    | Scenario Calculator |
                    | (Notebook/SQL)      |
                    +----------+----------+
                               |
         +---------------------+---------------------+
         |                     |                     |
+--------v--------+   +--------v--------+   +--------v--------+
|    contracts    |   |contract_burndown|   |contract_forecast |
| (base data)     |   | (actual usage)  |   | (Prophet ML)     |
+-----------------+   +-----------------+   +-----------------+
```

---

## Implementation Phases

### Phase 1: Data Model & Schema (Week 1)

**Objective:** Create the database schema for storing discount scenarios

**Deliverables:**
1. `sql/create_whatif_schema.sql` - New tables
2. `sql/populate_discount_tiers.sql` - Default discount tier configuration

**New Tables:**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `discount_tiers` | Configurable discount rates by commitment level | tier_id, min_commitment, discount_rate, duration |
| `discount_scenarios` | User-defined scenarios | scenario_id, contract_id, discount_pct, adjusted_total_value |
| `scenario_burndown` | Simulated daily consumption | scenario_id, usage_date, simulated_cumulative, daily_savings |
| `scenario_forecast` | Projected exhaustion with discount | scenario_id, forecast_date, days_extended, savings_at_exhaustion |
| `scenario_summary` | Denormalized KPIs for dashboard | scenario_id, cumulative_savings, exhaustion_date, pct_savings |

**Files to Create:**
- `sql/create_whatif_schema.sql` (new)
- `sql/populate_discount_tiers.sql` (new)

---

### Phase 2: Simulation Calculator (Week 2)

**Objective:** Build the calculation engine that generates scenario data

**Deliverables:**
1. New section in `notebooks/consumption_forecaster.py` OR new notebook `notebooks/whatif_simulator.py`
2. `sql/refresh_whatif_scenarios.sql` - Refresh scenario calculations

**Core Calculations:**

```python
# Discount Application
simulated_cost = original_cost * (1 - discount_pct / 100)

# Exhaustion Date Calculation
days_extended = baseline_days * (discount_pct / (100 - discount_pct))

# Break-Even Analysis
break_even_consumption = commitment / (1 - discount_pct / 100)

# Sweet Spot Detection
sweet_spot = max(savings) where utilization >= 85%
```

**Pre-Computed Scenarios:**
- 0% (Baseline - current contract)
- 5% discount
- 10% discount
- 15% discount
- 20% discount

**Files to Create/Modify:**
- `notebooks/whatif_simulator.py` (new)
- `sql/refresh_whatif_scenarios.sql` (new)

---

### Phase 3: Dashboard Integration (Week 3)

**Objective:** Add What-If Analysis page to Lakeview dashboard

**Deliverables:**
1. New dashboard page: "What-If Analysis"
2. 4-5 new widgets
3. 3 new datasets

**Dashboard Page Layout:**

```
+================================================================+
|                  What-If Analysis                               |
+================================================================+
| [Filter: Contract] [Filter: Discount Scenarios to Compare]      |
+-------------------------------+---------------------------------+
| Scenario Comparison Chart     | Savings Summary                 |
| (Multi-line burndown)         | +----------+----------+         |
| Width: 4, Height: 5           | | Days     | Max      |         |
|                               | | Extended | Savings  |         |
|                               | |  +34     | $50,000  |         |
|                               | +----------+----------+         |
|                               | Width: 2, Height: 5             |
+-------------------------------+---------------------------------+
| Scenario Comparison Table                                       |
| Contract | Baseline | 5% | 10% | 15% | 20% | Recommended        |
| Width: 6, Height: 4                                             |
+-------------------------------+---------------------------------+
| Break-Even Analysis                                             |
| [Gauge/Bar showing utilization vs break-even threshold]         |
| Width: 6, Height: 3                                             |
+================================================================+
```

**New Datasets:**
1. `ds_whatif_scenarios` - Multi-line chart data
2. `ds_whatif_summary` - Summary table data
3. `ds_whatif_breakeven` - Break-even analysis data

**Color Scheme:**
| Scenario | Color | Hex |
|----------|-------|-----|
| Baseline (0%) | Red | #FF0000 |
| 5% Discount | Light Green | #90EE90 |
| 10% Discount | Green | #00A972 |
| 15% Discount | Blue | #0078D4 |
| 20% Discount | Dark Blue | #00008B |

**Files to Modify:**
- `resources/dashboards/contract_consumption_monitor.json` (add new page)

---

### Phase 4: Job Integration (Week 4)

**Objective:** Integrate scenario calculation into existing jobs

**Deliverables:**
1. Add whatif calculation to `account_monitor_daily_refresh` job
2. Add whatif schema setup to `account_monitor_first_install` job

**Job Modifications:**

```yaml
# In resources/jobs.yml

# Add to first_install job
- task_key: setup_whatif_schema
  depends_on:
    - task_key: setup_forecast_schema
  notebook_task:
    notebook_path: /Workspace/${workspace.root_path}/files/sql/create_whatif_schema.sql

# Add to daily_refresh job
- task_key: refresh_whatif_scenarios
  depends_on:
    - task_key: prophet_inference
  notebook_task:
    notebook_path: /Workspace/${workspace.root_path}/files/notebooks/whatif_simulator.py
```

---

## File Summary

### New Files (8)

| File | Type | Description |
|------|------|-------------|
| `sql/create_whatif_schema.sql` | SQL | Create tables for what-if simulation |
| `sql/populate_discount_tiers.sql` | SQL | Insert default discount tier data |
| `sql/refresh_whatif_scenarios.sql` | SQL | Refresh scenario calculations |
| `notebooks/whatif_simulator.py` | Python | Simulation calculation engine |
| `docs/exploration/data_model_approach.md` | Docs | Data model research |
| `docs/exploration/simulation_engine_approach.md` | Docs | Calculation research |
| `docs/exploration/dashboard_visualization_approach.md` | Docs | Dashboard research |
| `docs/exploration/best_practices_approach.md` | Docs | Industry best practices |

### Modified Files (3)

| File | Modification |
|------|--------------|
| `resources/dashboards/contract_consumption_monitor.json` | Add What-If Analysis page |
| `resources/jobs.yml` | Add whatif tasks to jobs |
| `databricks.yml` | Add new files to sync |

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Dashboard complexity | Pre-compute all scenarios, use filters instead of dynamic input |
| Calculation accuracy | Use existing Prophet model, validate against known discounts |
| Schema migration | Separate tables, no changes to existing production tables |
| Performance | Partition by scenario_id, limit historical data range |

---

## Success Criteria

### MVP (Phase 1-3)
- [ ] 5 pre-computed discount scenarios visible in dashboard
- [ ] Multi-line comparison chart shows burndown for all scenarios
- [ ] Summary table shows savings and exhaustion dates
- [ ] Break-even threshold is clearly indicated

### Full Feature (Phase 4+)
- [ ] Scenarios auto-refresh with daily job
- [ ] Custom scenario creation via notebook
- [ ] "Sweet spot" recommendation highlighted
- [ ] Historical what-if accuracy tracking

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Schema | 3-5 days | None |
| Phase 2: Calculator | 3-5 days | Phase 1 |
| Phase 3: Dashboard | 3-5 days | Phase 2 |
| Phase 4: Jobs | 2-3 days | Phase 3 |

**Total Estimated Time:** 2-3 weeks

---

## Next Steps

1. **Review this plan** - Get approval on approach
2. **Start Phase 1** - Create schema SQL files
3. **Prototype calculator** - Test calculations with sample data
4. **Build dashboard** - Add new page and widgets
5. **Integration testing** - Run full first_install job
6. **Documentation** - Update README with what-if feature

---

## Appendix: Research Documents

- [Data Model Approach](./data_model_approach.md)
- [Simulation Engine Approach](./simulation_engine_approach.md)
- [Dashboard Visualization Approach](./dashboard_visualization_approach.md)
- [Best Practices Approach](./best_practices_approach.md)

---

*Plan created: 2026-02-07*
*Team: what-if-exploration*
*Lead: Claude (Team Lead Agent)*
