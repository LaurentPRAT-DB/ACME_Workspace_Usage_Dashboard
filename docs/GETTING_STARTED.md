# Getting Started - 15 Minute Quick Start

This guide will get you from zero to a working account monitor in 15 minutes.

## Prerequisites Check (2 minutes)

Open a SQL query in your Databricks workspace and run:

```sql
-- Test 1: Can you access system tables?
SELECT COUNT(*) FROM system.billing.usage;

-- Test 2: Do you have data?
SELECT MAX(usage_date) as latest_date
FROM system.billing.usage;
```

✅ If both queries work, continue!
❌ If either fails, you need to:
- Enable system tables (contact Databricks support)
- Wait for data to populate (24-48 hour lag)

## Step 1: Run Setup Script (5 minutes)

### Option A: Automated Setup (Recommended)

```bash
# Install Databricks SDK if not already installed
pip install databricks-sdk

# Run setup script
python setup_account_monitor.py
```

The script will:
1. Create `account_monitoring` database
2. Create 3 tables (contracts, account_metadata, dashboard_data)
3. Insert sample data
4. Set up a daily refresh job

### Option B: Manual Setup

If the script doesn't work, run these SQL commands:

```sql
-- 1. Create database
CREATE DATABASE IF NOT EXISTS account_monitoring;

-- 2. Create contracts table
CREATE TABLE account_monitoring.contracts (
  contract_id STRING,
  account_id STRING,
  cloud_provider STRING,
  start_date DATE,
  end_date DATE,
  total_value DECIMAL(18,2),
  currency STRING DEFAULT 'USD',
  commitment_type STRING,
  status STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- 3. Create account metadata table
CREATE TABLE account_monitoring.account_metadata (
  account_id STRING,
  customer_name STRING,
  salesforce_id STRING,
  business_unit_l0 STRING,
  business_unit_l1 STRING,
  business_unit_l2 STRING,
  business_unit_l3 STRING,
  account_executive STRING,
  solutions_architect STRING,
  delivery_solutions_architect STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA;

-- 4. Insert your account metadata (CUSTOMIZE THIS!)
INSERT INTO account_monitoring.account_metadata VALUES (
  'your-account-id',
  'Your Company Name',
  'your-salesforce-id',
  'Region',
  'Sub-Region',
  'Country',
  'Division',
  'Your AE Name',
  'Your SA Name',
  'Your DSA Name',
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);

-- 5. Insert your contracts (CUSTOMIZE THIS!)
INSERT INTO account_monitoring.contracts VALUES (
  'contract-001',
  'your-account-id',
  'aws',  -- or 'azure' or 'gcp'
  '2024-01-01',
  '2025-12-31',
  500000.00,
  'USD',
  'SPEND',
  'ACTIVE',
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
```

## Step 2: Test Basic Queries (3 minutes)

Run these queries to verify everything works:

```sql
-- Query 1: Current month spend
SELECT
  cloud_provider,
  ROUND(SUM(usage_metadata.total_price), 2) as mtd_spend
FROM system.billing.usage
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
GROUP BY cloud_provider;

-- Query 2: Contract status
SELECT
  contract_id,
  total_value as commitment,
  DATEDIFF(end_date, CURRENT_DATE()) as days_remaining
FROM account_monitoring.contracts
WHERE status = 'ACTIVE';

-- Query 3: Top 5 workspaces this month
SELECT
  workspace_id,
  ROUND(SUM(usage_metadata.total_price), 2) as spend
FROM system.billing.usage
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
GROUP BY workspace_id
ORDER BY spend DESC
LIMIT 5;
```

## Step 3: Create Your First Dashboard (5 minutes)

### Option A: Using Lakeview (Recommended)

1. Go to **Dashboards** in your Databricks workspace
2. Click **Create Dashboard**
3. Choose **Lakeview Dashboard**
4. Add visualizations using these queries:

**Visualization 1: Monthly Spend (Line Chart)**
```sql
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  SUM(usage_metadata.total_price) as cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY month, cloud_provider
ORDER BY month;
```

**Visualization 2: Top Workspaces (Table)**
```sql
SELECT
  workspace_id,
  COUNT(DISTINCT usage_date) as active_days,
  ROUND(SUM(usage_metadata.total_price), 2) as total_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id
ORDER BY total_cost DESC
LIMIT 10;
```

**Visualization 3: Contract Burndown (Line Chart)**
```sql
SELECT
  c.contract_id,
  u.usage_date,
  SUM(SUM(u.usage_metadata.total_price)) OVER (
    PARTITION BY c.contract_id
    ORDER BY u.usage_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_spend
FROM account_monitoring.contracts c
LEFT JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND u.usage_date BETWEEN c.start_date AND c.end_date
WHERE c.status = 'ACTIVE'
GROUP BY c.contract_id, u.usage_date
ORDER BY u.usage_date;
```

### Option B: Using Legacy Dashboards

1. Go to **SQL** → **Dashboards**
2. Click **Create Dashboard**
3. Add queries from above as visualizations

## You're Done! 🎉

You now have:
- ✅ Custom tables for tracking contracts and metadata
- ✅ Working queries to analyze spending
- ✅ A basic dashboard showing key metrics

## Next Steps

### Immediate (Today)
1. Replace sample data with your actual contracts
2. Update account metadata with real information
3. Add more visualizations to your dashboard

### This Week
1. Review the **QUICK_REFERENCE.md** for more queries
2. Set up daily data checks (see **OPERATIONS_GUIDE.md**)
3. Create alerts for high spending

### This Month
1. Review the full **README.md** for advanced features
2. Optimize your queries for performance
3. Set up automated reports

## Common Issues

### "Permission denied on system.billing.usage"
- **Fix**: Contact your Databricks account admin to enable system tables

### "Table or view not found: account_monitoring.contracts"
- **Fix**: Re-run Step 1 to create the tables

### "No data returned from queries"
- **Fix**: System tables have 24-48 hour lag. Check `SELECT MAX(usage_date) FROM system.billing.usage`

### "Contract consumption shows 0"
- **Fix**: Verify your contract account_id matches the account_id in system.billing.usage

## Quick Reference Card

Save this for daily use:

```sql
-- TODAY'S SPEND
SELECT ROUND(SUM(usage_metadata.total_price), 2) as today
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE() - 1;

-- THIS MONTH
SELECT ROUND(SUM(usage_metadata.total_price), 2) as mtd
FROM system.billing.usage
WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE());

-- DATA FRESHNESS
SELECT MAX(usage_date) as latest,
       DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_old
FROM system.billing.usage;

-- TOP WORKSPACE TODAY
SELECT workspace_id, ROUND(SUM(usage_metadata.total_price), 2) as cost
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE() - 1
GROUP BY workspace_id
ORDER BY cost DESC
LIMIT 1;

-- CONTRACT STATUS
SELECT contract_id,
       ROUND(100.0 * consumed / total_value, 1) as pct
FROM (
  SELECT c.contract_id, c.total_value,
         SUM(u.usage_metadata.total_price) as consumed
  FROM account_monitoring.contracts c
  LEFT JOIN system.billing.usage u
    ON c.account_id = u.account_id
    AND u.usage_date BETWEEN c.start_date AND c.end_date
  GROUP BY c.contract_id, c.total_value
);
```

## Help

- 📖 Full documentation: **README.md**
- 🔍 Query examples: **QUICK_REFERENCE.md**
- 🛠️ Daily operations: **OPERATIONS_GUIDE.md**
- 📊 Project overview: **PROJECT_SUMMARY.md**

## Feedback

Found an issue or have a suggestion? Update the documentation or contact your Databricks field engineer.

---

**Remember**: System tables have a 24-48 hour lag. Yesterday's data will be available today!
