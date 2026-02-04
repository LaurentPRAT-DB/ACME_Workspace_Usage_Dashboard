# Creating the Lakeview Dashboard

This guide explains how to create the Account Monitor Lakeview dashboard programmatically using the `create_lakeview_dashboard.py` script.

## Overview

The script creates a comprehensive Lakeview dashboard with 3 pages:
1. **Contract Burndown** - Real-time contract consumption tracking (8 visualizations)
2. **Account Overview** - High-level metrics and spending overview (6 visualizations)
3. **Usage Analytics** - Detailed usage breakdown (3 visualizations)

## Prerequisites

### 1. Data Tables Required

Ensure these tables exist and contain data:
- `main.account_monitoring_dev.contract_burndown`
- `main.account_monitoring_dev.contract_burndown_summary`
- `main.account_monitoring_dev.dashboard_data`
- `main.account_monitoring_dev.account_metadata`
- `system.billing.usage`

Run the `account_monitor_notebook.py` notebook first to create these tables.

### 2. Databricks CLI Setup

Install and configure Databricks CLI:
```bash
# Install
pip install databricks-cli

# Authenticate
databricks auth login --profile <your-profile>
```

### 3. SQL Warehouse

You need a SQL Warehouse ID. To find it:
```bash
databricks warehouses list --profile <your-profile>
```

Or from the Databricks UI:
1. Go to SQL Warehouses
2. Click on a warehouse
3. Copy the ID from the URL: `/sql/warehouses/<warehouse-id>`

## Usage

### Basic Usage

```bash
python create_lakeview_dashboard.py \
  --profile <your-databricks-profile> \
  --warehouse-id <your-warehouse-id>
```

### With Auto-Publish

```bash
python create_lakeview_dashboard.py \
  --profile <your-databricks-profile> \
  --warehouse-id <your-warehouse-id> \
  --publish
```

### Custom Parent Path

```bash
python create_lakeview_dashboard.py \
  --profile <your-databricks-profile> \
  --warehouse-id <your-warehouse-id> \
  --parent-path "/Users/your.email@company.com" \
  --publish
```

## Dashboard Structure

### Page 1: Contract Burndown

**Layout (6-column grid):**
- Row 1 (y=0):
  - Yesterday's Consumption (counter) - x=0, width=2, height=3
  - Active Contracts (counter) - x=2, width=2, height=3
  - Pace Distribution (pie chart) - x=4, width=2, height=6

- Row 2 (y=3):
  - Contract Burndown Line Chart - x=0, width=4, height=8
    - Shows actual vs ideal vs limit per contract

- Row 3 (y=6):
  - Contract Summary Table - x=4, width=2, height=6

- Row 4 (y=11):
  - Monthly Consumption Bar Chart - x=0, width=6, height=6
    - Stacked by contract_id

- Row 5 (y=17):
  - Top Workspaces Table - x=0, width=3, height=6
  - Contract Analysis Table - x=3, width=3, height=6

### Page 2: Account Overview

**Layout:**
- Row 1 (y=0):
  - Unique SKUs (counter) - x=0, width=2, height=3
  - Active Workspaces (counter) - x=2, width=2, height=3
  - Account Information (table) - x=4, width=2, height=3

- Row 2 (y=3):
  - Data Freshness Table - x=0, width=6, height=3

- Row 3 (y=6):
  - Total Spend by Cloud Table - x=0, width=6, height=5

- Row 4 (y=11):
  - Monthly Cost Trend Bar Chart - x=0, width=6, height=6
    - Grouped by cloud_provider

- Row 5 (y=17):
  - Combined Burndown Line Chart - x=0, width=6, height=6
    - All contracts aggregated

### Page 3: Usage Analytics

**Layout:**
- Row 1 (y=0):
  - Top Workspaces Table - x=0, width=3, height=6
  - Top SKUs Table - x=3, width=3, height=6

- Row 2 (y=6):
  - Product Category Area Chart - x=0, width=6, height=6

## Output Files

The script creates two files for debugging:
- `dashboard_payload.json` - The serialized dashboard structure
- `api_payload.json` - The complete API request payload

## After Creation

### View the Dashboard

1. Go to Databricks workspace
2. Navigate to the parent path (default: `/Shared`)
3. Open the dashboard: "Account Monitor - Cost & Usage Tracking with Contract Burndown"

### Publish the Dashboard

If you didn't use `--publish`, publish manually:
```bash
databricks api post /api/2.0/lakeview/dashboards/<dashboard-id>/published \
  --profile <your-profile>
```

### Update the Dashboard

To update an existing dashboard:
```bash
# Get dashboard ID
databricks api get /api/2.0/lakeview/dashboards --profile <your-profile>

# Update dashboard
databricks api patch /api/2.0/lakeview/dashboards/<dashboard-id> \
  --profile <your-profile> \
  --json-file api_payload.json
```

## Customization

### Change Catalog/Schema

Edit the script constants:
```python
CATALOG = "main"
SCHEMA = "account_monitoring_dev"
```

### Modify Visualizations

The `LakeviewDashboardBuilder` class provides methods for each widget type:
- `add_counter()` - KPI counters
- `add_line_chart()` - Line charts
- `add_bar_chart()` - Bar charts (grouped or stacked)
- `add_pie_chart()` - Pie charts
- `add_table()` - Data tables
- `add_area_chart()` - Area charts

### Add New Queries

1. Add dataset:
```python
builder.add_dataset(
    "dataset_name",
    "Display Name",
    "SELECT ... FROM ..."
)
```

2. Add visualization:
```python
builder.add_bar_chart(
    page,
    "dataset_name",
    "x_field",
    "y_field",
    "Chart Title",
    {"x": 0, "y": 0, "width": 3, "height": 4}
)
```

## Troubleshooting

### Error: "Dataset not found"

Check that all tables exist:
```sql
SHOW TABLES IN main.account_monitoring_dev;
```

### Error: "Warehouse not found"

Verify warehouse ID:
```bash
databricks warehouses list --profile <your-profile>
```

### Error: "Permission denied"

Ensure you have:
- CREATE permission on the parent path
- USE CATALOG permission on `main`
- USE SCHEMA permission on `account_monitoring_dev`
- CAN USE permission on the SQL Warehouse

### Empty Visualizations

Check data exists in tables:
```sql
SELECT COUNT(*) FROM main.account_monitoring_dev.contract_burndown;
SELECT COUNT(*) FROM main.account_monitoring_dev.dashboard_data;
```

Run the `account_monitor_notebook.py` to populate tables if needed.

## Query Reference

All queries are defined in `lakeview_dashboard_queries.sql`. The script uses these queries to create 16 datasets:

1. contract_burndown_chart
2. contract_summary_table
3. daily_consumption_counter
4. pace_distribution_pie
5. contract_monthly_trend
6. top_workspaces_detailed
7. contract_detailed_analysis
8. account_overview
9. data_freshness
10. total_spend
11. monthly_trend
12. top_workspaces
13. top_skus
14. product_category
15. account_info
16. combined_burndown

## Dashboard Grid System

Lakeview uses a **6-column grid** system:
- Width: 1-6 columns
- Height: units (typically 3-8 for most widgets)
- X position: 0-5 (column start)
- Y position: 0+ (row, grows downward)

**Best Practices:**
- Counters: width=2, height=3
- Tables: width=3-6, height=6
- Charts: width=3-6, height=6-8
- Leave no gaps between widgets for clean alignment

## API Reference

### Create Dashboard
```bash
databricks api post /api/2.0/lakeview/dashboards \
  --profile <profile> \
  --json '{
    "display_name": "Dashboard Name",
    "warehouse_id": "warehouse-id",
    "parent_path": "/Shared",
    "serialized_dashboard": "<json-string>"
  }'
```

### Update Dashboard
```bash
databricks api patch /api/2.0/lakeview/dashboards/<dashboard-id> \
  --profile <profile> \
  --json '{
    "serialized_dashboard": "<json-string>"
  }'
```

### Publish Dashboard
```bash
databricks api post /api/2.0/lakeview/dashboards/<dashboard-id>/published \
  --profile <profile>
```

### List Dashboards
```bash
databricks api get /api/2.0/lakeview/dashboards --profile <profile>
```

### Get Dashboard
```bash
databricks api get /api/2.0/lakeview/dashboards/<dashboard-id> --profile <profile>
```

## Related Files

- `lakeview_dashboard_queries.sql` - All SQL queries with documentation
- `account_monitor_notebook.py` - Data preparation notebook
- `lakeview_dashboard_config.json` - Configuration reference
- `create_lakeview_dashboard.py` - This creation script

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Databricks Lakeview documentation
3. Examine the generated JSON files for debugging
