# Create IBM-Style Account Monitor Dashboard

**⚠️ DEPRECATED - 2026-01-29**

**This guide has been superseded by the Lakeview Dashboard.**

The IBM-style queries have been merged into `lakeview_dashboard_queries.sql`. You can still create a single-page layout using Lakeview queries.

**Please use:**
- `/notebooks/lakeview_dashboard_queries.sql` - All 17 queries
- `/docs/CREATE_LAKEVIEW_DASHBOARD.md` - Updated comprehensive guide

**To create a single-page layout:** Use Lakeview Queries 1, 2, 8, 9, 10, 16, and 17

**For full details:** See `/docs/IBM_QUERIES_REDUNDANCY_ANALYSIS.md`

---

# Original Content (Archived)

# Create IBM-Style Account Monitor Dashboard

## Overview

This guide shows you how to recreate the IBM Account Monitor dashboard layout in Databricks Lakeview, featuring:
- Account overview with key metrics
- Data freshness indicators
- Account information table
- Total spend by cloud provider
- Contracts table with consumption tracking
- Contract burndown visualization

## Prerequisites

✅ All data loaded (contracts, account metadata, dashboard data)
✅ Contract burndown tables populated
✅ Queries available in `ibm_style_dashboard_queries` notebook

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Account Monitor                                                             │
│ Filters: Account | Date Range | SKU Count                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Row 1: Key Metrics                                                          │
│ ┌──────────────┬──────────────┬──────────────┬─────────────────────────┐   │
│ │ top_sku_count│ top_workspace│    date      │  Latest Data Dates      │   │
│ │   Counter    │   Counter    │   Counter    │      Table              │   │
│ └──────────────┴──────────────┴──────────────┴─────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Row 2: Account Information                                                  │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │  Account Info Table                                                   │   │
│ │  Customer | Salesforce ID | Business Units | Team                    │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Row 3: Spending Overview                                                    │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │  Total Spend in Timeframe                                             │   │
│ │  Customer | Cloud | Dates | DBU | Prices | Revenue                   │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Row 4: Contracts and Burndown                                               │
│ ┌──────────────────────────────┬──────────────────────────────────────┐     │
│ │  Contracts Table             │  Contract Burndown Chart             │     │
│ │  Platform | Contract ID      │  Line chart showing:                 │     │
│ │  Dates | Value | Consumed    │  - Commit (flat line)                │     │
│ │                              │  - Consumption (curve)               │     │
│ └──────────────────────────────┴──────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Instructions

### Step 1: Create New Dashboard

1. **Navigate to Dashboards**
   - Click **Dashboards** in left sidebar
   - Click **"Create Dashboard"**
   - Select **"Lakeview Dashboard"**

2. **Name Your Dashboard**
   - Name: `Account Monitor - IBM Style`
   - Description: `Comprehensive account monitoring with contract burndown tracking`
   - Click **"Create"**

### Step 2: Add Filters (Top Bar)

#### Filter 1: Account Selection
1. Click **"Add"** → **"Filter"**
2. **Type:** Dropdown
3. **Query:**
   ```sql
   SELECT DISTINCT customer_name
   FROM main.account_monitoring_dev.account_metadata
   ORDER BY customer_name
   ```
4. **Label:** Account
5. **Default:** Select first account
6. **Apply to:** All queries

#### Filter 2: Date Range
1. Click **"Add"** → **"Filter"**
2. **Type:** Date Range
3. **Label:** Date Range
4. **Default:** Last 12 months
5. **Apply to:** Queries using usage_date

#### Filter 3: SKU Count
1. Click **"Add"** → **"Filter"**
2. **Type:** Number Input
3. **Label:** top_sku_count
4. **Default:** 5
5. **Apply to:** SKU-related queries

### Step 3: Row 1 - Key Metrics (Counters)

#### Counter 1: Top SKU Count
1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `top_sku_count`
3. **Query:**
   ```sql
   SELECT COUNT(DISTINCT sku_name) as top_sku_count
   FROM system.billing.usage
   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
   ```
4. **Visualization:** Counter
5. **Field:** `top_sku_count`
6. **Title:** `top_sku_count`
7. **Position:** x=0, y=0, width=2, height=2

#### Counter 2: Top Workspace Count
1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `top_workspace_count`
3. **Query:**
   ```sql
   SELECT COUNT(DISTINCT workspace_id) as top_workspace_count
   FROM system.billing.usage
   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
   ```
4. **Visualization:** Counter
5. **Field:** `top_workspace_count`
6. **Title:** `top_workspace_count`
7. **Position:** x=2, y=0, width=2, height=2

#### Counter 3: Latest Date
1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `latest_date`
3. **Query:**
   ```sql
   SELECT MAX(usage_date) as date
   FROM system.billing.usage
   ```
4. **Visualization:** Counter
5. **Field:** `date`
6. **Title:** `date`
7. **Format:** Date/Time
8. **Position:** x=4, y=0, width=2, height=2

#### Table: Latest Data Dates
1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `data_freshness`
3. **Query:**
   ```sql
   SELECT
     'Consumption' as source,
     MAX(usage_date) as latest_date,
     CASE
       WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
       ELSE 'False'
     END as verified
   FROM system.billing.usage
   UNION ALL
   SELECT
     'Metrics' as source,
     MAX(usage_date) as latest_date,
     CASE
       WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
       ELSE 'False'
     END as verified
   FROM system.billing.usage
   ```
4. **Visualization:** Table
5. **Title:** `Latest Data Dates`
6. **Columns:** Source, Latest Date, Verified
7. **Conditional Formatting:**
   - Verified = "False" → Red background
   - Verified = "True" → Green background
8. **Position:** x=6, y=0, width=6, height=2

### Step 4: Row 2 - Account Information

1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `account_info`
3. **Query:**
   ```sql
   SELECT
     customer_name as "Customer",
     salesforce_id as "Salesforce ID",
     business_unit_l0 as "Business Unit L0",
     business_unit_l1 as "Business Unit L1",
     business_unit_l2 as "Business Unit L2",
     business_unit_l3 as "Business Unit L3",
     account_executive as "Account Executive",
     solutions_architect as "Solutions Architect",
     delivery_solutions_architect as "Delivery Solutions Architect"
   FROM main.account_monitoring_dev.account_metadata
   LIMIT 1
   ```
4. **Visualization:** Table
5. **Title:** `Account Info`
6. **Layout:** Horizontal (fields as columns)
7. **Show Headers:** Yes
8. **Position:** x=0, y=2, width=12, height=2

### Step 5: Row 3 - Total Spend by Cloud

1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `total_spend_timeframe`
3. **Query:**
   ```sql
   SELECT
     customer_name as "Customer Name",
     cloud_provider as "Cloud",
     MIN(usage_date) as "Start Date",
     MAX(usage_date) as "End Date",
     ROUND(SUM(usage_quantity), 0) as "DBU",
     CONCAT('$', FORMAT_NUMBER(ROUND(SUM(list_price), 2), 2)) as "List Price",
     CONCAT('$', FORMAT_NUMBER(ROUND(SUM(discounted_price), 2), 2)) as "Discounted Price",
     CONCAT('$', FORMAT_NUMBER(ROUND(SUM(actual_cost), 2), 2)) as "Revenue"
   FROM main.account_monitoring_dev.dashboard_data
   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
   GROUP BY customer_name, cloud_provider
   ORDER BY cloud_provider
   ```
4. **Visualization:** Table
5. **Title:** `Total Spend in Timeframe`
6. **Columns:** Customer Name, Cloud, Start Date, End Date, DBU, List Price, Discounted Price, Revenue
7. **Number Formatting:**
   - DBU: Thousands separator
   - Dates: MM/DD/YYYY format
8. **Position:** x=0, y=4, width=12, height=3

### Step 6: Row 4 Left - Contracts Table

1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `contracts_table`
3. **Query:**
   ```sql
   SELECT
     cloud_provider as "Platform",
     contract_id as "Contract ID",
     start_date as "Start",
     end_date as "End",
     CONCAT('$', FORMAT_NUMBER(commitment, 0)) as "Total Value",
     CASE
       WHEN total_consumed IS NULL THEN 'null'
       ELSE CONCAT('$', FORMAT_NUMBER(total_consumed, 2))
     END as "Consumed",
     CASE
       WHEN consumed_pct IS NULL THEN 'null'
       ELSE CONCAT(ROUND(consumed_pct, 1), '%')
     END as "Consumed %"
   FROM main.account_monitoring_dev.contract_burndown_summary
   ORDER BY start_date
   ```
4. **Visualization:** Table
5. **Title:** `Contracts`
6. **Columns:** Platform, Contract ID, Start, End, Total Value, Consumed, Consumed %
7. **Conditional Formatting:**
   - Consumed % > 80 → Yellow background
   - Consumed % > 90 → Red background
8. **Position:** x=0, y=7, width=6, height=6

### Step 7: Row 4 Right - Contract Burndown Chart

1. **Add** → **"Visualization"** → **"Create new query"**
2. **Query Name:** `contract_burndown_chart`
3. **Query:**
   ```sql
   SELECT
     usage_date as date,
     ROUND(SUM(commitment), 2) as commit,
     ROUND(SUM(cumulative_cost), 2) as consumption
   FROM main.account_monitoring_dev.contract_burndown
   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
   GROUP BY usage_date
   ORDER BY usage_date
   ```
4. **Visualization:** Line Chart
5. **Title:** `Contract Burndown`
6. **Configuration:**
   - **X-Axis:** `date` (Date format)
   - **Y-Axes:**
     - Series 1: `commit` - Label: "Commit" - Color: Gray (#757575) - Style: Solid
     - Series 2: `consumption` - Label: "Consumption" - Color: Orange (#FF9800) - Style: Solid
   - **Legend:** Bottom
   - **Y-Axis Label:** "DBU ($)"
   - **X-Axis Label:** "Date"
7. **Position:** x=6, y=7, width=6, height=6

### Step 8: Configure Dashboard Settings

1. **Dashboard Settings** (gear icon)
2. **Auto-refresh:** Every 24 hours at 3:00 AM UTC
3. **Permissions:**
   - Can View: All Users
   - Can Edit: Account Admins
4. **Description:** Add text at top:
   ```
   Account Monitor
   This monitor is currently up to date.
   Data refreshes daily at 2 AM UTC.
   ```

### Step 9: Test and Validate

1. **Test each filter** - Verify they work correctly
2. **Check data freshness** - Ensure Latest Data Dates shows green
3. **Verify contract burndown** - Check lines display correctly
4. **Test account selection** - Switch between accounts
5. **Check date range filter** - Adjust timeframe

## Tips for Best Results

### Visual Design
- Use consistent colors across visualizations
- Keep counter font sizes large and readable
- Use conditional formatting for important metrics
- Align tables and charts in grid layout

### Performance
- Add date filters to limit data scanned
- Use summary tables where possible
- Cache frequently used queries
- Set appropriate refresh schedules

### Data Quality
- Monitor the "Latest Data Dates" table
- Set up alerts for stale data (Verified = False)
- Validate contract data regularly
- Check for null values in contracts

## Troubleshooting

### No data showing in burndown chart
```sql
-- Check if contract_burndown table has data
SELECT COUNT(*), MIN(usage_date), MAX(usage_date)
FROM main.account_monitoring_dev.contract_burndown;
```

### Contracts showing null consumed values
```sql
-- Verify contract IDs match between tables
SELECT DISTINCT contract_id
FROM main.account_monitoring_dev.contract_burndown_summary
WHERE total_consumed IS NULL;
```

### Account filter not working
```sql
-- Verify account metadata exists
SELECT * FROM main.account_monitoring_dev.account_metadata;
```

## Next Steps

After creating the dashboard:

1. ✅ **Share with team** - Set appropriate permissions
2. ✅ **Set up alerts** - Configure notifications for data issues
3. ✅ **Schedule refresh** - Ensure data stays current
4. ✅ **Document usage** - Train team on dashboard features
5. ✅ **Monitor performance** - Check query execution times

## Files Reference

- **Queries:** `/account_monitor/files/notebooks/ibm_style_dashboard_queries`
- **Original Option 2:** `/account_monitor/files/docs/CREATE_LAKEVIEW_DASHBOARD`
- **Contract Guide:** `/account_monitor/files/docs/CONTRACT_BURNDOWN_GUIDE`

---

**Dashboard Type:** Single-page comprehensive view
**Total Visualizations:** 8 (3 counters, 4 tables, 1 line chart)
**Filters:** 3 (Account, Date Range, SKU Count)
**Estimated Creation Time:** 45-60 minutes
