# Query Fixes Analysis

## Issue Identified

After comparing the working queries in `account_monitor_notebook.py` with the dashboard query notebooks, I found field name mismatches in `ibm_style_dashboard_queries.sql`.

## Root Cause

The `dashboard_data` table created in `account_monitor_notebook.py` (lines 640-677) uses these field names:

```sql
CREATE OR REPLACE TABLE account_monitoring.dashboard_data AS
SELECT
  ...
  u.usage_quantity * COALESCE(lp.pricing.default, 0) as actual_cost,
  lp.pricing.default as list_price_per_unit,
  lp.pricing.default as discounted_price_per_unit,
  u.usage_quantity * COALESCE(lp.pricing.default, 0) as list_cost,
  u.usage_quantity * COALESCE(lp.pricing.default, 0) as discounted_cost,
  ...
```

**Key Fields:**
- `actual_cost` - Cost at actual/list price
- `list_price_per_unit` - Price per unit
- `discounted_price_per_unit` - Discounted price per unit
- `list_cost` - Total cost at list price (aggregated)
- `discounted_cost` - Total cost at discounted price (aggregated)

## Bug in ibm_style_dashboard_queries.sql

**Location:** Line 94-96 (Query 4: Total Spend in Timeframe)

**Current (INCORRECT):**
```sql
SELECT
  customer_name,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 0) as dbu,
  ROUND(SUM(list_price), 2) as list_price,        -- ❌ WRONG: field doesn't exist
  ROUND(SUM(discounted_price), 2) as discounted_price,  -- ❌ WRONG: field doesn't exist
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
```

**Should be (CORRECT):**
```sql
SELECT
  customer_name,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 0) as dbu,
  ROUND(SUM(list_cost), 2) as list_price,        -- ✅ CORRECT
  ROUND(SUM(discounted_cost), 2) as discounted_price,  -- ✅ CORRECT
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
```

## Verification

### lakeview_dashboard_queries.sql
✅ **NO ISSUES** - All queries use correct field names from dashboard_data table:
- Uses `actual_cost` consistently
- Uses `usage_quantity` for DBU calculations
- Uses `product_category` (which exists in dashboard_data)

### ibm_style_dashboard_queries.sql
❌ **HAS ISSUE** - Query 4 uses incorrect field names:
- `list_price` should be `list_cost`
- `discounted_price` should be `discounted_cost`

## Error Symptoms

When running Query 4 in ibm_style_dashboard_queries.sql, you would see:
```
[UNRESOLVED_COLUMN] Column 'list_price' does not exist
[UNRESOLVED_COLUMN] Column 'discounted_price' does not exist
```

## Fix Required

Update `notebooks/ibm_style_dashboard_queries.sql` line 94-96.
