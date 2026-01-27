# Step-by-Step: Create Contract Burndown Lakeview Dashboard

## Prerequisites

✅ Contract data loaded (run `verify_contract_burndown` notebook to confirm)
✅ Burndown table populated with historical data
✅ All queries available in `lakeview_dashboard_queries` notebook

## Step 1: Create New Lakeview Dashboard

1. **Navigate to Dashboards**
   - In Databricks workspace, click **Dashboards** in the left sidebar
   - Or go to: `https://dbc-cbb9ade6-873a.cloud.databricks.com/#dashboards`

2. **Create Dashboard**
   - Click **"Create Dashboard"** button (top right)
   - Select **"Lakeview Dashboard"**
   - Name: `Account Monitor - Contract Burndown`
   - Click **"Create"**

## Step 2: Add Contract Burndown Line Chart (Main Visualization)

### Create the Query

1. Click **"Add"** → **"Visualization"**
2. Click **"Create new query"**
3. **Query Name:** `contract_burndown_chart`
4. **Select Warehouse:** Choose "Serverless Starter Warehouse"
5. **Copy this query:**

```sql
SELECT
  contract_id,
  CONCAT(contract_id, ' ($', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
  usage_date as date,
  ROUND(cumulative_cost, 2) as actual_consumption,
  ROUND(projected_linear_burn, 2) as ideal_consumption,
  ROUND(commitment, 2) as contract_value,
  ROUND(budget_pct_consumed, 1) as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
ORDER BY contract_id, usage_date;
```

6. Click **"Run"** to test the query
7. Click **"Save"**

### Configure the Line Chart

1. In the visualization panel (right side):
   - **Visualization Type:** Select **"Line"**

2. **General Tab:**
   - **Chart Title:** `Contract Burndown - Actual vs Ideal`
   - **Chart Description:** `Blue = Actual Spend | Green = Ideal Linear | Red = Contract Limit`

3. **X-Axis Tab:**
   - **Column:** `date`
   - **Label:** `Date`
   - **Format:** Date

4. **Y-Axis Tab:**
   - Click **"+ Add column"** three times to add three Y-axis columns:

   **Column 1:**
   - **Column:** `actual_consumption`
   - **Label:** `Actual Spend`
   - **Color:** Blue (#1E88E5)
   - **Line Style:** Solid

   **Column 2:**
   - **Column:** `ideal_consumption`
   - **Label:** `Ideal Linear Burn`
   - **Color:** Green (#43A047)
   - **Line Style:** Dashed

   **Column 3:**
   - **Column:** `contract_value`
   - **Label:** `Contract Limit`
   - **Color:** Red (#E53935)
   - **Line Style:** Dotted

5. **Series/Groups Tab:**
   - **Group By:** `contract_label`
   - **Show Legend:** Yes (checked)
   - **Legend Position:** Bottom

6. Click **"Save"**

### Position the Chart

- Drag the chart to the top of your dashboard
- Resize to full width (12 columns)
- Height: 8 rows

## Step 3: Add Contract Summary Table

### Create the Query

1. Click **"Add"** → **"Visualization"**
2. Click **"Create new query"**
3. **Query Name:** `contract_summary`
4. **Select Warehouse:** Choose "Serverless Starter Warehouse"
5. **Copy this query:**

```sql
SELECT
  contract_id as "Contract ID",
  cloud_provider as "Cloud",
  start_date as "Start Date",
  end_date as "End Date",
  CONCAT('$', FORMAT_NUMBER(commitment, 0)) as "Total Value",
  CONCAT('$', FORMAT_NUMBER(total_consumed, 2)) as "Consumed",
  CONCAT('$', FORMAT_NUMBER(budget_remaining, 2)) as "Remaining",
  CONCAT(ROUND(consumed_pct, 1), '%') as "% Consumed",
  pace_status as "Pace Status",
  days_remaining as "Days Left",
  projected_end_date as "Projected End"
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY consumed_pct DESC;
```

6. Click **"Run"** to test
7. Click **"Save"**

### Configure the Table

1. **Visualization Type:** **"Table"**

2. **General Tab:**
   - **Title:** `Active Contracts - Status Summary`
   - **Description:** `🟢 = On Pace | 🟡 = Above Pace | 🔴 = Over Pace`

3. **Columns Tab:**
   - Enable **"Allow Search"**
   - Enable **"Allow Sort"**
   - Enable **"Show Row Numbers"**
   - **Rows Per Page:** 10

4. **Conditional Formatting** (if available):
   - **Column:** `Pace Status`
   - **Rule:** Contains "OVER" → Background color: Light Red
   - **Rule:** Contains "ABOVE" → Background color: Light Yellow
   - **Rule:** Contains "ON PACE" → Background color: Light Green

5. Click **"Save"**

### Position the Table

- Place below the line chart
- Width: 12 columns
- Height: 6 rows

## Step 4: Add Today's Consumption Counter

### Create the Query

1. Click **"Add"** → **"Visualization"**
2. Click **"Create new query"**
3. **Query Name:** `daily_consumption`
4. **Copy this query:**

```sql
SELECT
  CONCAT('$', FORMAT_NUMBER(SUM(daily_cost), 2)) as daily_cost,
  COUNT(DISTINCT contract_id) as active_contracts,
  usage_date as date
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date = CURRENT_DATE() - 1
GROUP BY usage_date;
```

5. Click **"Run"** and **"Save"**

### Configure the Counter

1. **Visualization Type:** **"Counter"**

2. **General Tab:**
   - **Title:** `Yesterday's Consumption`
   - **Label:** `Total Spend`

3. **Value Tab:**
   - **Column:** `daily_cost`
   - **Format:** Text (already formatted with $)

4. Click **"Save"**

### Position the Counter

- Place at top left, above the line chart
- Width: 3 columns
- Height: 2 rows

## Step 5: Add Pace Distribution Pie Chart

### Create the Query

1. Click **"Add"** → **"Visualization"**
2. Click **"Create new query"**
3. **Query Name:** `pace_distribution`
4. **Copy this query:**

```sql
SELECT
  pace_status,
  COUNT(*) as contract_count
FROM main.account_monitoring_dev.contract_burndown_summary
GROUP BY pace_status
ORDER BY
  CASE
    WHEN pace_status LIKE '%OVER%' THEN 1
    WHEN pace_status LIKE '%ABOVE%' THEN 2
    WHEN pace_status LIKE '%ON%' THEN 3
    ELSE 4
  END;
```

5. Click **"Run"** and **"Save"**

### Configure the Pie Chart

1. **Visualization Type:** **"Pie"** or **"Donut"**

2. **General Tab:**
   - **Title:** `Contract Pace Distribution`

3. **Values Tab:**
   - **Column:** `contract_count`
   - **Label Column:** `pace_status`

4. **Colors Tab (if available):**
   - Assign colors to match status meanings

5. Click **"Save"**

### Position the Pie Chart

- Place next to the counter (top right area)
- Width: 3 columns
- Height: 4 rows

## Step 6: Add Monthly Trend Bar Chart

### Create the Query

1. Click **"Add"** → **"Visualization"**
2. Click **"Create new query"**
3. **Query Name:** `monthly_trend`
4. **Copy this query:**

```sql
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  contract_id,
  SUM(daily_cost) as monthly_cost,
  COUNT(*) as days_active
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), contract_id
ORDER BY month, contract_id;
```

5. Click **"Run"** and **"Save"**

### Configure the Bar Chart

1. **Visualization Type:** **"Bar"** with stacking enabled

2. **General Tab:**
   - **Title:** `Monthly Consumption by Contract`

3. **X-Axis Tab:**
   - **Column:** `month`
   - **Label:** `Month`

4. **Y-Axis Tab:**
   - **Column:** `monthly_cost`
   - **Label:** `Cost ($)`
   - **Format:** Currency

5. **Series Tab:**
   - **Group By:** `contract_id`
   - **Stacking:** Enabled

6. Click **"Save"**

### Position the Bar Chart

- Place below summary table
- Width: 12 columns
- Height: 6 rows

## Step 7: Dashboard Settings

### Configure Refresh Schedule

1. Click **"Schedule"** (top right)
2. **Refresh Schedule:**
   - **Frequency:** Daily
   - **Time:** 3:00 AM UTC (after daily refresh job)
   - **Timezone:** UTC
3. Click **"Save"**

### Set Permissions

1. Click **"Share"** button (top right)
2. Add users/groups who should have access:
   - **Can View:** All relevant stakeholders
   - **Can Edit:** Dashboard administrators
   - **Can Manage:** You
3. Click **"Done"**

### Add Filters (Optional)

1. Click **"Add"** → **"Filter"**
2. **Filter Type:** Date Range
   - **Parameter Name:** `date_range`
   - **Default:** Last 180 days
3. Apply filter to relevant queries

## Step 8: Publish Dashboard

1. Review all visualizations
2. Adjust layout and sizing as needed
3. Click **"Publish"** (top right)
4. Dashboard is now live!

## Final Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Counter: Daily Cost    │ Pie: Pace Distribution             │
│ (3x2)                  │ (3x4)                               │
├────────────────────────┴─────────────────────────────────────┤
│                                                               │
│          Line Chart: Contract Burndown                        │
│          (Actual vs Ideal vs Limit)                           │
│          (12x8)                                               │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│          Table: Contract Summary                              │
│          (Status, Pace, Projections)                          │
│          (12x6)                                               │
├───────────────────────────────────────────────────────────────┤
│          Bar Chart: Monthly Trend                             │
│          (Stacked by Contract)                                │
│          (12x6)                                               │
└───────────────────────────────────────────────────────────────┘
```

## Verification Checklist

After creating the dashboard, verify:

- [ ] Line chart shows blue (actual), green (ideal), and red (limit) lines
- [ ] Chart displays data for both contracts
- [ ] Summary table shows pace status with emoji indicators
- [ ] Counter displays yesterday's consumption
- [ ] Pie chart shows pace distribution
- [ ] Bar chart shows monthly trends
- [ ] Dashboard refreshes daily at 3 AM UTC
- [ ] Permissions are set correctly
- [ ] All queries run without errors

## Troubleshooting

### "No data" in visualizations

**Check:**
```sql
SELECT COUNT(*) FROM main.account_monitoring_dev.contract_burndown;
```

If 0, run:
```bash
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

### Chart shows flat lines

**Check date range:**
```sql
SELECT MIN(usage_date), MAX(usage_date)
FROM main.account_monitoring_dev.contract_burndown;
```

Adjust the date filter in Query 1 if needed.

### Pace status not showing emojis

The pace_status field includes emoji characters. If not displaying, check:
- Browser font support
- Databricks workspace settings

## Next Steps

1. ✅ Dashboard created
2. Monitor daily consumption
3. Set up alerts for contracts over pace
4. Share dashboard link with stakeholders
5. Add more visualizations as needed

## Dashboard URL

After publishing, your dashboard will be available at:
```
https://dbc-cbb9ade6-873a.cloud.databricks.com/#/dashboards/<dashboard-id>
```

Bookmark this URL for easy access!

---

**Need Help?** See `CONTRACT_BURNDOWN_GUIDE.md` for more details.
