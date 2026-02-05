# DAB Deployment Update - Sync Script Deprecated

## ✅ Changes Made

The project has been updated to use **Databricks Asset Bundle (DAB)** exclusively for deployments. The `sync.sh` script has been **deprecated** to avoid confusion from having files in multiple locations.

## 🗂️ New Project Structure

```
databricks_conso_reports/
├── databricks.yml              # Main DAB configuration
├── lakeview_dashboard_config.json
├── notebooks/                  # Notebook files (.py, .sql)
│   ├── account_monitor_notebook.py
│   ├── post_deployment_validation.py
│   ├── verify_contract_burndown.sql
│   └── lakeview_dashboard_queries.sql
├── docs/                       # Documentation files (.md)
│   ├── README.md
│   ├── START_HERE.md
│   ├── CREATE_LAKEVIEW_DASHBOARD.md
│   ├── DASHBOARD_CONFIG_UPDATED.md
│   ├── OPTION2_COMPLETE.md
│   └── ... (all other docs)
├── sql/                        # SQL task files for jobs
│   ├── setup_schema.sql
│   ├── refresh_dashboard_data.sql
│   ├── refresh_contract_burndown.sql
│   └── ... (all other SQL tasks)
└── resources/                  # DAB resource definitions
    └── jobs.yml
```

## 📍 Workspace Deployment Location

All files are now deployed to:
```
/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/
```

### Directory Structure in Workspace:
```
/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/
├── files/                      # Synced files from DAB
│   ├── notebooks/              # All notebooks
│   ├── docs/                   # All documentation
│   ├── sql/                    # All SQL task files
│   └── lakeview_dashboard_config.json
├── artifacts/                  # Deployed job artifacts
└── state/                      # DAB deployment state
```

## 🚀 How to Deploy

### Deploy Everything
```bash
databricks bundle deploy --target dev
```

### Validate Before Deploying
```bash
databricks bundle validate
```

### Deploy and Run Setup Job
```bash
databricks bundle deploy --target dev
databricks bundle run account_monitor_setup --target dev
```

### Deploy to Production
```bash
databricks bundle deploy --target prod
```

## 📝 Key Dashboard Files Location

After deployment, find your dashboard files at:

1. **Dashboard Configuration**:
   ```
   /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/lakeview_dashboard_config.json
   ```

2. **Dashboard Queries Notebook**:
   ```
   /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/notebooks/lakeview_dashboard_queries
   ```

3. **Dashboard Creation Guide**:
   ```
   /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/docs/CREATE_LAKEVIEW_DASHBOARD
   ```

4. **Configuration Documentation**:
   ```
   /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/docs/DASHBOARD_CONFIG_UPDATED
   ```

5. **Option 2 Summary**:
   ```
   /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/docs/OPTION2_COMPLETE
   ```

## ⚙️ What Changed in databricks.yml

### Updated Workspace Paths
```yaml
targets:
  dev:
    workspace:
      root_path: /Workspace/Users/${workspace.current_user.userName}/account_monitor
```

### Updated Sync Configuration
```yaml
sync:
  include:
    - "notebooks/**"
    - "docs/**"
    - "sql/**"
    - "*.json"
    - "*.yml"
  exclude:
    - sync.sh
    - sync_to_workspace.py
```

## 🗑️ Deprecated Files

- **sync.sh** - Moved to `sync.sh.DEPRECATED` with error message
- **sync_to_workspace.py** - No longer used

## ✨ Benefits of Using DAB Only

1. **Single Source of Truth**: All deployments go through DAB
2. **No Confusion**: Files appear in one consistent location
3. **Version Control**: DAB tracks deployment state
4. **Job Management**: Jobs are deployed and managed automatically
5. **Environment Support**: Easy dev/prod separation

## 🔄 Continuous Updates

Any changes you make locally will be synced on next deployment:

```bash
# Make changes locally
nano notebooks/lakeview_dashboard_queries.sql

# Deploy to sync changes
databricks bundle deploy --target dev
```

## 📊 Dashboard Creation Workflow

1. **Deploy the bundle**:
   ```bash
   databricks bundle deploy --target dev
   ```

2. **Navigate to the files** in Databricks UI:
   - Go to: `/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files/`

3. **Open the queries notebook**:
   - `notebooks/lakeview_dashboard_queries`

4. **Use the queries** to create your Lakeview dashboard manually through the UI

5. **Reference the configuration**:
   - `lakeview_dashboard_config.json` contains all specifications
   - `docs/CREATE_LAKEVIEW_DASHBOARD` has step-by-step instructions
   - `docs/OPTION2_COMPLETE` shows what's included

## 🎯 Next Steps

1. ✅ DAB configuration updated
2. ✅ Project structure reorganized
3. ✅ Files deployed to workspace
4. ✅ Sync script deprecated

**You're ready to use DAB exclusively!**

To create your dashboard:
1. Navigate to the workspace location shown above
2. Open `files/notebooks/lakeview_dashboard_queries`
3. Use the queries to build your Lakeview dashboard
4. Reference `files/docs/CREATE_LAKEVIEW_DASHBOARD` for guidance

## 📖 Additional Resources

- **DAB Commands**: `docs/DAB_QUICK_COMMANDS.md`
- **DAB Guide**: `docs/DAB_README.md`
- **Dashboard Guide**: `docs/CREATE_LAKEVIEW_DASHBOARD.md`
- **Schema Reference**: `docs/SCHEMA_REFERENCE.md`

---

**Updated**: 2026-01-27
**Change**: Migrated from sync.sh to DAB-only deployment
