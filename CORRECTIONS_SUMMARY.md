# Schema Corrections Summary

## What Was Fixed

This document summarizes the corrections made after verifying the actual Databricks system table schemas using official documentation.

## Critical Schema Corrections

### 1. ❌ REMOVED: Non-Existent Columns

**system.billing.usage table DOES NOT have:**
- ❌ `list_price_per_unit` - This column does not exist
- ❌ `usage_metadata.total_price` - This field does not exist in the usage_metadata struct
- ❌ `default_price_per_unit` - Not in system.billing.usage

### 2. ✅ CORRECTED: Pricing Structure

**WRONG** (Original):
```sql
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
```

**CORRECT** (Fixed):
```sql
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
```

### 3. ✅ CORRECTED: Pricing Struct Access

**WRONG** (Original):
```sql
lp.pricing.default_price_per_unit
```

**CORRECT** (Fixed):
```sql
CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
```

The `pricing` struct has these fields:
- `pricing.default` - Standard list price (STRING)
- `pricing.promotional.default` - Promotional price (STRING)
- `pricing.effective_list.default` - Effective price used for calculations (STRING)

### 4. ✅ ADDED: Record Type Filtering

**IMPORTANT**: The billing.usage table includes correction records (RETRACTION, RESTATEMENT). Always filter for ORIGINAL records:

```sql
WHERE record_type = 'ORIGINAL'
```

### 5. ✅ CORRECTED: Unity Catalog References

**WRONG** (Original):
```sql
CREATE DATABASE IF NOT EXISTS account_monitoring;
CREATE TABLE account_monitoring.contracts ...
```

**CORRECT** (Fixed):
```sql
USE CATALOG main;  -- or your catalog name
CREATE SCHEMA IF NOT EXISTS main.account_monitoring;
CREATE TABLE main.account_monitoring.contracts ...
```

### 6. ✅ CORRECTED: Time Column Names

**WRONG** (Original):
```sql
u.usage_date  -- using generic date
```

**CORRECT** (Fixed):
```sql
u.usage_start_time  -- actual timestamp when usage started
u.usage_end_time    -- actual timestamp when usage ended
u.usage_date        -- date field for partitioning (USE THIS for filtering)
```

### 7. ✅ CORRECTED: Cost Calculation

**WRONG** (Original):
```sql
SUM(usage_metadata.total_price) as total_cost
```

**CORRECT** (Fixed):
```sql
SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
```

## File-by-File Changes

### ✅ NEW FILES CREATED

1. **SCHEMA_REFERENCE.md** - Complete official schema documentation
2. **account_monitor_queries_CORRECTED.sql** - All queries fixed with correct schema
3. **setup_account_monitor_UC.py** - Unity Catalog-enabled setup script
4. **CORRECTIONS_SUMMARY.md** - This file

### ⚠️ OLD FILES (DO NOT USE)

1. **account_monitor_queries.sql** - Uses incorrect schema
2. **setup_account_monitor.py** - Does not use Unity Catalog properly

## Migration Guide

### If You Haven't Started Yet

✅ **Use the corrected files:**
- `SCHEMA_REFERENCE.md` - For schema reference
- `account_monitor_queries_CORRECTED.sql` - For queries
- `setup_account_monitor_UC.py` - For setup

### If You Already Created Tables

Run these queries to verify your data:

```sql
-- Test 1: Check if you have the correct pricing join
SELECT
  u.sku_name,
  u.usage_quantity,
  lp.pricing.effective_list.default as price,
  u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)) as cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL'
LIMIT 5;

-- Test 2: Verify Unity Catalog tables exist
SHOW TABLES IN main.account_monitoring;
```

## Key Learnings

### 1. Always Join on Multiple Conditions

When joining usage with list_prices:
- ✅ Match on `sku_name`
- ✅ Match on `cloud`
- ✅ Match on `usage_unit`
- ✅ Match on time range (price validity period)

### 2. Type Casting is Critical

Pricing fields are STRING type, must cast to DECIMAL:
```sql
CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
```

### 3. Filter by Date, Join by Timestamp

- Use `usage_date` for WHERE clauses (partitioned, fast)
- Use `usage_end_time` for JOIN conditions (precision matching)

### 4. Handle Corrections Properly

Options:
```sql
-- Option 1: Exclude corrections
WHERE record_type = 'ORIGINAL'

-- Option 2: Include corrections (retracted records have negative quantity)
GROUP BY <dimensions>
-- Corrections will automatically net out
```

### 5. Unity Catalog is Required

All custom tables should use Unity Catalog:
```sql
<catalog>.<schema>.<table>

-- Example:
main.account_monitoring.contracts
main.account_monitoring.account_metadata
main.account_monitoring.dashboard_data
```

## Performance Tips

### 1. Always Filter on usage_date First

```sql
-- GOOD - Uses partition pruning
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.cloud = 'aws'

-- BAD - Full table scan
WHERE u.cloud = 'aws'
  AND u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
```

### 2. Use Appropriate Data Types

```sql
-- GOOD - Proper decimal precision
CAST(pricing.effective_list.default AS DECIMAL(20,10))

-- BAD - Could lose precision
CAST(pricing.effective_list.default AS DOUBLE)
```

### 3. Pre-aggregate When Possible

```sql
-- Create a summary table for faster queries
CREATE TABLE main.account_monitoring.daily_summary AS
SELECT
  usage_date,
  cloud,
  workspace_id,
  SUM(usage_quantity * CAST(pricing.effective_list.default AS DECIMAL(20,10))) as daily_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON <join conditions>
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
  AND record_type = 'ORIGINAL'
GROUP BY usage_date, cloud, workspace_id;
```

## Verification Checklist

Before using your dashboard, verify:

- [ ] System tables are accessible
- [ ] Pricing JOIN includes all 5 conditions
- [ ] Cost calculation uses `pricing.effective_list.default`
- [ ] Filtering on `record_type = 'ORIGINAL'`
- [ ] All custom tables use Unity Catalog (`main.account_monitoring.*`)
- [ ] Type casting for pricing (STRING → DECIMAL)
- [ ] Using `usage_date` for WHERE clauses
- [ ] Using `usage_end_time` for JOIN timing

## Quick Test Query

Run this to verify everything works:

```sql
-- Complete test query
WITH usage_with_cost AS (
  SELECT
    u.usage_date,
    u.cloud,
    u.workspace_id,
    u.sku_name,
    u.usage_quantity,
    CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)) as price_per_unit,
    u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)) as cost
  FROM system.billing.usage u
  LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name
    AND u.cloud = lp.cloud
    AND u.usage_unit = lp.usage_unit
    AND u.usage_end_time >= lp.price_start_time
    AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
  WHERE u.usage_date = CURRENT_DATE() - 1
    AND u.record_type = 'ORIGINAL'
)
SELECT
  usage_date,
  cloud,
  COUNT(*) as record_count,
  SUM(usage_quantity) as total_dbu,
  ROUND(SUM(cost), 2) as total_cost,
  ROUND(AVG(cost), 2) as avg_cost
FROM usage_with_cost
GROUP BY usage_date, cloud;
```

If this query runs successfully and returns costs, your setup is correct!

## Documentation References

Official Databricks documentation used for verification:

1. [Billable usage system table reference](https://docs.databricks.com/aws/en/admin/system-tables/billing)
2. [Pricing system table reference](https://docs.databricks.com/aws/en/admin/system-tables/pricing)
3. [Monitor costs using system tables](https://docs.databricks.com/aws/en/admin/usage/system-tables)

## Summary

✅ **What Changed:**
- Cost calculation now uses proper JOIN with list_prices
- Pricing struct accessed correctly
- Unity Catalog properly implemented
- Record type filtering added
- All column names verified against actual schema

⚠️ **Action Required:**
- Use `account_monitor_queries_CORRECTED.sql` instead of the original
- Run `setup_account_monitor_UC.py` for Unity Catalog setup
- Update any existing queries to use corrected schema
- Refer to `SCHEMA_REFERENCE.md` for accurate field names

🎯 **Result:**
- Queries will now work with actual Databricks system tables
- Cost calculations will be accurate
- Unity Catalog provides proper governance
- Performance optimized with correct filtering
