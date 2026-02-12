# Post-Deployment Validation

## Overview

The `post_deployment_validation.py` notebook validates that your Account Monitor deployment is working correctly. It performs 12 comprehensive tests covering all critical components.

## What It Tests

### ✅ System Access & Data
1. **System Tables Access** - Verifies you can query `system.billing.usage`
2. **Data Freshness** - Checks system tables have recent data
3. **Cost Calculation** - Tests correct JOIN pattern with list_prices

### ✅ Unity Catalog Objects
4. **Schema Exists** - Confirms `main.account_monitoring_dev` schema
5. **Required Tables** - Validates all 4 tables exist
6. **Account Metadata** - Checks sample data populated
7. **Contracts** - Verifies contract tracking table

### ✅ Dashboard Data
8. **Dashboard Data** - Validates main data table is populated
9. **Daily Summary** - Checks summary table exists
10. **Contract Consumption** - Tests consumption calculation queries

### ✅ Deployment Status
11. **Jobs Deployed** - Verifies workflow jobs exist
12. **Sample Queries** - Tests end-to-end query execution

## How to Run

### Method 1: Upload to Workspace (Recommended)

1. **Upload the notebook**
   ```bash
   databricks workspace import \
     post_deployment_validation.py \
     /Users/your.email@company.com/post_deployment_validation \
     --language PYTHON \
     --format SOURCE \
     --profile LPT_FREE_EDITION
   ```

2. **Open in workspace**
   - Go to **Workspace** → **Users** → your email
   - Click on `post_deployment_validation`

3. **Run all cells**
   - Click **Run All** at the top
   - Wait for all tests to complete

### Method 2: Using Databricks CLI

```bash
# Run the notebook remotely
databricks workspace run \
  /Users/your.email@company.com/post_deployment_validation \
  --profile LPT_FREE_EDITION
```

### Method 3: Manual Verification

If you prefer SQL, run these queries in SQL Editor:

```sql
-- Test 1: System tables access
SELECT COUNT(*) FROM system.billing.usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7);

-- Test 2: Schema exists
SHOW SCHEMAS IN main LIKE 'account_monitoring%';

-- Test 3: Tables exist
SHOW TABLES IN main.account_monitoring_dev;

-- Test 4: Data populated
SELECT COUNT(*) FROM main.account_monitoring_dev.dashboard_data;

-- Test 5: Cost calculation works
SELECT
  u.cloud,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date = CURRENT_DATE() - 1
  AND u.record_type = 'ORIGINAL'
GROUP BY u.cloud;
```

## Configuration

Edit the notebook's configuration cell if needed:

```python
# Configuration - Update these if you used different values
CATALOG = "main"
SCHEMA = "account_monitoring_dev"  # or "account_monitoring" for prod
TARGET = "dev"  # or "prod"
```

## Understanding Results

### ✅ All Tests Passed

```
📊 VALIDATION SUMMARY
======================================================================
Total Tests: 12
Passed: 12
Failed: 0
======================================================================

🎉 All tests passed! Your deployment is ready to use.
```

**Next Steps:**
1. Update account metadata with your actual data
2. Add your contracts
3. Run the daily refresh job
4. Create a Lakeview dashboard

### ⚠️ Some Tests Failed

```
📊 VALIDATION SUMMARY
======================================================================
Total Tests: 12
Passed: 8
Failed: 4
======================================================================

❌ Failed Tests:
  - Dashboard Data: Dashboard data is empty - run daily refresh job
  - Daily Summary: Daily summary is empty - run daily refresh job
  - Contract Consumption: No active contracts or no consumption data
  - Sample Query: No data for yesterday - may be normal
```

**Common Fixes:**

| Failed Test | Solution |
|-------------|----------|
| System Tables Access | Contact admin to enable system tables |
| Unity Catalog Schema | Run setup job: `databricks bundle run account_monitor_setup` |
| Required Tables | Run setup job first |
| Dashboard Data empty | Run: `databricks bundle run account_monitor_daily_refresh` |
| Contracts missing | Add your contract data in SQL |
| Account Metadata | Check setup job ran successfully |

## Troubleshooting

### "Cannot access system.billing.usage"

**Cause**: System tables not enabled or permissions issue

**Fix**:
```bash
# Test access directly
databricks sql-query create \
  --warehouse-id 58d41113cb262dce \
  --query "SELECT COUNT(*) FROM system.billing.usage" \
  --profile LPT_FREE_EDITION
```

If this fails, contact your Databricks admin.

### "Schema not found"

**Cause**: Setup job hasn't run yet

**Fix**:
```bash
# Run setup job
databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev

# Check it completed
databricks jobs runs list --profile LPT_FREE_EDITION --limit 5
```

### "Dashboard data is empty"

**Cause**: Daily refresh job hasn't run yet

**Fix**:
```bash
# Run daily refresh manually
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev

# Wait a few minutes, then re-run validation
```

### "Tables exist but no data"

**Cause**: Setup job ran but didn't insert sample data

**Fix**: Run this SQL in SQL Editor:
```sql
-- Insert sample data manually
INSERT INTO main.account_monitoring_dev.account_metadata VALUES
  ((SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1),
   'Your Organization',
   'SF-123456',
   'REGION',
   'SUB-REGION',
   'COUNTRY',
   'DIVISION',
   'AE Name',
   'SA Name',
   'DSA Name',
   'US',
   'Technology',
   CURRENT_TIMESTAMP(),
   CURRENT_TIMESTAMP());
```

## Expected Timeline

| After Action | Expected Results |
|--------------|-----------------|
| Bundle deploy | ✅ Schema and tables created |
| Run setup job | ✅ Sample data inserted |
| Run daily refresh | ✅ Dashboard data populated (5-10 min) |
| Next day | ✅ Yesterday's cost data available |

## Validation Checklist

Use this checklist when validating:

- [ ] Notebook uploaded to workspace
- [ ] All cells executed successfully
- [ ] All 12 tests passed
- [ ] Account metadata updated with real data
- [ ] Contracts added
- [ ] Dashboard data is populated
- [ ] Sample queries return results
- [ ] Jobs visible in Workflows UI

## Next Steps After Validation

### 1. Update Real Data

```sql
-- Get your account ID
SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1;

-- Update account metadata
UPDATE main.account_monitoring_dev.account_metadata
SET
  customer_name = 'Your Actual Organization',
  salesforce_id = 'YOUR-REAL-SF-ID',
  business_unit_l0 = 'YOUR-REGION',
  account_executive = 'Real AE Name',
  solutions_architect = 'Real SA Name'
WHERE account_id = 'your-account-id-from-above';

-- Add real contracts
INSERT INTO main.account_monitoring_dev.contracts VALUES
  ('YOUR-CONTRACT-ID',
   'your-account-id',
   'aws',
   DATE'2024-01-01',
   DATE'2025-12-31',
   500000.00,
   'USD',
   'SPEND',
   'ACTIVE',
   'Production AWS contract',
   CURRENT_TIMESTAMP(),
   CURRENT_TIMESTAMP());
```

### 2. Run Initial Refresh

```bash
# Run daily refresh to populate dashboard
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

### 3. Create Dashboard

1. Go to **Dashboards** → **Create Dashboard**
2. Use queries from `account_monitor_queries_CORRECTED.sql`
3. Add visualizations:
   - Counter: Today's spend
   - Line chart: Monthly trends
   - Table: Top workspaces
   - Line chart: Contract burndown

### 4. Schedule Jobs

Jobs are already scheduled, but verify:
```bash
# List jobs
databricks jobs list --profile LPT_FREE_EDITION --output json | \
  jq '.jobs[] | select(.settings.name | contains("Account Monitor"))'
```

## Rerunning Validation

After making fixes, rerun the validation:

```bash
# Method 1: In UI
# Just click "Run All" again in the notebook

# Method 2: Via CLI
databricks workspace run \
  /Users/your.email@company.com/post_deployment_validation \
  --profile LPT_FREE_EDITION
```

## Success Criteria

Your deployment is successful when:

✅ All 12 tests pass
✅ Dashboard data shows cost information
✅ Contracts track consumption correctly
✅ Jobs run on schedule
✅ Sample queries return accurate costs

## Support

- **Validation Issues**: See troubleshooting section above
- **Schema Questions**: Check `SCHEMA_REFERENCE.md`
- **Query Help**: See `QUICK_REFERENCE.md`
- **Operations**: See `OPERATIONS_GUIDE.md`

---

**Quick Command:**
```bash
# Upload and run validation in one command
databricks workspace import post_deployment_validation.py /Users/$(databricks current-user me --profile LPT_FREE_EDITION | jq -r .userName)/post_deployment_validation --language PYTHON --format SOURCE --profile LPT_FREE_EDITION && echo "✅ Uploaded! Now open it in your workspace and click 'Run All'"
```
