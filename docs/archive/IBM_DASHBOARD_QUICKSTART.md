# IBM-Style Dashboard Quick Start

**⚠️ DEPRECATED - 2026-01-29**

**This guide has been superseded by the Lakeview Dashboard.**

All functionality from the IBM-style queries has been merged into `lakeview_dashboard_queries.sql` (Queries 1-17). The Lakeview dashboard provides more comprehensive features while maintaining all the IBM layout capabilities.

**Please use:**
- `/notebooks/lakeview_dashboard_queries.sql` - All queries (now includes 17 queries)
- `/docs/CREATE_LAKEVIEW_DASHBOARD.md` - Updated guide

**What Changed:**
- IBM Query 3 (Account Info) → Lakeview Query 16
- IBM Query 7 (Combined Burndown) → Lakeview Query 17
- All other queries were duplicates or simplified versions of Lakeview queries

**For full details:** See `/docs/IBM_QUERIES_REDUNDANCY_ANALYSIS.md`

---

# Original Content (Archived)

# IBM-Style Dashboard Quick Start

## What You're Building

A comprehensive single-page dashboard matching the IBM Account Monitor layout with:
- **3 Counters**: SKU count, workspace count, latest date
- **4 Tables**: Data freshness, account info, spending, contracts
- **1 Line Chart**: Contract burndown visualization
- **3 Filters**: Account selection, date range, SKU count

## 5-Minute Quick Start

### 1. Open the Queries Notebook

Navigate to:
```
/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/notebooks/ibm_style_dashboard_queries
```

### 2. Create Dashboard

In Databricks UI:
1. **Dashboards** → **Create Dashboard** → **Lakeview Dashboard**
2. Name: `Account Monitor - IBM Style`
3. Click **Create**

### 3. Add Components in Order

Use the queries from the notebook and follow this sequence:

#### Top Row (Metrics)
```
[Counter]  [Counter]  [Counter]  [Table          ]
SKU Count  Workspace  Date       Data Freshness
           Count
```

**Time:** 10 minutes

#### Second Row (Account Info)
```
[Table: Account Information                      ]
Customer | Salesforce | Business Units | Team
```

**Time:** 5 minutes

#### Third Row (Spending)
```
[Table: Total Spend by Cloud Provider            ]
Customer | Cloud | Dates | DBU | Prices | Revenue
```

**Time:** 5 minutes

#### Fourth Row (Contracts + Burndown)
```
[Table: Contracts      ]  [Chart: Burndown       ]
Platform | ID | Value     Commit vs Consumption
```

**Time:** 15 minutes

### 4. Add Filters

Top bar filters:
- **Account dropdown** - Select which account to view
- **Date range** - Default: Last 12 months
- **SKU count** - Default: 5

**Time:** 10 minutes

## Total Time: ~45 minutes

## Layout Cheat Sheet

### Grid Positions (12-column grid)

| Component | X | Y | Width | Height | Query # |
|-----------|---|---|-------|--------|---------|
| SKU Counter | 0 | 0 | 2 | 2 | Query 1 |
| Workspace Counter | 2 | 0 | 2 | 2 | Query 1 |
| Date Counter | 4 | 0 | 2 | 2 | Query 1 |
| Data Freshness | 6 | 0 | 6 | 2 | Query 2 |
| Account Info | 0 | 2 | 12 | 2 | Query 3 |
| Total Spend | 0 | 4 | 12 | 3 | Query 4 |
| Contracts | 0 | 7 | 6 | 6 | Query 5 |
| Burndown Chart | 6 | 7 | 6 | 6 | Query 6 |

## Query Reference

| Query # | Name | Purpose | Viz Type |
|---------|------|---------|----------|
| 1 | top_metrics | SKU/Workspace/Date | Counter |
| 2 | data_freshness | Latest data check | Table |
| 3 | account_info | Customer details | Table |
| 4 | total_spend_timeframe | Cloud spending | Table |
| 5 | contracts_table | Contract list | Table |
| 6 | contract_burndown_chart | Burndown viz | Line Chart |

## Color Scheme

### Counters
- Background: Light gray (#F5F5F5)
- Text: Dark gray (#424242)
- Font size: 32px

### Tables
- Header: Gray (#EEEEEE)
- Alternating rows: White / Light gray
- Borders: 1px solid #E0E0E0

### Line Chart
- **Commit line**: Gray (#757575) - Solid
- **Consumption line**: Orange (#FF9800) - Solid
- Background: White
- Grid: Light gray

### Conditional Formatting
- **Data Verified = True**: Light green (#C8E6C9)
- **Data Verified = False**: Light red (#FFCDD2)
- **Contract > 80%**: Light yellow (#FFF9C4)
- **Contract > 90%**: Light red (#FFCDD2)

## Common Issues & Fixes

### Issue: No data in burndown chart
**Fix:**
```sql
-- Check if data exists
SELECT COUNT(*) FROM main.account_monitoring_dev.contract_burndown;
```

### Issue: Contracts showing "null" consumed
**Fix:**
```sql
-- Run the refresh job
databricks bundle run account_monitor_daily_refresh --target dev
```

### Issue: Account filter empty
**Fix:**
```sql
-- Verify account metadata
SELECT * FROM main.account_monitoring_dev.account_metadata;
```

## Tips for Success

1. ✅ **Test each query first** in SQL Editor before adding to dashboard
2. ✅ **Add visualizations top to bottom** - easier to position
3. ✅ **Use grid snap** - Enable in dashboard settings
4. ✅ **Save frequently** - Lakeview auto-saves but force save periodically
5. ✅ **Test filters** after adding all components

## Comparison to IBM Original

| Feature | IBM Dashboard | Your Dashboard | Status |
|---------|---------------|----------------|--------|
| Top metrics | ✅ | ✅ | Matching |
| Data freshness | ✅ | ✅ | Matching |
| Account info | ✅ | ✅ | Matching |
| Spending table | ✅ | ✅ | Matching |
| Contracts table | ✅ | ✅ | Matching |
| Burndown chart | ✅ | ✅ | Matching |
| Filters | ✅ | ✅ | Matching |
| Layout | Single page | Single page | Matching |

## Next Steps

After building:

1. **Set refresh schedule**: Daily at 3 AM UTC
2. **Configure permissions**: Share with team
3. **Test account switching**: Try different accounts
4. **Validate data**: Check all metrics load correctly
5. **Bookmark**: Add to favorites

## Help & Resources

- **Full Guide**: `/files/docs/CREATE_IBM_STYLE_DASHBOARD.md`
- **Queries**: `/files/notebooks/ibm_style_dashboard_queries`
- **Config Reference**: `/files/lakeview_dashboard_config_ibm_style.json`
- **Contract Guide**: `/files/docs/CONTRACT_BURNDOWN_GUIDE.md`

## Screenshot Comparison

Your dashboard should match the layout shown in the IBM Account Monitor v2 screenshot with:
- Same component placement
- Similar visual hierarchy
- Matching data structure
- Equivalent functionality

---

**Dashboard:** IBM-Style Account Monitor
**Components:** 8 visualizations + 3 filters
**Time to Build:** ~45 minutes
**Difficulty:** Intermediate
**Data Requirements:** All tables populated
