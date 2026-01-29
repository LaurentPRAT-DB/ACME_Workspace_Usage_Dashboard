# IBM Dashboard Queries - Account Name Column Fix Complete

## Summary

Fixed `customer_name` → `account_name` column reference error in the `ibm_style_dashboard_queries` notebook. The `dashboard_data` table uses `account_name` as the column name, not `customer_name`.

## Error Fixed

### Cell 17 (Query 8): Available Accounts
**Error:** `[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter with name 'customer_name' cannot be resolved. Did you mean one of the following? ['account_name', 'main'.'account_monitoring_dev'.'dashboard_data'.'salesforce_id']. SQLSTATE: 42703`

**Root Cause:** The `dashboard_data` table uses `account_name` as the column name, not `customer_name`.

**Fixes Applied:**

#### Query 4 (Cell 9) - Line 106
```sql
-- Before (WRONG):
SELECT
  customer_name,
  ...
FROM main.account_monitoring_dev.dashboard_data
GROUP BY customer_name, cloud_provider

-- After (CORRECT):
SELECT
  account_name,
  ...
FROM main.account_monitoring_dev.dashboard_data
GROUP BY account_name, cloud_provider
```

#### Query 8 (Cell 17) - Line 195
```sql
-- Before (WRONG):
SELECT DISTINCT
  customer_name as account_name,
  salesforce_id
FROM main.account_monitoring_dev.dashboard_data
ORDER BY customer_name;

-- After (CORRECT):
SELECT DISTINCT
  account_name,
  salesforce_id
FROM main.account_monitoring_dev.dashboard_data
ORDER BY account_name;
```

**Explanation:** The `dashboard_data` table uses `account_name` as the standard column name. Query 3 correctly uses `customer_name` from the `account_metadata` table, but queries against `dashboard_data` must use `account_name`.

## Complete Query Comparisons

### Query 4 - Complete Before/After

**Before (Cell 9):**
```sql
SELECT
  customer_name,                                -- ❌ Should be account_name
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 0) as dbu,
  ROUND(SUM(list_cost), 2) as list_price,
  ROUND(SUM(actual_cost), 2) as discounted_price,
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider          -- ❌ Should be account_name
ORDER BY cloud_provider;
```

**After (Cell 9):**
```sql
SELECT
  account_name,                                 -- ✅ Correct column name
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 0) as dbu,
  ROUND(SUM(list_cost), 2) as list_price,
  ROUND(SUM(actual_cost), 2) as discounted_price,
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY account_name, cloud_provider           -- ✅ Correct column name
ORDER BY cloud_provider;
```

### Query 8 - Complete Before/After

**Before (Cell 17):**
```sql
SELECT DISTINCT
  customer_name as account_name,                -- ❌ customer_name doesn't exist
  salesforce_id
FROM main.account_monitoring_dev.dashboard_data
ORDER BY customer_name;                         -- ❌ customer_name doesn't exist
```

**After (Cell 17):**
```sql
SELECT DISTINCT
  account_name,                                 -- ✅ Use account_name directly
  salesforce_id
FROM main.account_monitoring_dev.dashboard_data
ORDER BY account_name;                          -- ✅ Correct column name
```

## Schema Reference

### dashboard_data table columns:
- ✅ `account_name` - Customer/Account name (standard column name)
- ✅ `actual_cost` - Actual cost at list price
- ✅ `list_cost` - Total cost at list price
- ✅ `account_id` - Account identifier
- ✅ `salesforce_id` - Salesforce account ID
- ✅ `cloud_provider` - Cloud provider
- ✅ `usage_quantity` - DBU/units consumed
- ❌ `customer_name` - **Does NOT exist in dashboard_data**

### account_metadata table columns:
- ✅ `customer_name` - Customer name (different naming convention)
- ✅ `salesforce_id` - Salesforce account ID
- ✅ `business_unit_l0`, `business_unit_l1`, etc.
- ✅ `account_executive`, `solutions_architect`

**Key Insight:** Different tables use different naming conventions:
- `account_metadata` → uses `customer_name`
- `dashboard_data` → uses `account_name`

## Changes Summary

| Query | Cell | Column Changed | Location |
|-------|------|----------------|----------|
| Query 4 | 9 | `customer_name` → `account_name` | SELECT, GROUP BY |
| Query 8 | 17 | `customer_name as account_name` → `account_name` | SELECT, ORDER BY |

## Version Update

- **Current:** 1.5.6 (Build: 2026-01-29-003)
- **Note:** Version not incremented (cosmetic fix, same logical intent)

## Deployment Checklist

- [ ] **Commit:** Changes committed to git
- [ ] **Push:** Pushed to GitHub repository
- [ ] **Deploy:** Deploy to Databricks workspace using bundle
- [ ] **Verify:** Test both queries in notebook

## Testing Instructions

1. **Open the notebook in your workspace:**
   ```
   /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/notebooks/ibm_style_dashboard_queries
   ```

2. **Run Cell 9 (Query 4 - Total Spend in Timeframe):**
   - Should execute successfully
   - Returns spending breakdown by cloud provider
   - No "customer_name" error

3. **Run Cell 17 (Query 8 - Available Accounts):**
   - Should execute successfully
   - Returns list of distinct account names with salesforce IDs
   - No "customer_name" error

## Expected Results

### Query 4 Output:
| account_name | cloud | start_date | end_date | dbu | list_price | discounted_price | revenue |
|--------------|-------|------------|----------|-----|------------|------------------|---------|
| Customer 1   | aws   | 2025-01-30 | 2026-01-29 | 1000 | $50,000 | $50,000 | $50,000 |
| Customer 1   | azure | 2025-01-30 | 2026-01-29 | 500 | $25,000 | $25,000 | $25,000 |

### Query 8 Output:
| account_name | salesforce_id |
|--------------|---------------|
| Customer 1   | 0014N00001... |
| Customer 2   | 0014N00002... |

## Why This Fix Works

- **Correct Column Name:** Using `account_name` matches the actual schema of `dashboard_data` table
- **Simplified Query 8:** No need for aliasing since the column is already named `account_name`
- **Consistency:** All queries against `dashboard_data` now use the correct column name

## Related Context

### Previous Fixes on Same Notebook:
- ✅ Fixed `discounted_cost` → `actual_cost` (Cell 9)
- ✅ Fixed Query 8 source table: `account_metadata` → `dashboard_data`
- ✅ Fixed SQL syntax in `lakeview_dashboard_queries`

### This Fix:
- ✅ Fixed column name: `customer_name` → `account_name` in queries against `dashboard_data`

## Next Steps

1. **Commit the changes:**
   ```bash
   git add notebooks/ibm_style_dashboard_queries.sql
   git commit -m "Fix account_name column references in IBM queries"
   ```

2. **Push to GitHub:**
   ```bash
   git push
   ```

3. **Deploy to Databricks:**
   ```bash
   databricks bundle deploy
   ```

4. **Verify in workspace:**
   - Run Cell 9 (Query 4)
   - Run Cell 17 (Query 8)
   - Confirm no errors

## Conclusion

The `customer_name` → `account_name` column references have been corrected in both Query 4 and Query 8. The notebook is now ready for deployment and testing.

**Status:** ✅ CODE FIXED - Ready for Deployment

---

**Remember:** Deploy workflow = `git push` + `databricks bundle deploy` ✅
