# Databricks Account Monitor

Recreates IBM Account Monitor functionality using Databricks System Tables for cost and usage tracking.

## Overview

This solution provides comprehensive account monitoring and cost tracking capabilities using:
- **System Tables**: `system.billing.usage` and `system.billing.list_prices`
- **Custom Tables**: Contract management and account metadata
- **Visualizations**: Pre-built queries and Lakeview dashboard components

## Features

### 1. Account Overview
- Top SKU count and workspace count
- Date range selection and filtering
- Real-time data freshness indicators

### 2. Latest Data Dates
- Data freshness validation for consumption and metrics
- Automated verification status

### 3. Account Information
- Customer details and Salesforce integration
- Business unit hierarchy (L0-L3)
- Team assignments (AE, SA, DSA)

### 4. Total Spend Analysis
- Breakdown by cloud provider (AWS, Azure, GCP)
- DBU consumption tracking
- List price vs. discounted price comparison
- Actual revenue calculation

### 5. Contract Management
- Contract tracking with start/end dates
- Total value and consumption monitoring
- Consumption percentage calculation
- Multi-cloud contract support

### 6. Contract Burndown Chart
- Visual representation of cumulative spending
- Commitment vs. actual consumption trends
- Projection for contract completion

### 7. Usage Analytics
- Top consuming workspaces
- Top consuming SKUs
- Monthly spend trends
- Cost by product category

## Quick Start

### Step 1: Import Notebook

```bash
# Upload the notebook to your Databricks workspace
databricks workspace import account_monitor_notebook.py \
  /Users/<your-email>/account_monitor_notebook \
  --language PYTHON --format SOURCE
```

### Step 2: Create Custom Tables

Run cells 2-3 in the notebook to create:
- `account_monitoring.contracts` - Contract tracking
- `account_monitoring.account_metadata` - Customer information

### Step 3: Populate Metadata

Update the sample data in the notebook with your actual:
- Contract information
- Customer details
- Salesforce IDs
- Business unit hierarchy
- Team assignments

### Step 4: Run Analysis

Execute the notebook cells to generate:
- Account overview metrics
- Usage and cost reports
- Contract burndown analysis
- Export data for dashboards

### Step 5: Create Lakeview Dashboard

Use the exported `account_monitoring.dashboard_data` table to build a Lakeview dashboard.

## Data Sources

### System Tables (Built-in)

**system.billing.usage**
- `usage_date` - Date of usage
- `account_id` - Databricks account ID
- `workspace_id` - Workspace identifier
- `cloud_provider` - aws, azure, or gcp
- `sku_name` - Product SKU
- `usage_quantity` - DBUs consumed
- `usage_metadata.total_price` - Actual cost
- `list_price_per_unit` - List price per DBU

**system.billing.list_prices**
- `sku_name` - Product SKU
- `cloud` - Cloud provider
- `pricing.default_price_per_unit` - Price per unit
- `price_start_time` - Price effective date
- `price_end_time` - Price expiration date

### Custom Tables (You Create)

**account_monitoring.contracts**
```sql
- contract_id (STRING) - Unique contract identifier
- account_id (STRING) - Databricks account ID
- cloud_provider (STRING) - aws, azure, or gcp
- start_date (DATE) - Contract start date
- end_date (DATE) - Contract end date
- total_value (DECIMAL) - Total contract value
- currency (STRING) - USD, EUR, etc.
- commitment_type (STRING) - 'DBU' or 'SPEND'
- status (STRING) - 'ACTIVE', 'EXPIRED', 'PENDING'
```

**account_monitoring.account_metadata**
```sql
- account_id (STRING) - Databricks account ID
- customer_name (STRING) - Customer display name
- salesforce_id (STRING) - SFDC account ID
- business_unit_l0 (STRING) - Top-level BU (e.g., 'EMEA')
- business_unit_l1 (STRING) - Second-level BU (e.g., 'Central')
- business_unit_l2 (STRING) - Third-level BU (e.g., 'Switzerland')
- business_unit_l3 (STRING) - Fourth-level BU (e.g., 'Enterprise')
- account_executive (STRING) - AE name
- solutions_architect (STRING) - SA name
- delivery_solutions_architect (STRING) - DSA name
```

## Key Queries

### Get Total Spend by Cloud Provider

```sql
SELECT
  cloud_provider,
  SUM(usage_quantity) as total_dbu,
  SUM(usage_metadata.total_price) as total_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY cloud_provider;
```

### Check Data Freshness

```sql
SELECT
  MAX(usage_date) as latest_data,
  DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind
FROM system.billing.usage;
```

### Contract Consumption Status

```sql
SELECT
  c.contract_id,
  c.total_value as commitment,
  SUM(u.usage_metadata.total_price) as consumed,
  ROUND(SUM(u.usage_metadata.total_price) / c.total_value * 100, 1) as consumed_pct
FROM account_monitoring.contracts c
LEFT JOIN system.billing.usage u
  ON c.account_id = u.account_id
  AND u.usage_date BETWEEN c.start_date AND c.end_date
GROUP BY c.contract_id, c.total_value;
```

### Top Consuming Workspaces

```sql
SELECT
  workspace_id,
  SUM(usage_metadata.total_price) as total_cost,
  COUNT(DISTINCT sku_name) as sku_count
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY workspace_id
ORDER BY total_cost DESC
LIMIT 10;
```

## Dashboard Components

### 1. Key Metrics Cards
- Total Spend (Last 365 days)
- Total DBUs Consumed
- Active Workspaces
- Unique SKUs Used
- Average Daily Spend

### 2. Data Freshness Indicators
- Consumption data: Latest date and verification status
- Metrics data: Latest date and verification status

### 3. Spend Analysis Table
- Customer Name
- Cloud Provider
- Start/End Dates
- DBU Consumption
- List Price vs. Discounted Price vs. Revenue

### 4. Contract Table
- Platform
- Contract ID
- Start/End Dates
- Total Value
- Consumed Amount
- Consumption %

### 5. Burndown Chart
- X-axis: Date
- Y-axis: Cumulative Cost
- Lines: Commitment (dashed) vs. Actual (solid)
- Multiple contracts displayed

### 6. Monthly Trend Chart
- Bar chart showing monthly costs
- Grouped by cloud provider
- Last 12 months

### 7. Product Category Breakdown
- Pie or bar chart
- Categories: All Purpose, Jobs, DLT, SQL, Model Serving, etc.
- Filter by date range

## Automation

### Daily Data Refresh

Create a job to refresh the dashboard data daily:

```python
# Schedule as a daily job
spark.sql("""
  CREATE OR REPLACE TABLE account_monitoring.dashboard_data AS
  SELECT ... -- full query from notebook cell 14
""")
```

### Weekly Contract Report

Email weekly contract consumption status:

```python
from databricks.sdk.service.jobs import Task, TaskEmailNotifications

# Add to your job configuration
email_notifications = TaskEmailNotifications(
    on_success=["your-team@company.com"],
    on_failure=["your-team@company.com"]
)
```

## Customization

### Adding Custom Tags

Track costs by custom tags:

```sql
SELECT
  custom_tags['project'] as project,
  custom_tags['environment'] as environment,
  SUM(usage_metadata.total_price) as cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
  AND custom_tags IS NOT NULL
GROUP BY custom_tags['project'], custom_tags['environment'];
```

### Cost Allocation by Team

```sql
SELECT
  custom_tags['team'] as team,
  workspace_id,
  SUM(usage_metadata.total_price) as team_cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY custom_tags['team'], workspace_id
ORDER BY team_cost DESC;
```

### Forecast Future Spend

```sql
WITH daily_avg AS (
  SELECT
    cloud_provider,
    AVG(daily_cost) as avg_daily_cost
  FROM (
    SELECT
      cloud_provider,
      usage_date,
      SUM(usage_metadata.total_price) as daily_cost
    FROM system.billing.usage
    WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
    GROUP BY cloud_provider, usage_date
  )
  GROUP BY cloud_provider
)
SELECT
  cloud_provider,
  avg_daily_cost,
  avg_daily_cost * 30 as projected_monthly_cost,
  avg_daily_cost * 365 as projected_annual_cost
FROM daily_avg;
```

## Troubleshooting

### No Data in system.billing.usage

**Issue**: Query returns no results

**Solutions**:
1. Check if system tables are enabled in your account
2. Verify you have the correct permissions
3. Check if data is available: `SELECT COUNT(*) FROM system.billing.usage`
4. Contact Databricks support to enable system tables

### Contract Consumption Not Matching

**Issue**: Contract consumption doesn't match actual usage

**Solutions**:
1. Verify contract dates are correct
2. Check account_id matches between tables
3. Ensure cloud_provider matches exactly ('aws' vs 'AWS')
4. Verify usage_date is within contract period

### Dashboard Shows Stale Data

**Issue**: Dashboard not updating with latest data

**Solutions**:
1. Check data freshness query (Section 5 of notebook)
2. Verify system tables are updating (usually 24-48 hour lag)
3. Refresh the dashboard data table (Cell 14)
4. Schedule automated refresh job

## Best Practices

1. **Regular Updates**: Refresh dashboard data daily
2. **Data Validation**: Monitor data freshness indicators
3. **Contract Tracking**: Update contract table when new agreements are signed
4. **Tag Hygiene**: Enforce consistent custom tag usage
5. **Access Control**: Grant appropriate permissions to dashboard users
6. **Backup**: Regularly backup account_monitoring tables
7. **Documentation**: Keep metadata tables up-to-date

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Databricks system tables documentation
3. Contact your Databricks account team

## License

Internal use only - Databricks Field Engineering
