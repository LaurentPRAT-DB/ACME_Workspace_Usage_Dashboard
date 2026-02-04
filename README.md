# Databricks Account Monitor

**Track consumption, costs, and contract burndown across your Databricks workspaces**

[![Databricks](https://img.shields.io/badge/Databricks-Asset_Bundle-FF3621?logo=databricks)](https://databricks.com)
[![Version](https://img.shields.io/badge/Version-1.6.1-green)](CHANGELOG.md)

---

## 📚 Documentation

**👉 [Complete User Guide](docs/user-guide/USER_GUIDE.md)** - Start here for comprehensive instructions

### Quick Links

- **[Installation & Setup](docs/user-guide/USER_GUIDE.md#installation--setup)** - Deploy with Databricks Asset Bundles
- **[Understanding Tables](docs/user-guide/USER_GUIDE.md#understanding-the-data-model)** - Data model and schemas
- **[Managing Contracts](docs/user-guide/USER_GUIDE.md#managing-contracts-crud-operations)** - CRUD operations guide
- **[Data Refresh Jobs](docs/user-guide/USER_GUIDE.md#data-refresh-jobs)** - Automated job schedules
- **[Dashboard Guide](docs/user-guide/USER_GUIDE.md#dashboard--burndown-charts)** - Visualizations and burndown charts
- **[Troubleshooting](docs/user-guide/USER_GUIDE.md#troubleshooting)** - Common issues and solutions

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Databricks workspace with Unity Catalog
- Databricks CLI installed
- Access to system.billing tables

### Installation

```bash
# 1. Authenticate
databricks auth login https://your-workspace.cloud.databricks.com --profile YOUR_PROFILE

# 2. Configure
# Edit databricks.yml and set your profile and warehouse_id

# 3. Deploy
databricks bundle deploy --profile YOUR_PROFILE

# 4. Run Setup
databricks bundle run account_monitor_setup --profile YOUR_PROFILE
```

**Done!** Your tables are created and sample data is loaded.

### Next Steps

1. **Update Your Data** - Open the Contract Management CRUD notebook and add your actual contracts
2. **View Dashboard** - Open the Account Monitor notebook to see your cost analysis
3. **Schedule Jobs** - Jobs are already deployed and scheduled (daily, weekly, monthly)

---

## 🎯 What This Solution Does

### Cost Tracking
- Monitor Databricks spending across all workspaces
- Track costs by product category (compute, SQL, DLT, etc.)
- Identify top consumers and cost anomalies

### Contract Management
- Store and track contract details (value, dates, cloud provider)
- Calculate contract burndown and consumption rates
- Project contract exhaustion dates
- Get alerts for overspending

### Organizational Reporting
- Organize accounts by business units (4 levels)
- Track team assignments (AE, SA, DSA)
- Generate summaries by region, team, or account

### Automation
- **Daily** - Refresh dashboard data from system tables
- **Weekly** - Analyze contracts and identify anomalies
- **Monthly** - Generate summaries and archive old data

---

## 📊 Key Features

### Interactive Notebooks

**Account Monitor Dashboard** - Main analytics notebook
- Cost trends over time
- Contract burndown visualization
- Top consumers analysis
- Product category breakdown

**Contract Management CRUD** - Manage your data
- Add/update/delete contracts
- Manage account metadata
- Data validation tools
- Bulk operations

**Post Deployment Validation** - Verify your setup
- Check table creation
- Validate data integrity
- Test job configurations

### Automated Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| Setup | On-demand | Initialize schema and tables |
| Daily Refresh | 2 AM UTC | Update dashboard data |
| Weekly Review | Mon 8 AM | Contract analysis |
| Monthly Summary | 1st @ 6 AM | Generate reports |

### Data Tables

**Contracts** - Track your Databricks contracts
- Contract value, dates, status
- Cloud provider and commitment type
- Notes and metadata

**Account Metadata** - Organizational structure
- Business unit hierarchy (4 levels)
- Team assignments (AE, SA, DSA)
- Regional and industry tags

**Dashboard Data** - Pre-aggregated analytics
- Usage and cost by day/workspace/SKU
- Product category breakdowns
- Optimized for fast queries

---

## 🏗️ Architecture

```
System Tables (Databricks)
    ↓
Daily Refresh Job
    ↓
Dashboard Data Tables (Unity Catalog)
    ↓
Notebooks & Lakeview Dashboards
    ↓
Business Insights
```

**Data Flow:**
1. System tables (`system.billing.usage`, `system.billing.list_prices`) contain raw data
2. Daily job aggregates and enriches data
3. Tables store processed data with business context
4. Notebooks and dashboards provide visualization

---

## 📁 Repository Structure

```
databricks_conso_reports/
├── README.md                          # This file
├── databricks.yml                     # DAB configuration
├── docs/
│   ├── user-guide/
│   │   └── USER_GUIDE.md             # 📚 Main documentation
│   └── archive/                       # Old summaries
├── notebooks/
│   ├── account_monitor_notebook.py   # Main dashboard
│   ├── contract_management_crud.py   # Data management
│   └── post_deployment_validation.py # Setup validation
├── sql/
│   ├── setup_schema.sql              # Table creation
│   ├── insert_sample_data.sql        # Sample data
│   ├── refresh_dashboard_data.sql    # Daily refresh
│   └── refresh_contract_burndown.sql # Burndown calc
└── resources/
    └── jobs.yml                       # Job definitions
```

---

## 🔧 Common Tasks

### Add a New Contract

```sql
INSERT INTO main.account_monitoring_dev.contracts
VALUES (
  'CONTRACT_2026_001',
  'your-account-id',
  'AWS',
  '2026-01-01',
  '2027-01-01',
  10000.00,
  'USD',
  'SPEND',
  'ACTIVE',
  'Annual contract',
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
```

### View Current Spending

```sql
SELECT
  contract_id,
  total_value,
  SUM(actual_cost) as spent,
  (SUM(actual_cost) / total_value * 100) as percent_used
FROM main.account_monitoring_dev.contracts c
JOIN main.account_monitoring_dev.dashboard_data d
  ON c.account_id = d.account_id
WHERE c.status = 'ACTIVE'
GROUP BY contract_id, total_value;
```

### Refresh Dashboard Data

```bash
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE
```

---

## 🆘 Support & Troubleshooting

### Common Issues

**"Table not found"**
→ Run setup job: `databricks bundle run account_monitor_setup`

**"No data in dashboard"**
→ Check system tables have data, then run daily refresh job

**"Warehouse not found"**
→ Update `warehouse_id` in `databricks.yml`

**Detailed troubleshooting:** See [User Guide - Troubleshooting](docs/user-guide/USER_GUIDE.md#troubleshooting)

---

## 📝 Version History

- **1.6.1** (2026-02-04)
  - Removed salesforce_id field (breaking change)
  - Added notes column to contracts table
  - Fixed MERGE statement wildcard issues
  - Clean schema for fresh deployments

- **1.5.x** - Initial stable release

---

## 🤝 Contributing

This solution is designed for use by power users and administrators. For technical questions or feature requests, consult with your Databricks team.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🎓 Learning Resources

- [Databricks System Tables](https://docs.databricks.com/en/admin/system-tables/index.html)
- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html)
- [Unity Catalog](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Lakeview Dashboards](https://docs.databricks.com/en/dashboards/index.html)

---

**Questions?** Check the [Complete User Guide](docs/user-guide/USER_GUIDE.md) for detailed instructions on all features.
