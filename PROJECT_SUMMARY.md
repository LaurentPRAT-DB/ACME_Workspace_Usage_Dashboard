# Databricks Account Monitor - Project Summary

## Overview

This project recreates the IBM Account Monitor dashboard using Databricks System Tables to track cost and usage across your Databricks account. The solution provides comprehensive monitoring of DBU consumption, spending trends, contract management, and detailed usage analytics.

## Project Structure

```
databricks_conso_reports/
├── README.md                          # Main documentation and getting started guide
├── PROJECT_SUMMARY.md                 # This file - high-level overview
├── QUICK_REFERENCE.md                 # Common queries and patterns
├── OPERATIONS_GUIDE.md                # Daily, weekly, monthly operations
├── account_monitor_queries.sql        # Core SQL queries for all reports
├── account_monitor_notebook.py        # Main analysis notebook
├── setup_account_monitor.py           # Automated setup script
└── lakeview_dashboard_config.json     # Dashboard configuration template
```

## Components

### 1. Core Documentation

**README.md** (9.4 KB)
- Complete setup instructions
- Data source descriptions
- Dashboard component specifications
- Troubleshooting guide
- Best practices

**QUICK_REFERENCE.md** (11 KB)
- Ready-to-use SQL queries
- Common patterns and templates
- Cost allocation examples
- Anomaly detection queries
- Forecasting queries

**OPERATIONS_GUIDE.md** (16 KB)
- Daily operations checklist
- Weekly and monthly reviews
- Maintenance procedures
- Alerting setup
- Performance optimization
- Backup and recovery

### 2. Implementation Files

**account_monitor_queries.sql** (8.4 KB)
- 11 core SQL queries covering:
  - Account overview metrics
  - Data freshness checks
  - Total spend analysis
  - Contract tracking
  - Usage trends
  - Cost by product category
  - Top consumers (workspaces and SKUs)

**account_monitor_notebook.py** (17 KB)
- Complete Python notebook with 15 sections:
  - Setup and configuration
  - Custom table creation
  - All analysis queries
  - Visualizations (contract burndown, monthly trends)
  - Data export for dashboards
  - Summary statistics

**setup_account_monitor.py** (14 KB)
- Automated setup script that:
  - Creates account_monitoring database
  - Creates contracts table
  - Creates account_metadata table
  - Creates dashboard_data table
  - Inserts sample data
  - Creates scheduled refresh job
  - Verifies system tables access

**lakeview_dashboard_config.json** (8.4 KB)
- Dashboard configuration with:
  - 10 dataset definitions
  - 2 pages (Account Overview, Usage Analytics)
  - Multiple visualizations (tables, charts, counters)
  - Filter specifications
  - Refresh schedule

## Key Features

### Dashboard Sections

1. **Account Overview**
   - Top SKU count and workspace count
   - Data freshness indicators
   - Account information (customer, Salesforce ID, business units, team)
   - Total spend by cloud provider

2. **Contract Management**
   - Contract details (ID, dates, value)
   - Consumption tracking
   - Contract burndown visualization
   - Consumption pace monitoring

3. **Usage Analytics**
   - Monthly cost trends
   - Top consuming workspaces
   - Top consuming SKUs
   - Cost by product category
   - Custom tag analysis

4. **Alerting & Monitoring**
   - High spend alerts
   - Contract overrun warnings
   - Data freshness checks
   - Anomaly detection

## Data Architecture

### System Tables (Read-Only)
```
system.billing.usage
├── usage_date (partition key)
├── account_id
├── workspace_id
├── cloud_provider
├── sku_name
├── usage_quantity
├── usage_metadata.total_price
└── custom_tags

system.billing.list_prices
├── sku_name
├── cloud
├── pricing.default_price_per_unit
├── price_start_time
└── price_end_time
```

### Custom Tables (You Create)
```
account_monitoring.contracts
├── contract_id (primary key)
├── account_id
├── cloud_provider
├── start_date
├── end_date
├── total_value
├── commitment_type
└── status

account_monitoring.account_metadata
├── account_id (primary key)
├── customer_name
├── salesforce_id
├── business_unit_l0..l3
├── account_executive
├── solutions_architect
└── delivery_solutions_architect

account_monitoring.dashboard_data
├── usage_date (partition key)
├── All fields from usage + metadata
├── Calculated fields (list_cost, discounted_cost)
└── product_category
```

## Implementation Steps

### Phase 1: Setup (30 minutes)
1. Run `python setup_account_monitor.py`
2. Verify system tables access
3. Create custom tables
4. Insert sample data

### Phase 2: Configuration (1-2 hours)
1. Update account metadata with real data
2. Add contract information
3. Configure refresh schedule
4. Test queries

### Phase 3: Dashboard (2-3 hours)
1. Upload notebook to workspace
2. Run analysis
3. Create Lakeview dashboard
4. Configure filters and visualizations
5. Set up access permissions

### Phase 4: Operations (Ongoing)
1. Daily: Check data freshness and anomalies
2. Weekly: Review top consumers and update contracts
3. Monthly: Review contracts, archive old data
4. Quarterly: Update metadata and permissions

## Key Queries

### Check Today's Spend
```sql
SELECT
  SUM(usage_metadata.total_price) as today_spend
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE() - 1;
```

### Contract Status
```sql
SELECT
  contract_id,
  ROUND(consumed/total_value*100, 1) as pct_consumed
FROM (
  SELECT
    c.contract_id,
    c.total_value,
    SUM(u.usage_metadata.total_price) as consumed
  FROM account_monitoring.contracts c
  LEFT JOIN system.billing.usage u
    ON c.account_id = u.account_id
    AND u.usage_date BETWEEN c.start_date AND c.end_date
  GROUP BY c.contract_id, c.total_value
);
```

### Top Workspaces
```sql
SELECT
  workspace_id,
  SUM(usage_metadata.total_price) as cost
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id
ORDER BY cost DESC
LIMIT 10;
```

## Metrics Tracked

### Financial Metrics
- Total spend (actual, list, discounted)
- DBU consumption
- Cost per workspace
- Cost per SKU
- Daily/weekly/monthly trends
- Contract consumption rate

### Operational Metrics
- Active workspaces
- Unique SKUs used
- Data freshness
- Usage by product category
- Cost by cloud provider
- Custom tag allocation

### Alerting Metrics
- Day-over-day spend changes
- Contract pace vs. time elapsed
- Weekend/off-hours usage
- New workspace creation
- Anomalous spending patterns

## Integration Points

### Data Sources
- **System Tables**: Real-time usage and billing data
- **Salesforce**: Customer and contract information
- **Custom Tags**: Project/team/environment labels
- **Metadata**: Organizational structure

### Outputs
- **Lakeview Dashboards**: Interactive visualizations
- **Email Alerts**: Automated notifications
- **Scheduled Reports**: Weekly/monthly summaries
- **API Access**: Integration with other tools

## Maintenance Requirements

### Daily
- Check data freshness (5 minutes)
- Review yesterday's spend (5 minutes)
- Check for anomalies (10 minutes)

### Weekly
- Update contract information (15 minutes)
- Review top consumers (15 minutes)
- Refresh dashboard data (automated)

### Monthly
- Contract pace review (30 minutes)
- Archive old data (15 minutes)
- Update account metadata (30 minutes)
- Performance optimization (30 minutes)

## Customization Options

### Add Custom Dimensions
- Cost centers
- Projects
- Teams
- Environments
- Applications

### Add Custom Metrics
- Cost per user
- Cost per transaction
- Efficiency metrics
- Resource utilization

### Add Custom Alerts
- Budget thresholds
- Usage quotas
- Cost anomalies
- Resource waste

## Prerequisites

### Required
- Databricks workspace (any tier)
- System tables enabled
- SQL warehouse
- Python 3.8+
- Databricks SDK

### Permissions Needed
- Read access to system.billing.*
- Create database/table permissions
- Workflow creation (for scheduled jobs)
- Dashboard creation (for Lakeview)

### Optional
- Salesforce integration
- Email/Slack for alerts
- Git for version control
- CI/CD pipeline

## Success Metrics

After implementation, you should have:

✅ **Visibility**
- Real-time cost tracking
- Contract consumption monitoring
- Usage trends and patterns
- Anomaly detection

✅ **Control**
- Budget alerts
- Contract pace monitoring
- Workspace-level cost allocation
- Tag-based chargeback

✅ **Optimization**
- Identify cost reduction opportunities
- Unused resource detection
- Right-sizing recommendations
- Efficiency improvements

✅ **Governance**
- Cost center accountability
- Contract compliance
- Usage policies
- Audit trail

## Support and Resources

### Documentation
- README.md - Full setup guide
- QUICK_REFERENCE.md - Query examples
- OPERATIONS_GUIDE.md - Daily operations

### Code Examples
- account_monitor_queries.sql - All queries
- account_monitor_notebook.py - Analysis notebook
- setup_account_monitor.py - Setup automation

### Configuration
- lakeview_dashboard_config.json - Dashboard template

### Getting Help
1. Check troubleshooting sections in guides
2. Review Databricks system tables documentation
3. Contact your Databricks account team

## Future Enhancements

### Planned Features
- Forecast modeling with ML
- Automated cost optimization recommendations
- Integration with cloud billing (AWS Cost Explorer, Azure Cost Management)
- Multi-account consolidation
- Advanced anomaly detection with ML

### Integration Opportunities
- Jira for cost tracking tickets
- Slack for real-time alerts
- PagerDuty for critical alerts
- ServiceNow for cost governance
- Confluence for documentation

## License and Usage

This solution is provided for internal use by Databricks customers and field engineers. Feel free to customize and extend based on your organization's needs.

## Version History

- **v1.0** (2026-01-27): Initial release
  - Core SQL queries
  - Python notebook
  - Setup automation
  - Dashboard configuration
  - Complete documentation

## Credits

Created by Databricks Field Engineering to help customers track and optimize their Databricks usage and costs using system tables.

---

**Quick Start**: Run `python setup_account_monitor.py` to begin!
