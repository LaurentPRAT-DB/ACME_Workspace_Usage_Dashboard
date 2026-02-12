# Account Monitor - Troubleshooting Guide

**For: System Administrators, DevOps**

---

## Quick Diagnosis

| Symptom | Most Likely Cause | Quick Fix |
|---------|-------------------|-----------|
| Empty dashboard | No data loaded | Run daily refresh job |
| Old forecast dates | Training not run | Run weekly training job |
| Job failures | Warehouse stopped | Start SQL warehouse |
| Permission errors | Missing grants | Grant system.billing access |
| Dashboard errors | Not published | Deploy with `--force` |

---

## Common Issues

### 1. Dashboard Shows "No Data"

**Symptoms:**
- Dashboard widgets show empty or "No data"
- Tables show 0 rows

**Diagnosis:**
```sql
-- Check if tables have data
SELECT 'contracts' as tbl, COUNT(*) FROM main.account_monitoring_dev.contracts
UNION ALL
SELECT 'dashboard_data', COUNT(*) FROM main.account_monitoring_dev.dashboard_data
UNION ALL
SELECT 'contract_burndown', COUNT(*) FROM main.account_monitoring_dev.contract_burndown;
```

**Solutions:**

If `contracts` is empty:
```bash
# Re-run first install to load contracts
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

If `dashboard_data` is empty:
```bash
# Run daily refresh
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE
```

If system tables have no data:
- Contact Databricks support
- Verify system.billing tables are populated

---

### 2. Forecast Shows "linear_fallback"

**Symptoms:**
- `contract_forecast.forecast_model` = "linear_fallback"
- Forecast line is straight, not curved

**Cause:** Prophet requires at least 30 days of data to train properly.

**Check:**
```sql
SELECT contract_id, COUNT(DISTINCT usage_date) as days_of_data
FROM main.account_monitoring_dev.contract_burndown
GROUP BY contract_id;
```

**Solutions:**

If < 30 days:
- Wait until you have 30+ days of consumption data
- Linear fallback is expected for new contracts

If >= 30 days but still linear:
```bash
# Force re-training
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE
```

---

### 3. Job Fails with Permission Error

**Symptoms:**
```
Error: Permission denied: system.billing.usage
```

**Solution:**

Contact your Databricks account admin to grant:
```sql
-- Requires account admin privileges
GRANT SELECT ON TABLE system.billing.usage TO `your_service_principal`;
GRANT SELECT ON TABLE system.billing.list_prices TO `your_service_principal`;
```

---

### 4. Job Fails with Warehouse Error

**Symptoms:**
```
Error: SQL warehouse not found
Error: SQL warehouse is not running
```

**Solutions:**

1. **Warehouse stopped** - Start it in Databricks UI:
   - Go to SQL Warehouses
   - Click Start on your warehouse

2. **Wrong warehouse ID** - Update `databricks.yml`:
   ```yaml
   variables:
     warehouse_id:
       default: "correct-warehouse-id"
   ```

   Find correct ID:
   ```bash
   databricks warehouses list --profile YOUR_PROFILE
   ```

3. **Warehouse deleted** - Create a new one and update config

---

### 5. Dashboard Not Updating After Deploy

**Symptoms:**
- You deployed changes but dashboard looks the same
- New pages/widgets not appearing

**Cause:** Dashboard may have been edited in UI, causing conflicts.

**Solution:**
```bash
# Force overwrite remote changes
databricks bundle deploy --force --profile YOUR_PROFILE
```

If still not working, update via API:
```bash
# Get dashboard ID
databricks api get /api/2.0/lakeview/dashboards --profile YOUR_PROFILE | grep -i consumption

# Force publish
databricks api post /api/2.0/lakeview/dashboards/DASHBOARD_ID/published \
  --json '{}' --profile YOUR_PROFILE
```

---

### 6. Contract Pace Status Wrong

**Symptoms:**
- Dashboard shows wrong pace (OVER PACE when should be ON PACE)
- Percentages don't match expected

**Diagnosis:**
```sql
SELECT
  contract_id,
  start_date,
  end_date,
  total_value as commitment,
  DATEDIFF(CURRENT_DATE(), start_date) as days_elapsed,
  DATEDIFF(end_date, start_date) as total_days
FROM main.account_monitoring_dev.contracts;
```

**Solutions:**

1. **Wrong contract dates** - Edit `config/contracts.yml`:
   ```yaml
   contracts:
     - contract_id: "CONTRACT-001"
       start_date: "2026-01-01"  # Correct date
       end_date: "2026-12-31"    # Correct date
   ```
   Then redeploy and re-run setup.

2. **Wrong total_value** - Update in config or direct SQL:
   ```sql
   UPDATE main.account_monitoring_dev.contracts
   SET total_value = 500000.00
   WHERE contract_id = 'CONTRACT-001';
   ```

---

### 7. What-If Scenarios Missing

**Symptoms:**
- What-If Analysis page shows no scenarios
- `scenario_summary` table is empty

**Diagnosis:**
```sql
SELECT COUNT(*) FROM main.account_monitoring_dev.discount_tiers;
SELECT COUNT(*) FROM main.account_monitoring_dev.scenario_summary;
```

**Solutions:**

If `discount_tiers` is empty:
```bash
# Re-run first install to populate tiers
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

If tiers exist but scenarios don't:
```bash
# Run weekly training which generates scenarios
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE
```

---

### 8. SQL Syntax Errors

**Symptoms:**
```
[PARSE_SYNTAX_ERROR] Syntax error at or near...
[TABLE_OR_VIEW_NOT_FOUND] The table or view cannot be found
```

**Common Causes & Solutions:**

| Error | Cause | Fix |
|-------|-------|-----|
| `TABLE_OR_VIEW_NOT_FOUND` | CTE out of scope | Convert to temp view |
| Syntax error near `IDENTIFIER` | Unsupported usage | Use CTAS workaround |
| Column not found | Schema mismatch | Check column names |

**CTE Scope Issue:**
```sql
-- Wrong: CTE goes out of scope
WITH my_data AS (SELECT * FROM t1)
SELECT * FROM my_data;
SELECT * FROM my_data;  -- ERROR!

-- Right: Use temp view
CREATE OR REPLACE TEMP VIEW my_data AS SELECT * FROM t1;
SELECT * FROM my_data;
SELECT * FROM my_data;  -- Works
```

---

### 9. Decimal Type Errors in Python

**Symptoms:**
```
TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'
```

**Cause:** Spark returns Decimal types, but pandas expects float.

**Solution:**
```python
# Convert before arithmetic
df['column'] = df['column'].astype(float)
```

---

### 10. Prophet Installation Fails on Serverless

**Symptoms:**
```
ModuleNotFoundError: No module named 'prophet'
```

**Solution:**

Use subprocess, not %pip:
```python
# This works on serverless
import subprocess
subprocess.run(['pip', 'install', 'prophet'], check=True)

# This may fail
# %pip install prophet  # Don't use
```

---

## Diagnostic Queries

### Check All Table Freshness

```sql
SELECT
  'dashboard_data' as table_name,
  MAX(usage_date) as latest_date,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_stale
FROM main.account_monitoring_dev.dashboard_data

UNION ALL
SELECT 'contract_burndown', MAX(usage_date), DATEDIFF(CURRENT_DATE(), MAX(usage_date))
FROM main.account_monitoring_dev.contract_burndown

UNION ALL
SELECT 'contract_forecast', MAX(forecast_date), DATEDIFF(CURRENT_DATE(), MAX(forecast_date))
FROM main.account_monitoring_dev.contract_forecast;
```

### Check Forecast Model Type

```sql
SELECT
  contract_id,
  forecast_model,
  MIN(forecast_date) as first_forecast,
  MAX(forecast_date) as last_forecast,
  training_date
FROM main.account_monitoring_dev.contract_forecast
GROUP BY contract_id, forecast_model, training_date;
```

### Check Contract Status

```sql
SELECT
  contract_id,
  status,
  total_value,
  start_date,
  end_date,
  DATEDIFF(end_date, CURRENT_DATE()) as days_remaining
FROM main.account_monitoring_dev.contracts;
```

### Check Job Run History

```bash
# Last 10 job runs
databricks runs list --limit 10 --profile YOUR_PROFILE

# Details of specific run
databricks runs get --run-id RUN_ID --profile YOUR_PROFILE
```

---

## Getting Help

### Internal Resources

1. Check this troubleshooting guide
2. Review [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
3. Check job run logs in Databricks UI

### External Resources

1. Databricks documentation: https://docs.databricks.com
2. Databricks community: https://community.databricks.com
3. Contact Databricks support

### Information to Gather

When escalating, include:
- Error message (exact text)
- Job run ID
- SQL query that failed
- Steps to reproduce
- What you've already tried

---

*Last updated: February 2026*
