# 🚀 Quick Start: Create Your Contract Burndown Dashboard

## ✅ Everything is Ready!

Your contract burndown data is populated and ready for visualization. Follow these 3 simple steps:

## Step 1: Open the Dashboard Queries Notebook (2 minutes)

📂 **Open this notebook in your workspace:**
```
/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/notebooks/lakeview_dashboard_queries
```

**Direct Link:**
```
https://dbc-cbb9ade6-873a.cloud.databricks.com/#workspace/Users/laurent.prat@mailwatcher.net/account_monitor/notebooks/lakeview_dashboard_queries
```

This notebook contains 7 ready-to-use queries for your dashboard. Each query includes:
- ✅ The SQL code (copy/paste ready)
- ✅ Visualization type to use
- ✅ Configuration settings
- ✅ Chart/table setup instructions

## Step 2: Create the Lakeview Dashboard (10 minutes)

### 2.1 Start the Dashboard

1. Go to **Dashboards** → **Create Dashboard**
2. Select **"Lakeview Dashboard"**
3. Name it: `Account Monitor - Contract Burndown`

### 2.2 Add the Main Line Chart

**This is your primary visualization!**

1. Click **"Add"** → **"Visualization"** → **"Create new query"**
2. Query name: `contract_burndown_chart`
3. **Copy Query 1** from the `lakeview_dashboard_queries` notebook
4. Run and Save
5. Select visualization type: **Line Chart**
6. Configure:
   - **X-Axis:** `date`
   - **Y-Axis:** Add 3 columns:
     - `actual_consumption` (Blue, Solid line)
     - `ideal_consumption` (Green, Dashed line)
     - `contract_value` (Red, Dotted line)
   - **Group By:** `contract_label`
   - **Show Legend:** Yes

### 2.3 Add the Summary Table

1. Click **"Add"** → **"Visualization"** → **"Create new query"**
2. Query name: `contract_summary`
3. **Copy Query 2** from the `lakeview_dashboard_queries` notebook
4. Run and Save
5. Select visualization type: **Table**
6. Enable sorting and search

### 2.4 Publish

Click **"Publish"** at the top right!

## Step 3: View Your Dashboard

Your dashboard will show:

📈 **Line Chart** - Real-time burndown showing:
- Blue line = Your actual spending
- Green line = Ideal linear spending
- Red line = Contract limit

📊 **Summary Table** - Current status:
- 🟢 ON PACE = Spending as planned
- 🟡 ABOVE PACE = Spending 10-20% faster
- 🔴 OVER PACE = Spending >20% faster (needs action!)
- 🔵 UNDER PACE = Spending slower than expected

## 📚 Detailed Instructions

For complete step-by-step instructions with all 7 visualizations:

**Open this guide:**
```
/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/docs/CREATE_LAKEVIEW_DASHBOARD
```

This includes:
- Screenshots and detailed configuration
- 5 additional visualizations (counters, pie charts, bar charts)
- Troubleshooting tips
- Dashboard layout recommendations

## 🎯 What You'll See

### Sample Data Already Loaded

Your dashboard will immediately show:

**Contract 1: $2,000 1-Year Contract**
- Shows full year of historical consumption
- Demonstrates realistic burn patterns
- Ideal for testing and learning

**Contract 2: $500,000 Enterprise Contract**
- Multi-year contract tracking
- Good for comparison

### Expected Visualizations

**Line Chart:**
```
              Contract Limit (Red horizontal line)
              ─────────────────────────────────────
        $2000 │                                  ─
              │                              ─
              │                          ─   Actual
              │                      ─       (Blue)
        $1500 │                  ─
              │              ─       Ideal
              │          ─           (Green)
        $1000 │      ─
              │  ─
        $500  │
              └─────────────────────────────────────
               Jan  Feb  Mar  Apr  May  Jun  Jul
```

**Summary Table:**
```
Contract ID           | Status      | % Consumed | Days Left
──────────────────────|─────────────|────────────|──────────
CONTRACT-2026-001     | 🟢 ON PACE  | 47.3%      | 180
CONTRACT-ENTERPRISE-1 | 🟡 ABOVE    | 12.8%      | 720
```

## ⚡ Pro Tips

### Quick Copy-Paste

All 7 queries in the `lakeview_dashboard_queries` notebook are ready to copy directly into Lakeview:

1. **Query 1** → Line Chart (Main burndown)
2. **Query 2** → Table (Summary)
3. **Query 3** → Counter (Today's cost)
4. **Query 4** → Pie Chart (Pace distribution)
5. **Query 5** → Bar Chart (Monthly trend)
6. **Query 6** → Table (Top workspaces)
7. **Query 7** → Table (Detailed analysis)

Start with Queries 1 & 2, then add others as needed.

### Refresh Schedule

Set your dashboard to refresh **daily at 3:00 AM UTC** to sync with the data refresh job.

### Share Your Dashboard

After publishing:
1. Click **"Share"** button
2. Add team members with "Can View" permissions
3. Copy the dashboard URL to share

## 🔄 Data Updates

Your dashboard data refreshes automatically:
- **Daily at 2:00 AM UTC** - Data refresh job runs
- **Daily at 3:00 AM UTC** - Dashboard refreshes (if configured)

To manually refresh data:
```bash
databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
```

## 🆘 Need Help?

### Common Issues

**"No data in chart"**
→ Run the `verify_contract_burndown` notebook to check data

**"Query error"**
→ Verify catalog name is `main.account_monitoring_dev`

**"Chart looks wrong"**
→ Check date range filter (should be last 180 days)

### Documentation

- **Full Guide:** `/account_monitor/docs/CREATE_LAKEVIEW_DASHBOARD`
- **Burndown Guide:** `/account_monitor/docs/CONTRACT_BURNDOWN_GUIDE`
- **Verification Notebook:** `/account_monitor/notebooks/verify_contract_burndown`

## ✨ You're All Set!

Everything is configured and ready:
- ✅ Sample contracts loaded
- ✅ Burndown data populated
- ✅ Queries tested and ready
- ✅ Step-by-step instructions available
- ✅ Data refreshes automatically

**Time to create your dashboard:** ~10-15 minutes

**Start here:**
1. Open `lakeview_dashboard_queries` notebook
2. Follow Step 2 above
3. Enjoy your real-time contract burn down visualization! 🎉

---

**Quick Links:**
- **Queries:** [/account_monitor/notebooks/lakeview_dashboard_queries](https://dbc-cbb9ade6-873a.cloud.databricks.com/#workspace/Users/laurent.prat@mailwatcher.net/account_monitor/notebooks/lakeview_dashboard_queries)
- **Verification:** [/account_monitor/notebooks/verify_contract_burndown](https://dbc-cbb9ade6-873a.cloud.databricks.com/#workspace/Users/laurent.prat@mailwatcher.net/account_monitor/notebooks/verify_contract_burndown)
- **Full Guide:** [/account_monitor/docs/CREATE_LAKEVIEW_DASHBOARD](https://dbc-cbb9ade6-873a.cloud.databricks.com/#workspace/Users/laurent.prat@mailwatcher.net/account_monitor/docs/CREATE_LAKEVIEW_DASHBOARD)
