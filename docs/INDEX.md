# Databricks Account Monitor - Documentation Index

## 🚀 Start Here

New to this project? Start with these files in order:

1. **[GETTING_STARTED.md](GETTING_STARTED.md)** (7.5 KB)
   - 15-minute quick start guide
   - Step-by-step setup instructions
   - Basic queries to test your setup
   - First dashboard creation

2. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** (10 KB)
   - High-level project overview
   - Architecture and components
   - Key features and metrics
   - Success criteria

3. **[README.md](README.md)** (9.4 KB)
   - Comprehensive documentation
   - Detailed setup instructions
   - Data source descriptions
   - Troubleshooting guide

## 📚 Reference Documentation

### Query References
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** (11 KB)
  - Ready-to-use SQL queries
  - Common patterns and templates
  - Cost allocation examples
  - Anomaly detection
  - Forecasting queries

### Operations
- **[OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)** (16 KB)
  - Daily operations checklist
  - Weekly and monthly reviews
  - Maintenance procedures
  - Alerting setup
  - Performance optimization
  - Backup and recovery

## 🛠️ Implementation Files

### Code Files
1. **[account_monitor_queries.sql](account_monitor_queries.sql)** (8.4 KB)
   - 11 core SQL queries
   - Account overview
   - Usage analysis
   - Contract tracking
   - Cost breakdown

2. **[account_monitor_notebook.py](account_monitor_notebook.py)** (17 KB)
   - Complete Python/Databricks notebook
   - 15 analysis sections
   - Visualizations and charts
   - Data export functionality

3. **[setup_account_monitor.py](setup_account_monitor.py)** (14 KB)
   - Automated setup script
   - Table creation
   - Sample data insertion
   - Job scheduling

### Configuration
4. **[lakeview_dashboard_config.json](lakeview_dashboard_config.json)** (8.4 KB)
   - Dashboard configuration template
   - 10 dataset definitions
   - Visualization specifications
   - Filter configuration

## 📖 How to Use This Documentation

### By Role

**Data Engineer / Administrator**
1. Start: [GETTING_STARTED.md](GETTING_STARTED.md)
2. Setup: [setup_account_monitor.py](setup_account_monitor.py)
3. Operations: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)
4. Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Business Analyst / Finance**
1. Start: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. Learn: [README.md](README.md)
3. Query: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
4. Dashboard: [lakeview_dashboard_config.json](lakeview_dashboard_config.json)

**DevOps / SRE**
1. Operations: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)
2. Queries: [account_monitor_queries.sql](account_monitor_queries.sql)
3. Automation: [setup_account_monitor.py](setup_account_monitor.py)
4. Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Executive / Manager**
1. Overview: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. Features: [README.md](README.md) (Features section)
3. Dashboard: [lakeview_dashboard_config.json](lakeview_dashboard_config.json)

### By Task

**Setting Up for the First Time**
1. [GETTING_STARTED.md](GETTING_STARTED.md) - Quick setup
2. [setup_account_monitor.py](setup_account_monitor.py) - Run setup script
3. [account_monitor_notebook.py](account_monitor_notebook.py) - Upload notebook
4. [README.md](README.md) - Detailed configuration

**Daily Operations**
1. [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) - Daily checklist
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common queries
3. [account_monitor_queries.sql](account_monitor_queries.sql) - SQL queries

**Creating Dashboards**
1. [lakeview_dashboard_config.json](lakeview_dashboard_config.json) - Configuration
2. [account_monitor_queries.sql](account_monitor_queries.sql) - Query definitions
3. [README.md](README.md) - Dashboard components section

**Troubleshooting Issues**
1. [README.md](README.md) - Troubleshooting section
2. [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) - Common issues
3. [GETTING_STARTED.md](GETTING_STARTED.md) - Common issues

**Cost Analysis**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Analysis queries
2. [account_monitor_queries.sql](account_monitor_queries.sql) - Core queries
3. [account_monitor_notebook.py](account_monitor_notebook.py) - Full analysis

**Contract Management**
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Contract queries
2. [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) - Contract reviews
3. [account_monitor_notebook.py](account_monitor_notebook.py) - Contract analysis

## 🔍 Quick Find

### Key Concepts

- **System Tables**: [README.md](README.md#data-sources), [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md#data-architecture)
- **Custom Tables**: [README.md](README.md#custom-tables-you-create), [setup_account_monitor.py](setup_account_monitor.py)
- **Contracts**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#contract-management), [account_monitor_queries.sql](account_monitor_queries.sql)
- **Dashboards**: [lakeview_dashboard_config.json](lakeview_dashboard_config.json), [README.md](README.md#dashboard-components)

### Common Queries

- **Today's Spend**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#todays-spending)
- **Monthly Trends**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#monthly-spend-trend)
- **Top Workspaces**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#find-expensive-workspaces)
- **Contract Status**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#check-contract-status)
- **Anomalies**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md#anomaly-detection)

### Setup Tasks

- **Prerequisites**: [GETTING_STARTED.md](GETTING_STARTED.md#prerequisites-check-2-minutes)
- **Automated Setup**: [setup_account_monitor.py](setup_account_monitor.py)
- **Manual Setup**: [GETTING_STARTED.md](GETTING_STARTED.md#option-b-manual-setup)
- **Sample Data**: [setup_account_monitor.py](setup_account_monitor.py) (insert_sample_data function)

### Operations

- **Daily Tasks**: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md#daily-operations)
- **Weekly Tasks**: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md#weekly-review)
- **Monthly Tasks**: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md#monthly-review)
- **Alerts**: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md#alerting)
- **Maintenance**: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md#maintenance-tasks)

## 📊 Dashboard Components

### Visualizations Included

1. **Account Overview Page**
   - Counter: Top SKU Count
   - Counter: Top Workspace Count
   - Table: Latest Data Dates
   - Table: Total Spend in Timeframe
   - Table: Contracts
   - Line Chart: Contract Burndown

2. **Usage Analytics Page**
   - Bar Chart: Monthly Cost Trend
   - Table: Top Consuming Workspaces
   - Table: Top Consuming SKUs
   - Stacked Area Chart: Cost by Product Category

See [lakeview_dashboard_config.json](lakeview_dashboard_config.json) for full configuration.

## 🎯 Learning Paths

### Path 1: Quick Start (15 minutes)
1. [GETTING_STARTED.md](GETTING_STARTED.md)
2. Run [setup_account_monitor.py](setup_account_monitor.py)
3. Test queries from [GETTING_STARTED.md](GETTING_STARTED.md#step-2-test-basic-queries-3-minutes)

### Path 2: Comprehensive Setup (2-3 hours)
1. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. [README.md](README.md)
3. [setup_account_monitor.py](setup_account_monitor.py)
4. [account_monitor_notebook.py](account_monitor_notebook.py)
5. [lakeview_dashboard_config.json](lakeview_dashboard_config.json)
6. [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)

### Path 3: Advanced Operations (Ongoing)
1. [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. [account_monitor_queries.sql](account_monitor_queries.sql)
4. Custom development based on needs

## 📦 File Sizes

| File | Size | Purpose |
|------|------|---------|
| GETTING_STARTED.md | 7.5 KB | Quick start guide |
| PROJECT_SUMMARY.md | 10 KB | Project overview |
| README.md | 9.4 KB | Main documentation |
| QUICK_REFERENCE.md | 11 KB | Query reference |
| OPERATIONS_GUIDE.md | 16 KB | Operations manual |
| account_monitor_queries.sql | 8.4 KB | SQL queries |
| account_monitor_notebook.py | 17 KB | Analysis notebook |
| setup_account_monitor.py | 14 KB | Setup automation |
| lakeview_dashboard_config.json | 8.4 KB | Dashboard config |
| **Total** | **~120 KB** | Complete solution |

## 🆘 Need Help?

### Can't Find What You're Looking For?

1. **Setup Issues**: Check [GETTING_STARTED.md](GETTING_STARTED.md#common-issues)
2. **Query Help**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. **Operation Questions**: Read [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)
4. **Understanding the System**: Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

### Still Stuck?

1. Check troubleshooting sections in [README.md](README.md#troubleshooting)
2. Review [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md#troubleshooting)
3. Contact your Databricks account team

## 🔄 Version Information

- **Version**: 1.0
- **Last Updated**: 2026-01-27
- **Compatible With**: Databricks Runtime 13.0+
- **System Tables**: billing.usage, billing.list_prices

## 📝 Notes

- All documentation uses markdown format
- Code examples are provided in SQL and Python
- Sample data included for testing
- Configuration templates ready to use

---

**Need to get started quickly?** → [GETTING_STARTED.md](GETTING_STARTED.md)

**Want the full picture?** → [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

**Ready to dive deep?** → [README.md](README.md)
