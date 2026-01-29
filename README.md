# Databricks Account Monitor

**Track consumption, costs, and contract burndown across your Databricks workspaces**

[![Databricks](https://img.shields.io/badge/Databricks-Asset_Bundle-FF3621?logo=databricks)](https://databricks.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard.git
cd ACME_Workspace_Usage_Dashboard

# 2. Deploy to Databricks
databricks bundle deploy -t dev

# 3. Run validation
# Open notebooks/post_deployment_validation.py in your workspace

# 4. View your data
# Open notebooks/account_monitor_notebook.py in your workspace
```

**See:** [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions.

---

## 📊 Features

- **📈 Contract Burndown Tracking** - Monitor spending against contract commitments
- **💰 Cost Analysis** - Break down costs by workspace, SKU, and product category
- **🏢 Multi-Account Support** - Track multiple accounts and business units
- **📅 Automated Refresh** - Scheduled jobs for daily/weekly/monthly updates
- **🎨 Lakeview Dashboards** - Pre-built queries for visualization
- **✅ Validation Suite** - Automated tests to verify deployment

---

## 🛠️ Development Workflow

### Fixing Notebooks

**Quick Fix (Recommended):**
```bash
# Automated version bump, commit, and deploy
./scripts/notebook_fix.sh notebooks/account_monitor_notebook.py "Fix SQL parameter issue"
```

**Manual Fix:**
```bash
# 1. Edit the notebook
# 2. Update version numbers (VERSION and BUILD)
# 3. Commit and push
git add notebooks/account_monitor_notebook.py
git commit -m "Fix [issue]"
git push

# 4. Deploy
databricks bundle deploy
```

**Resources:**
- **Quick Reference:** [NOTEBOOK_FIX_QUICKREF.md](NOTEBOOK_FIX_QUICKREF.md) - Common fixes and quick commands
- **Full Workflow:** [docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md](docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md) - Complete development workflow
- **Scripts:** [scripts/README.md](scripts/README.md) - Helper script documentation

---

## 📁 Project Structure

```
databricks_conso_reports/
├── databricks.yml                    # Asset bundle configuration
├── README.md                          # This file
├── NOTEBOOK_FIX_QUICKREF.md          # Quick reference for notebook fixes
├── GETTING_STARTED.md                 # Initial setup guide
│
├── notebooks/                         # Databricks notebooks
│   ├── account_monitor_notebook.py   # Main analytics notebook
│   ├── post_deployment_validation.py # Deployment validation tests
│   └── lakeview_dashboard_queries.sql # Dashboard queries
│
├── sql/                               # SQL scripts for jobs
│   ├── setup_schema.sql              # Schema and table creation
│   ├── refresh_dashboard_data.sql    # Daily data refresh
│   └── refresh_contract_burndown.sql # Contract burndown calculation
│
├── scripts/                           # Helper scripts
│   ├── notebook_fix.sh               # Automated notebook fix workflow
│   └── README.md                      # Scripts documentation
│
├── resources/                         # Bundle resources
│   └── jobs.yml                      # Job definitions
│
└── docs/                              # Documentation
    ├── SKILL_NOTEBOOK_FIX_WORKFLOW.md # Complete fix workflow
    ├── SCHEMA_REFERENCE.md            # System tables reference
    ├── QUICK_REFERENCE.md             # Query examples
    └── OPERATIONS_GUIDE.md            # Daily operations
```

---

## 🔧 Configuration

### Unity Catalog Tables

The project creates these tables in your catalog:

| Table | Purpose |
|-------|---------|
| `contracts` | Contract tracking (value, dates, status) |
| `account_metadata` | Customer information (AE, SA, business units) |
| `dashboard_data` | Pre-aggregated usage and cost data |
| `daily_summary` | Daily rollup for fast queries |
| `contract_burndown` | Contract consumption tracking |

### Scheduled Jobs

Four jobs are deployed:

| Job | Schedule | Purpose |
|-----|----------|---------|
| Setup | Manual | Create schema and tables |
| Daily Refresh | 2 AM UTC | Update dashboard data |
| Weekly Review | Mon 8 AM | Contract analysis and anomalies |
| Monthly Summary | 1st @ 6 AM | Monthly report and archival |

---

## 📊 Usage

### Running the Main Notebook

```python
# In Databricks workspace:
# 1. Open: /Users/{your-email}/account_monitor/files/notebooks/account_monitor_notebook.py
# 2. Attach to a cluster or warehouse
# 3. Run All

# The notebook includes:
# - Contract burndown chart
# - Cost analysis by workspace/SKU
# - Daily/weekly/monthly trends
# - Top consumers
```

### Creating Lakeview Dashboards

```sql
-- Use queries from: notebooks/lakeview_dashboard_queries.sql
-- In Lakeview:
-- 1. Create New Dashboard
-- 2. Add Visualization
-- 3. Copy query from lakeview_dashboard_queries.sql
-- 4. Configure chart type and axes
```

### Running Validation

```python
# In Databricks workspace:
# Open: /Users/{your-email}/account_monitor/files/notebooks/post_deployment_validation.py
# Run All

# Tests verify:
# - System tables access
# - Unity Catalog tables
# - Cost calculations
# - Jobs deployment
# - Data freshness
```

---

## 📚 Documentation

### Quick Access
- [NOTEBOOK_FIX_QUICKREF.md](NOTEBOOK_FIX_QUICKREF.md) - Quick reference for common fixes
- [GETTING_STARTED.md](GETTING_STARTED.md) - Initial setup guide

### Development
- [docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md](docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md) - Complete fix workflow
- [scripts/README.md](scripts/README.md) - Helper scripts documentation

### Operations
- [docs/OPERATIONS_GUIDE.md](docs/OPERATIONS_GUIDE.md) - Daily operations
- [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Query examples
- [docs/SCHEMA_REFERENCE.md](docs/SCHEMA_REFERENCE.md) - System tables reference

---

## 🐛 Troubleshooting

### Common Issues

**SQL Parameter Error:** `SQL query contains $ parameter`
```bash
# Fix: Replace $ with USD in CONCAT statements
./scripts/notebook_fix.sh notebooks/account_monitor_notebook.py "Fix SQL parameter markers"
```

**Decimal Type Error:** `TypeError: unsupported operand type(s) for *: 'decimal.Decimal'`
```python
# Fix: Convert Decimal to float
range=[0, float(contract_value) * 1.1]
```

**Jobs Not Found:** Test 11 in validation fails
```bash
# Verify jobs deployed
databricks bundle validate
databricks bundle deploy
```

**See:** [NOTEBOOK_FIX_QUICKREF.md](NOTEBOOK_FIX_QUICKREF.md) for more fixes.

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.5.4 | 2026-01-29 | Fixed SQL parameter markers in comments |
| 1.5.3 | 2026-01-29 | Fixed Decimal type conversions in Cell 9 |
| 1.5.2 | 2026-01-29 | Fixed SQL parameter syntax throughout |
| 1.5.1 | 2026-01-29 | Fixed Decimal to float conversion |
| 1.5.0 | 2026-01-29 | Horizontal commitment line in burndown chart |

**See:** [docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md](docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md) for complete history.

---

## 🤝 Contributing

### Making Changes

1. Create a feature branch
2. Make your changes
3. Use the helper script for notebooks:
   ```bash
   ./scripts/notebook_fix.sh notebooks/your_notebook.py "Description"
   ```
4. Deploy and test:
   ```bash
   databricks bundle deploy -t dev
   ```
5. Submit a pull request

### Versioning

- **Patch (x.x.+1):** Bug fixes, minor corrections
- **Minor (x.+1.0):** New features, significant changes
- **Major (+1.0.0):** Breaking changes, major refactors

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Support

- **Issues:** [GitHub Issues](https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard/issues)
- **Documentation:** See `docs/` folder
- **Quick Help:** [NOTEBOOK_FIX_QUICKREF.md](NOTEBOOK_FIX_QUICKREF.md)

---

## 🎯 Next Steps

After deployment:

1. ✅ **Run Validation:** `notebooks/post_deployment_validation.py`
2. 📝 **Update Metadata:** Add your account info to `account_metadata` table
3. 📊 **Add Contracts:** Insert your contracts into `contracts` table
4. 🔄 **Run Refresh Job:** Execute daily refresh to populate data
5. 📈 **Create Dashboard:** Use queries from `lakeview_dashboard_queries.sql`

---

**Quick Links:**
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup instructions
- [NOTEBOOK_FIX_QUICKREF.md](NOTEBOOK_FIX_QUICKREF.md) - Development quick reference
- [docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md](docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md) - Complete workflow
- [GitHub Repository](https://github.com/LaurentPRAT-DB/ACME_Workspace_Usage_Dashboard)

---

**Built with ❤️ for Databricks Field Engineering**
