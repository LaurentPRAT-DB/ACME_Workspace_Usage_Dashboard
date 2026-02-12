# START HERE - Databricks Account Monitor

Welcome to the Account Monitor! This guide will get you from zero to a working dashboard in 15 minutes.

## Prerequisites Check (2 minutes)

Open a SQL query in your Databricks workspace and run:

```sql
-- Test 1: Can you access system tables?
SELECT COUNT(*) as record_count, MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);

-- Test 2: Can you access pricing?
SELECT COUNT(*) FROM system.billing.list_prices;
```

- **Both work?** Continue to Step 1
- **Permission denied?** Contact your Databricks admin to enable system tables
- **No data?** System tables have 24-48 hour lag - check back tomorrow

## Step 1: Run Setup Script (5 minutes)

```bash
# Install Databricks SDK if needed
pip install databricks-sdk

# Run Unity Catalog setup (uses 'main' catalog by default)
python setup_account_monitor_UC.py

# Or specify your catalog:
python setup_account_monitor_UC.py your_catalog_name
```

This creates:
- `main.account_monitoring.contracts`
- `main.account_monitoring.account_metadata`
- `main.account_monitoring.dashboard_data`

## Step 2: Test Cost Calculation (3 minutes)

**Important**: Cost calculation requires joining `usage` with `list_prices`. There is no `usage_metadata.total_price` column.

```sql
-- Verify pricing join works correctly
SELECT
  u.cloud,
  u.sku_name,
  COUNT(*) as records,
  SUM(u.usage_quantity) as total_dbu,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL'
GROUP BY u.cloud, u.sku_name
ORDER BY total_cost DESC
LIMIT 10;
```

If you see costs calculated, you're ready to build dashboards.

## Step 3: Create Your First Dashboard (5 minutes)

1. Go to **Dashboards** in your Databricks workspace
2. Click **Create Dashboard** → **Lakeview Dashboard**
3. Add these visualizations:

**Monthly Spend Trend (Line Chart)**
```sql
SELECT
  DATE_TRUNC('MONTH', u.usage_date) as month,
  u.cloud,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 365)
  AND u.record_type = 'ORIGINAL'
GROUP BY month, u.cloud
ORDER BY month;
```

**Top Workspaces (Table)**
```sql
SELECT
  u.workspace_id,
  COUNT(DISTINCT u.usage_date) as active_days,
  ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.workspace_id
ORDER BY total_cost DESC
LIMIT 10;
```

## You're Done!

You now have:
- Custom tables for tracking contracts and metadata
- Working queries with correct cost calculation
- A basic dashboard showing key metrics

---

## Quick Reference Card

Save these queries for daily use:

```sql
-- YESTERDAY'S SPEND
SELECT ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as yesterday_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1 AND u.record_type = 'ORIGINAL';

-- MONTH-TO-DATE SPEND
SELECT ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as mtd_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name AND u.cloud = lp.cloud AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE()) AND u.record_type = 'ORIGINAL';

-- DATA FRESHNESS
SELECT MAX(usage_date) as latest, DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_old
FROM system.billing.usage;

-- CONTRACT STATUS
SELECT contract_id, total_value as commitment, DATEDIFF(end_date, CURRENT_DATE()) as days_remaining
FROM main.account_monitoring.contracts
WHERE status = 'ACTIVE';
```

---

## Key Concepts

### Cost Calculation Requires a JOIN

There is no `usage_metadata.total_price` column. You must join with `list_prices`:

```sql
SELECT SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10)))
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
```

### Always Filter by record_type

```sql
WHERE record_type = 'ORIGINAL'  -- Excludes corrections
```

### Use Unity Catalog Paths

```sql
main.account_monitoring.contracts         -- Correct
account_monitoring.contracts              -- Wrong (missing catalog)
```

### Pricing Fields are STRINGS

Always cast:
```sql
CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
```

---

## Which Files to Use

| File | Purpose |
|------|---------|
| **START_HERE.md** | You are here - quick start guide |
| **SCHEMA_REFERENCE.md** | Official system table schemas |
| **account_monitor_queries_CORRECTED.sql** | All SQL queries with correct schema |
| **setup_account_monitor_UC.py** | Unity Catalog setup script |
| **CORRECTIONS_SUMMARY.md** | What was fixed and why |
| **OPERATIONS_GUIDE.md** | Daily operations |

### Do Not Use (Old Schema)

| File | Issue | Use Instead |
|------|-------|-------------|
| account_monitor_queries.sql | Uses non-existent columns | account_monitor_queries_CORRECTED.sql |
| setup_account_monitor.py | No Unity Catalog | setup_account_monitor_UC.py |

---

## Common Issues

### "Column not found: usage_metadata.total_price"
This column doesn't exist. Use the list_prices JOIN pattern shown above.

### "Table not found: account_monitoring.contracts"
Missing Unity Catalog prefix. Use `main.account_monitoring.contracts`.

### "Cannot access system.billing.usage"
System tables not enabled. Contact your Databricks admin.

### "Costs are NULL"
Incorrect pricing join or missing type cast. Use the complete JOIN pattern from this guide.

### "No data returned"
System tables have 24-48 hour lag. Check: `SELECT MAX(usage_date) FROM system.billing.usage`

### "Contract consumption shows 0"
Verify your contract `account_id` matches the `account_id` in system.billing.usage.

---

## Next Steps

### Today
1. Replace sample data with your actual contracts
2. Update account metadata with real information
3. Add more visualizations to your dashboard

### This Week
1. Review **OPERATIONS_GUIDE.md** for daily operations
2. Set up daily data freshness checks
3. Create alerts for high spending

### This Month
1. Optimize your queries for performance
2. Set up automated reports
3. Add custom tags for cost allocation

---

## External References

- [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Pricing system table](https://docs.databricks.com/aws/en/admin/system-tables/pricing)
- [Monitor costs using system tables](https://docs.databricks.com/aws/en/admin/usage/system-tables)

---

**Version**: 2.1 (Consolidated)
**Last Updated**: 2026-02-12
**Databricks Runtime**: 13.0+

---

**Ready to begin?** Run `python setup_account_monitor_UC.py`

**Need schema details?** Read [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md)

**Want more queries?** See [account_monitor_queries_CORRECTED.sql](account_monitor_queries_CORRECTED.sql)
