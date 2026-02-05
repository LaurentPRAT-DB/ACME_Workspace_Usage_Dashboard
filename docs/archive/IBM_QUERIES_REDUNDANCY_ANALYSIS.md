# IBM Dashboard Queries - Redundancy Analysis

**Date:** 2026-01-29
**Analyzed by:** Claude Code
**Status:** LARGELY REDUNDANT

---

## Executive Summary

**Conclusion:** The `ibm_style_dashboard_queries.sql` file is **largely redundant** with `lakeview_dashboard_queries.sql`. The Lakeview queries provide more comprehensive coverage with 15 queries vs 9 IBM queries, and most IBM queries are either duplicates or simplified versions of Lakeview queries.

**Recommendation:**
- **Keep:** `lakeview_dashboard_queries.sql` (primary/comprehensive)
- **Consider removing:** `ibm_style_dashboard_queries.sql` (redundant unless single-page layout is specifically needed)

---

## Detailed Query Comparison

### Query-by-Query Analysis

| IBM Query | Lakeview Equivalent | Status | Notes |
|-----------|---------------------|--------|-------|
| **1. Top Metrics** | Query 8: Account Overview | ✅ REDUNDANT | Exact same: SKU count, workspace count, date |
| **2. Data Freshness** | Query 9: Data Freshness | ✅ REDUNDANT | Identical queries for data quality check |
| **3. Account Info** | - | ⚠️ UNIQUE | Uses account_metadata table (not in Lakeview) |
| **4. Total Spend** | Query 10: Total Spend | ⚠️ SIMILAR | IBM adds 'revenue' field; otherwise same |
| **5. Contracts Table** | Query 2: Contract Summary | ✅ REDUNDANT | Lakeview version is MORE detailed |
| **6. Burndown Chart** | Query 1: Burndown Chart | ✅ REDUNDANT | Lakeview version is MORE detailed |
| **7. Combined Burndown** | - | ⚠️ UNIQUE | Aggregates all contracts (not in Lakeview) |
| **8. Account List** | Query 15: Dashboard Data | ⚠️ SIMILAR | Both provide filter data |
| **9. Data Check** | - | ⚠️ UNIQUE | Validation query (not in Lakeview) |

### Summary Statistics

- **Total IBM Queries:** 9
- **Total Lakeview Queries:** 15
- **Redundant:** 4 (44%)
- **Similar:** 3 (33%)
- **Unique:** 2 (22%)

---

## Dashboard Purpose Comparison

### Lakeview Dashboard (`lakeview_dashboard_queries.sql`)

**Purpose:** Comprehensive multi-page analytics dashboard
**Pages:** 3 (Contract Burndown, Account Overview, Usage Analytics)
**Visualizations:** 15
**Features:**
- ✅ Contract burndown with pace analysis
- ✅ Daily consumption tracking
- ✅ Pace distribution pie chart
- ✅ Monthly consumption trends
- ✅ Top workspaces detailed analysis
- ✅ Contract health indicators
- ✅ Product category breakdown
- ✅ Top SKUs analysis

**Target Users:** Analysts, Account Managers, Finance Teams

---

### IBM Style Dashboard (`ibm_style_dashboard_queries.sql`)

**Purpose:** Simplified single-page executive summary
**Pages:** 1 (Single page layout)
**Visualizations:** 8-9
**Features:**
- ✅ Top metrics counters
- ✅ Basic data freshness
- ✅ Account info table
- ✅ Simple spending breakdown
- ✅ Basic contracts table
- ✅ Basic burndown chart

**Target Users:** Executives, Quick Overview

---

## Data Coverage Analysis

### What IBM Queries Provide

| Data Category | IBM Coverage | Lakeview Coverage | Winner |
|---------------|--------------|-------------------|--------|
| **Top Metrics** | ✅ Basic | ✅ Basic | TIE |
| **Data Quality** | ✅ Basic | ✅ Basic | TIE |
| **Account Info** | ✅ Yes | ❌ No | IBM |
| **Spending** | ✅ Basic | ✅ Detailed + Trends | Lakeview |
| **Contracts** | ✅ Basic | ✅ Detailed + Health | Lakeview |
| **Burndown** | ✅ Basic | ✅ Advanced + Projections | Lakeview |
| **Workspaces** | ❌ No | ✅ Top 10 Analysis | Lakeview |
| **SKUs** | ❌ No | ✅ Top 10 Analysis | Lakeview |
| **Product Category** | ❌ No | ✅ Yes | Lakeview |
| **Monthly Trends** | ❌ No | ✅ Yes | Lakeview |
| **Pace Analysis** | ❌ No | ✅ Yes | Lakeview |

---

## Unique IBM Queries Deep Dive

### Query 3: Account Info
```sql
SELECT customer_name, salesforce_id, business_unit_l0, business_unit_l1,
       business_unit_l2, business_unit_l3, account_executive,
       solutions_architect, delivery_solutions_architect
FROM main.account_monitoring_dev.account_metadata
```

**Status:** Unique
**Value:** Shows organizational hierarchy and team assignments
**Replacement:** Could be added to Lakeview as Query 16

---

### Query 7: Combined Burndown (All Contracts)
```sql
SELECT usage_date as date,
       SUM(commitment) as commit,
       SUM(cumulative_cost) as consumption
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY usage_date
```

**Status:** Unique
**Value:** Shows aggregated view of all contracts
**Replacement:** Could be added to Lakeview as alternative view

---

### Query 9: Data Check (Verification)
```sql
-- Verify all tables have data
SELECT 'dashboard_data' as table_name, COUNT(*) as row_count,
       MIN(usage_date) as min_date, MAX(usage_date) as max_date
FROM main.account_monitoring_dev.dashboard_data
UNION ALL ...
```

**Status:** Unique
**Value:** Validation/troubleshooting query
**Replacement:** Could be in `post_deployment_validation.py`

---

## Redundancy Details

### Fully Redundant Queries

#### IBM Query 1 = Lakeview Query 8 (Top Metrics)
Both execute:
```sql
SELECT COUNT(DISTINCT sku_name) as top_sku_count,
       COUNT(DISTINCT workspace_id) as top_workspace_count,
       MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
```
**Verdict:** 100% identical

---

#### IBM Query 2 = Lakeview Query 9 (Data Freshness)
Both execute:
```sql
SELECT 'Consumption' as source, MAX(usage_date) as latest_date,
       CASE WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2
            THEN 'True' ELSE 'False' END as verified
FROM system.billing.usage
UNION ALL ...
```
**Verdict:** 100% identical

---

#### IBM Query 5 < Lakeview Query 2 (Contracts)

**IBM Version (Simpler):**
```sql
SELECT cloud_provider as platform, contract_id, start_date, end_date,
       CONCAT('$', FORMAT_NUMBER(commitment, 0)) as total_value,
       CONCAT('$', FORMAT_NUMBER(total_consumed, 2)) as consumed,
       CONCAT(ROUND(consumed_pct, 1), '%') as consumed_pct
FROM main.account_monitoring_dev.contract_burndown_summary
```

**Lakeview Version (More Detailed):**
```sql
SELECT contract_id, cloud_provider, start_date, end_date,
       CONCAT('USD ', FORMAT_NUMBER(commitment, 0)) as total_value,
       CONCAT('USD ', FORMAT_NUMBER(total_consumed, 2)) as consumed,
       CONCAT('USD ', FORMAT_NUMBER(budget_remaining, 2)) as remaining,
       CONCAT(ROUND(consumed_pct, 1), '%') as consumed_pct,
       pace_status, days_remaining, projected_end_date
FROM main.account_monitoring_dev.contract_burndown_summary
```

**Verdict:** Lakeview provides MORE information (pace_status, days_remaining, projected_end_date, budget_remaining)

---

#### IBM Query 6 < Lakeview Query 1 (Burndown Chart)

**IBM Version (Basic):**
```sql
SELECT usage_date as date, contract_id,
       ROUND(commitment, 2) as commit,
       ROUND(cumulative_cost, 2) as consumption
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
```

**Lakeview Version (Advanced):**
```sql
SELECT contract_id,
       CONCAT(contract_id, ' (USD ', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
       usage_date as date,
       ROUND(cumulative_cost, 2) as actual_consumption,
       ROUND(projected_linear_burn, 2) as ideal_consumption,
       ROUND(commitment, 2) as contract_value,
       ROUND(budget_pct_consumed, 1) as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
```

**Verdict:** Lakeview provides MORE information (projected_linear_burn, contract_label, pct_consumed)

---

## What Would Be Lost If IBM Queries Were Removed

### Minimal Impact

1. **Account Info Table** - Could be added as Query 16 in Lakeview
2. **Combined Burndown** - Useful but not critical (individual contracts more informative)
3. **Data Check Query** - Validation query (belongs in validation notebook anyway)

### Dashboard Layout

- IBM provides a **single-page layout** option
- Lakeview uses a **3-page layout** (more comprehensive)
- If single-page executive view is required, keep IBM queries
- If detailed analytics are more important, Lakeview is sufficient

---

## Recommendations

### Option 1: Remove IBM Queries (Recommended)

**Actions:**
1. Delete `notebooks/ibm_style_dashboard_queries.sql`
2. Add Query 16 to Lakeview: Account Info
3. Add Query 17 to Lakeview: Combined Burndown (optional)
4. Move Data Check query to `post_deployment_validation.py`
5. Update documentation to reference only Lakeview

**Benefits:**
- ✅ Single source of truth for queries
- ✅ Reduces maintenance burden
- ✅ Clearer for new team members
- ✅ Lakeview is more comprehensive

**Risks:**
- ⚠️ Lose single-page layout option
- ⚠️ May need to recreate if executives prefer simple view

---

### Option 2: Keep IBM Queries (Alternative)

**When to keep:**
- Executives specifically request single-page dashboard
- Team prefers having both layout options
- IBM layout is actively used by stakeholders

**Actions:**
1. Document clearly that IBM queries are simplified alternatives
2. Add note about query overlap in both files
3. Keep both maintained when schema changes

---

### Option 3: Merge Best of Both (Middle Ground)

**Actions:**
1. Keep Lakeview as primary (15 queries)
2. Add the 2 unique IBM queries to Lakeview:
   - Query 16: Account Info
   - Query 17: Combined Burndown (optional)
3. Create separate layout guide for single-page option
4. Remove `ibm_style_dashboard_queries.sql`

**Benefits:**
- ✅ Best of both worlds
- ✅ Single query file
- ✅ Layout flexibility via documentation

---

## Migration Path (If Removing IBM Queries)

### Step 1: Extract Unique Queries

Add to `lakeview_dashboard_queries.sql`:

```sql
-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Query 16: Account Information
-- MAGIC **Dataset:** account_info
-- MAGIC **Visualization:** Table
-- MAGIC **Purpose:** Organizational hierarchy and team assignments

-- COMMAND ----------

SELECT
  customer_name as `Customer`,
  salesforce_id as `Salesforce ID`,
  CONCAT_WS(' > ', business_unit_l0, business_unit_l1, business_unit_l2, business_unit_l3) as `Business Unit`,
  account_executive as `AE`,
  solutions_architect as `SA`,
  delivery_solutions_architect as `DSA`
FROM main.account_monitoring_dev.account_metadata
LIMIT 1;
```

---

### Step 2: Update Documentation

Files to update:
- `docs/CREATE_LAKEVIEW_DASHBOARD.md` - Add Query 16 instructions
- `docs/IBM_DASHBOARD_QUICKSTART.md` - Mark as deprecated or remove
- `docs/CREATE_IBM_STYLE_DASHBOARD.md` - Mark as deprecated or remove
- `README.md` - Remove IBM dashboard references
- `START_HERE.md` - Update to reference only Lakeview

---

### Step 3: Update Asset Bundle

Edit `databricks.yml`:
- Remove IBM queries notebook from resources (if listed)
- Keep only `lakeview_dashboard_queries`

---

### Step 4: Archive or Delete

```bash
# Option A: Archive
mkdir -p archive
git mv notebooks/ibm_style_dashboard_queries.sql archive/
git commit -m "Archive IBM dashboard queries (redundant with Lakeview)"

# Option B: Delete
git rm notebooks/ibm_style_dashboard_queries.sql
git commit -m "Remove redundant IBM dashboard queries"
```

---

## Testing After Removal

### Verification Checklist

- [ ] Lakeview dashboard displays all required data
- [ ] No broken references to IBM queries in documentation
- [ ] Asset bundle deploys successfully
- [ ] All stakeholders informed of change
- [ ] Alternative single-page layout documented (if needed)

---

## Conclusion

The `ibm_style_dashboard_queries.sql` file contains **largely redundant queries** compared to the more comprehensive `lakeview_dashboard_queries.sql`.

**Key Points:**
- 4 queries are 100% redundant (44%)
- 3 queries are similar but Lakeview is more detailed (33%)
- Only 2 queries are truly unique (22%)
- Lakeview provides 6 additional queries not in IBM version

**Final Recommendation:**
✅ **Remove** `ibm_style_dashboard_queries.sql` and add the 2 unique queries to Lakeview (Query 16: Account Info, Query 17: Combined Burndown if needed).

This consolidates all queries into a single source of truth while preserving all valuable functionality.

---

**Analysis Date:** 2026-01-29
**Files Analyzed:**
- `/notebooks/ibm_style_dashboard_queries.sql` (259 lines, 9 queries)
- `/notebooks/lakeview_dashboard_queries.sql` (405 lines, 15 queries)
- `/notebooks/account_monitor_notebook.py` (reference)
- `/docs/IBM_DASHBOARD_QUICKSTART.md` (reference)
- `/docs/CREATE_LAKEVIEW_DASHBOARD.md` (reference)
