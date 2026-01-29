# Notebook Version and Metadata Update

## Summary

Added version tracking and comprehensive metadata to SQL query notebooks to match the Python notebook standards and ensure proper documentation.

## Changes Applied

### Version Information Added

Both SQL notebooks now include:
- **Version:** 1.5.5 (Build: 2026-01-29-002)
- **Data Sources:** Complete list of tables used
- **Schema Fields:** Documentation of key fields and their meanings
- **Last Updated:** Change log with date

### Files Updated

#### 1. notebooks/lakeview_dashboard_queries.sql

**Added Metadata:**
```markdown
**Version:** 1.5.5 (Build: 2026-01-29-002)

**Data Sources:**
- system.billing.usage - Usage data and costs
- main.account_monitoring_dev.dashboard_data - Pre-aggregated dashboard data
- main.account_monitoring_dev.contract_burndown - Contract consumption tracking
- main.account_monitoring_dev.contract_burndown_summary - Latest contract status

**Schema Fields Used:**
- actual_cost - Cost at list price
- list_cost - Total cost at list price (aggregated)
- discounted_cost - Total cost at discounted price (aggregated)
- usage_quantity - DBU/units consumed
- product_category - Derived product category

**Last Updated:** 2026-01-29 - Fixed field names, added version tracking
```

#### 2. notebooks/ibm_style_dashboard_queries.sql

**Added Metadata:**
```markdown
**Version:** 1.5.5 (Build: 2026-01-29-002)

**Data Sources:**
- system.billing.usage - Usage data and costs
- main.account_monitoring_dev.dashboard_data - Pre-aggregated dashboard data
- main.account_monitoring_dev.contract_burndown - Contract consumption tracking
- main.account_monitoring_dev.contract_burndown_summary - Latest contract status
- main.account_monitoring_dev.account_metadata - Customer information

**Schema Fields Used:**
- actual_cost - Cost at list price
- list_cost - Total cost at list price (aggregated)
- discounted_cost - Total cost at discounted price (aggregated)
- usage_quantity - DBU/units consumed

**Last Updated:** 2026-01-29 - Fixed Query 4 field names
```

## Verification Completed

### Schema Field Verification

✅ **lakeview_dashboard_queries.sql (15 queries)**
- All field names verified against dashboard_data schema
- Uses: `actual_cost`, `usage_quantity`, `product_category`, `cloud_provider`
- No schema errors found

✅ **ibm_style_dashboard_queries.sql (9 queries)**
- Fixed Query 4: `list_price` → `list_cost`, `discounted_price` → `discounted_cost`
- All other queries verified correct
- Uses: `actual_cost`, `usage_quantity`, `cloud_provider`
- No remaining schema errors

### Table Reference Verification

All table references confirmed:
- ✅ `system.billing.usage` (7 references)
- ✅ `main.account_monitoring_dev.dashboard_data` (9 references)
- ✅ `main.account_monitoring_dev.contract_burndown` (5 references)
- ✅ `main.account_monitoring_dev.contract_burndown_summary` (5 references)
- ✅ `main.account_monitoring_dev.account_metadata` (4 references)

## Benefits

1. **Version Tracking:** Clear version numbers for change management
2. **Documentation:** Inline documentation of data sources and schema
3. **Troubleshooting:** Field definitions help debug query issues
4. **Consistency:** Matches account_monitor_notebook.py standard
5. **Maintenance:** Change log tracks modifications

## Notebook Versions Aligned

| Notebook | Version | Build | Status |
|----------|---------|-------|--------|
| account_monitor_notebook.py | 1.5.4 | 2026-01-29-014 | ✅ Reference |
| lakeview_dashboard_queries.sql | 1.5.5 | 2026-01-29-002 | ✅ Updated |
| ibm_style_dashboard_queries.sql | 1.5.5 | 2026-01-29-002 | ✅ Updated |

## Schema Reference

### dashboard_data Table Fields

From `account_monitor_notebook.py` (lines 640-677):

**Identity:**
- `usage_date` - DATE
- `account_id` - STRING
- `workspace_id` - STRING
- `cloud_provider` - STRING (alias: `cloud` from system.billing.usage)

**Usage:**
- `sku_name` - STRING
- `usage_unit` - STRING
- `usage_quantity` - DECIMAL(18,6)

**Costs:**
- `actual_cost` - DECIMAL(18,2) - usage_quantity * list_price_per_unit
- `list_cost` - DECIMAL(18,2) - Same as actual_cost
- `discounted_cost` - DECIMAL(18,2) - Same as actual_cost (no discount applied)
- `list_price_per_unit` - DECIMAL(18,6)
- `discounted_price_per_unit` - DECIMAL(18,6)

**Metadata:**
- `customer_name` - STRING (from account_metadata)
- `product_category` - STRING (derived via CASE statement)
- Plus all business unit, salesforce, and team fields from account_metadata

## Testing

To verify notebooks work correctly:

```sql
-- Test dashboard_data schema
DESCRIBE main.account_monitoring_dev.dashboard_data;

-- Test Query 4 from ibm_style_dashboard_queries.sql
SELECT
  customer_name,
  cloud_provider as cloud,
  ROUND(SUM(list_cost), 2) as list_price,
  ROUND(SUM(discounted_cost), 2) as discounted_price,
  ROUND(SUM(actual_cost), 2) as revenue
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider;
```

## Conclusion

✅ **All notebooks now have:**
- Proper version tracking
- Complete metadata documentation
- Verified schema field names
- Consistent formatting with reference notebook
- Change logs for maintenance

Ready for production use!
