# 🚀 START HERE - Databricks Account Monitor

## ⚠️ IMPORTANT: Schema Corrections Applied

This project has been **UPDATED** with the correct Databricks system table schemas verified from official documentation.

## 📁 Which Files to Use?

### ✅ USE THESE FILES (Corrected & Verified)

| File | Purpose | Status |
|------|---------|--------|
| **START_HERE.md** | You are here! Start guide | ✅ Use This |
| **SCHEMA_REFERENCE.md** | Official system table schemas | ✅ Use This |
| **account_monitor_queries_CORRECTED.sql** | All SQL queries with correct schema | ✅ Use This |
| **setup_account_monitor_UC.py** | Unity Catalog setup script | ✅ Use This |
| **CORRECTIONS_SUMMARY.md** | What was fixed and why | ✅ Read This |
| **GETTING_STARTED.md** | 15-minute quick start | ✅ Use This |
| **OPERATIONS_GUIDE.md** | Daily operations | ✅ Use This |
| **QUICK_REFERENCE.md** | Query examples | ⚠️ Needs Update* |
| **README.md** | Main documentation | ⚠️ Needs Update* |

*These files contain some queries with the old schema. Refer to `CORRECTIONS_SUMMARY.md` to understand what to fix.

### ❌ DO NOT USE (Old Schema)

| File | Issue | Use Instead |
|------|-------|-------------|
| account_monitor_queries.sql | Uses non-existent columns | account_monitor_queries_CORRECTED.sql |
| setup_account_monitor.py | No Unity Catalog | setup_account_monitor_UC.py |

## 🎯 Quick Start (5 Minutes)

### Step 1: Verify System Tables Access

```sql
-- Run this in Databricks SQL Editor
SELECT
  COUNT(*) as record_count,
  MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);
```

✅ If this works, continue!
❌ If this fails, contact your admin to enable system tables.

### Step 2: Run Setup Script

```bash
# Install Databricks SDK
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

### Step 3: Test Cost Calculation

```sql
-- Verify pricing join works correctly
SELECT
  u.cloud,
  u.sku_name,
  COUNT(*) as records,
  SUM(u.usage_quantity) as total_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
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

✅ If you see costs calculated, you're good to go!

## 📚 Learning Path

### For First-Time Users

1. **Read**: [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md)
   - Understand the actual system table structure
   - See how cost calculation works

2. **Read**: [CORRECTIONS_SUMMARY.md](CORRECTIONS_SUMMARY.md)
   - Understand what was fixed
   - Learn key patterns

3. **Run**: [setup_account_monitor_UC.py](setup_account_monitor_UC.py)
   - Create Unity Catalog tables
   - Insert sample data

4. **Query**: [account_monitor_queries_CORRECTED.sql](account_monitor_queries_CORRECTED.sql)
   - Run the verified queries
   - Build your understanding

5. **Reference**: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)
   - Learn daily operations
   - Set up monitoring

### For Experienced Users

1. Review [CORRECTIONS_SUMMARY.md](CORRECTIONS_SUMMARY.md) for what changed
2. Run [setup_account_monitor_UC.py](setup_account_monitor_UC.py)
3. Use [account_monitor_queries_CORRECTED.sql](account_monitor_queries_CORRECTED.sql)
4. Refer to [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md) as needed

## 🔑 Key Concepts You Need to Know

### 1. Cost Calculation is NOT in system.billing.usage

❌ **WRONG**: `SELECT SUM(usage_metadata.total_price) FROM system.billing.usage`

✅ **CORRECT**:
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

### 2. Always Filter by record_type

```sql
WHERE record_type = 'ORIGINAL'  -- Excludes corrections
```

### 3. Use Unity Catalog

```sql
main.account_monitoring.contracts         -- ✅ Correct
account_monitoring.contracts              -- ❌ Wrong
hive_metastore.account_monitoring.contracts  -- ❌ Old way
```

### 4. Pricing Fields are STRINGS

Always cast:
```sql
CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))
```

## 🎨 What You Get

### Dashboards Components

1. **Account Overview**
   - SKU and workspace counts
   - Data freshness indicators
   - Customer metadata
   - Spend by cloud provider

2. **Contract Management**
   - Contract details and status
   - Consumption tracking
   - Burndown visualization
   - Pace monitoring

3. **Usage Analytics**
   - Monthly cost trends
   - Top workspaces and SKUs
   - Product category breakdown
   - Custom tag analysis

### Key Metrics Tracked

- **Financial**: Spend, DBU consumption, cost per workspace
- **Operational**: Active workspaces, data freshness, SKU usage
- **Governance**: Contract compliance, budget tracking, anomalies

## 🔧 Common Issues & Solutions

### Issue: "Column not found: usage_metadata.total_price"

**Cause**: This column doesn't exist.

**Solution**: Use the corrected queries that join with list_prices.

### Issue: "Table not found: account_monitoring.contracts"

**Cause**: Missing Unity Catalog prefix.

**Solution**: Use `main.account_monitoring.contracts`

### Issue: "Cannot access system.billing.usage"

**Cause**: System tables not enabled or permissions issue.

**Solution**: Contact your Databricks admin.

### Issue: Costs are NULL

**Cause**: Incorrect pricing join or missing type cast.

**Solution**: Use the complete JOIN pattern from SCHEMA_REFERENCE.md

## 📖 Documentation Map

```
START_HERE.md (You are here)
├── SCHEMA_REFERENCE.md          # Official schema docs
├── CORRECTIONS_SUMMARY.md       # What was fixed
├── GETTING_STARTED.md           # Quick start guide
├── account_monitor_queries_CORRECTED.sql  # All queries
├── setup_account_monitor_UC.py  # Setup script
├── OPERATIONS_GUIDE.md          # Daily operations
├── QUICK_REFERENCE.md           # Query examples (needs updates)
├── README.md                    # Full documentation (needs updates)
└── PROJECT_SUMMARY.md           # Project overview
```

## ✅ Pre-Flight Checklist

Before building your dashboard:

- [ ] System tables are accessible
- [ ] Unity Catalog is enabled in your workspace
- [ ] SQL warehouse is available
- [ ] You have CREATE SCHEMA permissions
- [ ] You've read SCHEMA_REFERENCE.md
- [ ] You understand cost calculation requires JOIN
- [ ] You know to filter by `record_type = 'ORIGINAL'`

## 🆘 Need Help?

1. **Schema Questions**: See [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md)
2. **Query Issues**: See [CORRECTIONS_SUMMARY.md](CORRECTIONS_SUMMARY.md)
3. **Setup Problems**: Check [setup_account_monitor_UC.py](setup_account_monitor_UC.py) output
4. **General Questions**: Read [GETTING_STARTED.md](GETTING_STARTED.md)

## 🎯 Success Criteria

After setup, you should be able to:

✅ Query system.billing.usage successfully
✅ Calculate costs using list_prices JOIN
✅ See your Unity Catalog tables (main.account_monitoring.*)
✅ Run all queries from account_monitor_queries_CORRECTED.sql
✅ Get yesterday's spend by cloud provider

## 📊 Next Steps

1. **Customize**: Update account_metadata with your org structure
2. **Populate**: Add your contract information
3. **Dashboard**: Create Lakeview dashboard
4. **Automate**: Schedule daily refresh
5. **Monitor**: Set up alerts for anomalies

## 🔗 External References

Official Databricks documentation:

- [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Pricing system table](https://docs.databricks.com/aws/en/admin/system-tables/pricing)
- [Monitor costs using system tables](https://docs.databricks.com/aws/en/admin/usage/system-tables)

## 📝 Version Info

- **Version**: 2.0 (Schema Corrected)
- **Last Updated**: 2026-01-27
- **Schema Verified**: Official Databricks Docs
- **Databricks Runtime**: 13.0+

---

**Ready to begin?** → Run `python setup_account_monitor_UC.py`

**Need to understand first?** → Read [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md)

**Want quick examples?** → See [account_monitor_queries_CORRECTED.sql](account_monitor_queries_CORRECTED.sql)
