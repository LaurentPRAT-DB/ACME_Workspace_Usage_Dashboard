# Quick Start - Create Lakeview Dashboard

## TL;DR

```bash
# 1. Get your SQL Warehouse ID
databricks warehouses list --profile <your-profile>

# 2. Create and publish dashboard
python create_lakeview_dashboard.py \
  --profile <your-profile> \
  --warehouse-id <warehouse-id> \
  --publish
```

## Example

```bash
# List warehouses to get ID
databricks warehouses list --profile myprofile

# Output shows:
# ID                                     Name              State
# a1b2c3d4e5f6g7h8                      Shared Warehouse  RUNNING

# Create dashboard
python create_lakeview_dashboard.py \
  --profile myprofile \
  --warehouse-id a1b2c3d4e5f6g7h8 \
  --publish
```

## What Gets Created

A dashboard with **17 visualizations** across **3 pages**:

### Page 1: Contract Burndown (8 visualizations)
- Yesterday's Consumption (counter)
- Active Contracts (counter)
- Pace Distribution (pie chart)
- Contract Burndown Line Chart (actual vs ideal vs limit)
- Contract Summary Table
- Monthly Consumption Bar Chart (stacked by contract)
- Top 10 Workspaces Table
- Contract Analysis Table

### Page 2: Account Overview (6 visualizations)
- Unique SKUs (counter)
- Active Workspaces (counter)
- Account Information (table)
- Data Freshness (table)
- Total Spend by Cloud (table)
- Monthly Cost Trend (bar chart by cloud)
- Combined Burndown (all contracts aggregated line chart)

### Page 3: Usage Analytics (3 visualizations)
- Top Workspaces Table (90 days)
- Top SKUs Table (90 days)
- Cost by Product Category (area chart)

## Layout Design

All visualizations are aligned **one after the other** with no overlaps:
- Uses a 6-column grid system
- Widgets flow from top to bottom
- No gaps between visualizations
- Clean, professional layout

## Prerequisites Checklist

- [ ] Databricks CLI installed (`pip install databricks-cli`)
- [ ] Authenticated with Databricks (`databricks auth login --profile <profile>`)
- [ ] SQL Warehouse available and running
- [ ] Data tables populated (run `account_monitor_notebook.py` first)
- [ ] Python 3.7+ installed

## Data Tables Required

```sql
main.account_monitoring_dev.contract_burndown
main.account_monitoring_dev.contract_burndown_summary
main.account_monitoring_dev.dashboard_data
main.account_monitoring_dev.account_metadata
system.billing.usage
```

## After Creation

1. **View Dashboard**: Go to Databricks → `/Shared` → Open dashboard
2. **Share**: Click Share button → Add users/groups
3. **Schedule**: Set refresh schedule in dashboard settings
4. **Customize**: Edit queries or add filters as needed

## Troubleshooting

**Q: "Error: Warehouse not found"**
A: Run `databricks warehouses list --profile <profile>` to get valid warehouse ID

**Q: "Error: Permission denied"**
A: Ensure you have CREATE permission on `/Shared` path

**Q: "Empty visualizations"**
A: Run `account_monitor_notebook.py` to populate data tables first

**Q: "Dataset not found"**
A: Check tables exist: `SHOW TABLES IN main.account_monitoring_dev`

## Advanced Options

```bash
# Create in custom location
python create_lakeview_dashboard.py \
  --profile myprofile \
  --warehouse-id abc123 \
  --parent-path "/Users/your.email@company.com" \
  --publish

# Create without publishing (draft mode)
python create_lakeview_dashboard.py \
  --profile myprofile \
  --warehouse-id abc123
```

## What's Next?

- Review `CREATE_LAKEVIEW_DASHBOARD.md` for detailed documentation
- Check `lakeview_dashboard_queries.sql` for all SQL queries
- Customize the script to add your own visualizations
- Set up scheduled refresh for automatic updates

## Dashboard Features

✅ **No Duplicates**: Each query/visualization appears exactly once
✅ **Aligned Layout**: All widgets properly positioned in grid
✅ **Complete Coverage**: All 17 queries from notebooks included
✅ **Production Ready**: Uses proper Lakeview API structure
✅ **Maintainable**: Clean Python code, easy to modify

## Need Help?

1. Check `CREATE_LAKEVIEW_DASHBOARD.md` for full documentation
2. Review generated `dashboard_payload.json` for debugging
3. Verify data with queries in `lakeview_dashboard_queries.sql`
