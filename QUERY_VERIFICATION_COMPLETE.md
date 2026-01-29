# Query Verification Complete

## Summary

Analyzed all three notebooks to identify and fix schema/field name issues by comparing against the working `account_monitor_notebook.py`.

## Files Analyzed

1. ✅ **account_monitor_notebook.py** (746 lines) - Reference/Working queries
2. ✅ **lakeview_dashboard_queries.sql** (387 lines) - Verified correct
3. ✅ **ibm_style_dashboard_queries.sql** (241 lines) - Fixed issue

## Issue Found and Fixed

### ibm_style_dashboard_queries.sql

**Query 4: Total Spend in Timeframe (Lines 88-100)**

**Problem:** Incorrect field names used when querying `dashboard_data` table

**Fix Applied:**
- Line 94: Changed `SUM(list_price)` → `SUM(list_cost)`
- Line 95: Changed `SUM(discounted_price)` → `SUM(discounted_cost)`

**Before:**
```sql
  ROUND(SUM(list_price), 2) as list_price,           -- ❌ Field doesn't exist
  ROUND(SUM(discounted_price), 2) as discounted_price, -- ❌ Field doesn't exist
```

**After:**
```sql
  ROUND(SUM(list_cost), 2) as list_price,             -- ✅ Correct field name
  ROUND(SUM(discounted_cost), 2) as discounted_price,  -- ✅ Correct field name
```

## Field Name Reference

Based on `account_monitor_notebook.py` (lines 640-677), the `dashboard_data` table contains:

### Usage Fields:
- `usage_date` - Date of usage
- `usage_quantity` - Amount of DBUs/units used
- `usage_unit` - Unit of measurement
- `sku_name` - SKU identifier
- `workspace_id` - Workspace identifier
- `account_id` - Account identifier

### Cost Fields:
- `actual_cost` - Cost at actual/list price (usage_quantity * list_price_per_unit)
- `list_cost` - Same as actual_cost, total cost at list price
- `discounted_cost` - Total cost at discounted price (currently same as list_cost)
- `list_price_per_unit` - Price per unit (from list_prices table)
- `discounted_price_per_unit` - Discounted price per unit (currently same as list)

### Metadata Fields:
- `customer_name` - Customer name (from account_metadata)
- `cloud_provider` - Cloud provider (aws/azure/gcp)
- `product_category` - Derived category (All Purpose Compute, Jobs Compute, DLT, SQL, etc.)
- `salesforce_id`, `business_unit_l*`, `account_executive`, etc. - From account_metadata

## Query Validation

### lakeview_dashboard_queries.sql

All 15 queries validated ✅:

| Query # | Purpose | Status | Notes |
|---------|---------|--------|-------|
| 1 | Contract Burndown Chart | ✅ | Uses contract_burndown table |
| 2 | Contract Summary | ✅ | Uses contract_burndown_summary |
| 3 | Daily Consumption | ✅ | Uses contract_burndown |
| 4 | Pace Distribution | ✅ | Uses contract_burndown_summary |
| 5 | Monthly Consumption | ✅ | Uses contract_burndown |
| 6 | Top Workspaces | ✅ | Uses dashboard_data with correct fields |
| 7 | Contract Detailed Analysis | ✅ | Uses contract_burndown_summary |
| 8 | Account Overview | ✅ | Uses system.billing.usage directly |
| 9 | Data Freshness | ✅ | Uses system.billing.usage |
| 10 | Total Spend by Cloud | ✅ | Uses dashboard_data with correct fields |
| 11 | Monthly Cost Trend | ✅ | Uses dashboard_data |
| 12 | Top Consuming Workspaces | ✅ | Uses dashboard_data |
| 13 | Top Consuming SKUs | ✅ | Uses dashboard_data |
| 14 | Cost by Product Category | ✅ | Uses dashboard_data with product_category |
| 15 | Dashboard Data Base | ✅ | Direct table query |

### ibm_style_dashboard_queries.sql

All 9 queries validated ✅:

| Query # | Purpose | Status | Notes |
|---------|---------|--------|-------|
| 1 | Top Metrics | ✅ | Uses system.billing.usage |
| 2 | Latest Data Dates | ✅ | Uses system.billing.usage |
| 3 | Account Info | ✅ | Uses account_metadata |
| 4 | Total Spend | ✅ **FIXED** | Changed list_price→list_cost, discounted_price→discounted_cost |
| 5 | Contracts Table | ✅ | Uses contract_burndown_summary |
| 6 | Burndown Chart | ✅ | Uses contract_burndown |
| 7 | Combined Burndown | ✅ | Uses contract_burndown |
| 8 | Account List | ✅ | Uses account_metadata |
| 9 | Data Check | ✅ | Verification query |

## Testing Recommendations

To verify the fixes:

```sql
-- 1. Verify dashboard_data table schema
DESCRIBE main.account_monitoring_dev.dashboard_data;

-- 2. Test the fixed query (Query 4 from ibm_style_dashboard_queries.sql)
SELECT
  customer_name,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 0) as dbu,
  ROUND(SUM(list_cost), 2) as list_price,
  ROUND(SUM(discounted_cost), 2) as discounted_price,
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider
ORDER BY cloud_provider;

-- 3. Compare with working query from account_monitor_notebook
-- Should return same results
```

## Common Patterns from Working Queries

### Joining with list_prices:
```sql
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_date >= lp.price_start_time
  AND (u.usage_date < lp.price_end_time OR lp.price_end_time IS NULL)
```

### Calculating costs:
```sql
-- Actual cost
u.usage_quantity * COALESCE(lp.pricing.default, 0) as actual_cost

-- List cost (same as actual in current implementation)
u.usage_quantity * COALESCE(lp.pricing.default, 0) as list_cost

-- Discounted cost (15% discount in example)
u.usage_quantity * COALESCE(lp.pricing.default, 0) * 0.85 as discounted_cost
```

### Product categorization:
```sql
CASE
  WHEN sku_name LIKE '%ALL_PURPOSE%' THEN 'All Purpose Compute'
  WHEN sku_name LIKE '%JOBS%' THEN 'Jobs Compute'
  WHEN sku_name LIKE '%DLT%' OR sku_name LIKE '%DELTA_LIVE_TABLES%' THEN 'Delta Live Tables'
  WHEN sku_name LIKE '%SQL%' THEN 'SQL Warehouse'
  WHEN sku_name LIKE '%INFERENCE%' OR sku_name LIKE '%MODEL_SERVING%' THEN 'Model Serving'
  WHEN sku_name LIKE '%VECTOR_SEARCH%' THEN 'Vector Search'
  WHEN sku_name LIKE '%SERVERLESS%' THEN 'Serverless'
  ELSE 'Other'
END as product_category
```

## Conclusion

✅ **All queries verified and fixed**
- 1 issue found and corrected in `ibm_style_dashboard_queries.sql`
- 0 issues found in `lakeview_dashboard_queries.sql`
- All field names now match the schema defined in `account_monitor_notebook.py`
- All queries should now execute successfully

## Next Steps

1. Run both notebooks to verify queries execute without errors
2. Verify query results match expected data
3. Test dashboard visualizations with updated queries
4. Consider committing the fix to version control
