# Export & Import Lakeview Dashboards (.lvdash.json)

## Quick Reference

Once you've built your dashboard in the UI, you can export it as a `.lvdash.json` file for:
- ✅ Version control (Git)
- ✅ Backup and recovery
- ✅ Deployment across workspaces
- ✅ Programmatic management

## Export Your Dashboard

### Method 1: UI Export (Easiest)

1. **Open your dashboard** in Databricks
2. **Click ⋮ menu** (three dots) in top-right corner
3. **Select "Export"**
4. File downloads to your browser: `Dashboard_Name.lvdash.json`

**Time:** 10 seconds

### Method 2: CLI Export

```bash
# Export dashboard using databricks CLI
databricks workspace export \
  "/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/dashboard_name.lvdash.json" \
  --format AUTO \
  --profile LPT_FREE_EDITION \
  > account_monitor_dashboard.lvdash.json
```

**Time:** 30 seconds

### Method 3: API Export

```bash
# Get the dashboard content via API
curl -X GET \
  "https://dbc-cbb9ade6-873a.cloud.databricks.com/api/2.0/workspace/export" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "path": "/Workspace/Users/laurent.prat@mailwatcher.net/dashboard_name.lvdash.json",
    "format": "AUTO",
    "direct_download": true
  }' > dashboard.lvdash.json
```

**Time:** 1 minute

## Import Dashboard

### Method 1: UI Import (Easiest)

1. **Go to Databricks** → **Dashboards**
2. **Click "Create"** → **"Import Dashboard"**
3. **Upload** your `.lvdash.json` file
4. **Choose destination** path
5. **Click "Import"**

**Time:** 30 seconds

### Method 2: CLI Import

```bash
# Import dashboard using databricks CLI
databricks workspace import \
  "/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/imported_dashboard.lvdash.json" \
  --file account_monitor_dashboard.lvdash.json \
  --format AUTO \
  --overwrite \
  --profile LPT_FREE_EDITION
```

**CRITICAL:** Path must end with `.lvdash.json`

**Time:** 30 seconds

### Method 3: API Import

```bash
# Base64 encode the file first
CONTENT=$(cat dashboard.lvdash.json | base64)

# Import via API
curl -X POST \
  "https://dbc-cbb9ade6-873a.cloud.databricks.com/api/2.0/workspace/import" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d "{
    \"path\": \"/Workspace/Users/laurent.prat@mailwatcher.net/dashboard.lvdash.json\",
    \"format\": \"AUTO\",
    \"content\": \"${CONTENT}\",
    \"overwrite\": false
  }"
```

**Time:** 1-2 minutes

## Workflow Examples

### Scenario 1: Version Control in Git

```bash
# 1. Build dashboard in UI
# 2. Export it
databricks workspace export \
  "/path/to/dashboard.lvdash.json" \
  --format AUTO \
  --profile LPT_FREE_EDITION \
  > dashboards/account_monitor.lvdash.json

# 3. Commit to Git
git add dashboards/account_monitor.lvdash.json
git commit -m "Add account monitor dashboard"
git push

# 4. Deploy to another workspace
git pull
databricks workspace import \
  "/Workspace/Users/user@example.com/account_monitor.lvdash.json" \
  --file dashboards/account_monitor.lvdash.json \
  --format AUTO \
  --profile PROD_WORKSPACE
```

### Scenario 2: Deploy Across Environments

```bash
# Development
databricks workspace import \
  "/Workspace/Shared/dashboards/account_monitor.lvdash.json" \
  --file account_monitor.lvdash.json \
  --format AUTO \
  --profile DEV_PROFILE

# Staging
databricks workspace import \
  "/Workspace/Shared/dashboards/account_monitor.lvdash.json" \
  --file account_monitor.lvdash.json \
  --format AUTO \
  --profile STAGING_PROFILE

# Production
databricks workspace import \
  "/Workspace/Shared/dashboards/account_monitor.lvdash.json" \
  --file account_monitor.lvdash.json \
  --format AUTO \
  --profile PROD_PROFILE
```

### Scenario 3: Backup Before Updates

```bash
# Backup current version
databricks workspace export \
  "/path/to/dashboard.lvdash.json" \
  --format AUTO \
  --profile LPT_FREE_EDITION \
  > backups/dashboard_$(date +%Y%m%d_%H%M%S).lvdash.json

# Make changes in UI
# ...

# Export new version
databricks workspace export \
  "/path/to/dashboard.lvdash.json" \
  --format AUTO \
  --profile LPT_FREE_EDITION \
  > dashboards/dashboard_v2.lvdash.json

# If needed, restore backup
databricks workspace import \
  "/path/to/dashboard.lvdash.json" \
  --file backups/dashboard_20260127_153000.lvdash.json \
  --format AUTO \
  --overwrite \
  --profile LPT_FREE_EDITION
```

## Best Practices

### File Naming
```
✅ account_monitor_ibm_style.lvdash.json
✅ contract_burndown_dashboard.lvdash.json
✅ account_monitor_v2.lvdash.json

❌ dashboard.json
❌ my_dashboard.txt
❌ lakeview_config.json
```

### Directory Structure
```
project/
├── dashboards/              # Deployable .lvdash.json files
│   ├── account_monitor.lvdash.json
│   └── contract_burndown.lvdash.json
├── blueprints/              # Documentation/reference JSON
│   ├── lakeview_dashboard_config.json
│   └── ibm_style_config.json
├── backups/                 # Timestamped backups
│   └── account_monitor_20260127.lvdash.json
└── docs/                    # Build guides
    └── CREATE_DASHBOARD.md
```

### Version Control
```bash
# .gitignore - exclude backups
backups/*.lvdash.json

# Track only current versions
git add dashboards/*.lvdash.json
git commit -m "Update dashboard: add contract burndown chart"
```

### Deployment Script
```bash
#!/bin/bash
# deploy_dashboard.sh

DASHBOARD_FILE=$1
TARGET_PROFILE=${2:-LPT_FREE_EDITION}
DASHBOARD_NAME=$(basename "$DASHBOARD_FILE" .lvdash.json)

echo "Deploying ${DASHBOARD_NAME} to ${TARGET_PROFILE}..."

databricks workspace import \
  "/Workspace/Shared/dashboards/${DASHBOARD_NAME}.lvdash.json" \
  --file "$DASHBOARD_FILE" \
  --format AUTO \
  --overwrite \
  --profile "$TARGET_PROFILE"

echo "✅ Dashboard deployed successfully!"
echo "📍 Location: /Workspace/Shared/dashboards/${DASHBOARD_NAME}"
```

Usage:
```bash
./deploy_dashboard.sh dashboards/account_monitor.lvdash.json DEV_PROFILE
./deploy_dashboard.sh dashboards/account_monitor.lvdash.json PROD_PROFILE
```

## Troubleshooting

### Error: "Path must end with .lvdash.json"
```bash
# ❌ Wrong
databricks workspace import \
  "/path/to/dashboard" \
  --file dashboard.lvdash.json

# ✅ Correct
databricks workspace import \
  "/path/to/dashboard.lvdash.json" \
  --file dashboard.lvdash.json
```

### Error: "Invalid format"
```bash
# Ensure you're using format AUTO
databricks workspace import \
  "/path/to/dashboard.lvdash.json" \
  --file dashboard.lvdash.json \
  --format AUTO  # ← Must be AUTO
```

### Error: "Dashboard already exists"
```bash
# Add --overwrite flag
databricks workspace import \
  "/path/to/dashboard.lvdash.json" \
  --file dashboard.lvdash.json \
  --format AUTO \
  --overwrite  # ← Add this
```

### Export returns empty file
```bash
# Check if path is correct
databricks workspace list "/path/to/" --profile LPT_FREE_EDITION

# Verify dashboard exists
databricks workspace get-status "/path/to/dashboard.lvdash.json" --profile LPT_FREE_EDITION
```

## After Import

### Publish Dashboard
Once imported, publish it to make it available:

```bash
# Get dashboard ID
DASHBOARD_ID=$(databricks workspace get-status \
  "/path/to/dashboard.lvdash.json" \
  --profile LPT_FREE_EDITION \
  --output json | jq -r '.object_id')

# Publish via API
curl -X POST \
  "https://dbc-cbb9ade6-873a.cloud.databricks.com/api/2.0/lakeview/dashboards/${DASHBOARD_ID}/published" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "embed_credentials": true
  }'
```

### Set Permissions
```bash
# Via API (example)
curl -X PATCH \
  "https://dbc-cbb9ade6-873a.cloud.databricks.com/api/2.0/permissions/dashboards/${DASHBOARD_ID}" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "access_control_list": [
      {
        "user_name": "user@example.com",
        "permission_level": "CAN_VIEW"
      },
      {
        "group_name": "admins",
        "permission_level": "CAN_MANAGE"
      }
    ]
  }'
```

## Integration with DAB

You can integrate dashboard deployment with Databricks Asset Bundles:

```yaml
# databricks.yml
artifacts:
  dashboards:
    account_monitor:
      type: dashboard
      path: dashboards/account_monitor.lvdash.json
      target_path: /Workspace/Shared/dashboards/account_monitor.lvdash.json
```

Then deploy with:
```bash
databricks bundle deploy --target dev
```

## Next Steps for Your Project

1. **Build dashboards** using your blueprint guides:
   - IBM-style dashboard
   - Option 2 dashboard

2. **Export each dashboard**:
   ```bash
   # After building in UI
   databricks workspace export \
     "/path/to/ibm_dashboard.lvdash.json" \
     --format AUTO \
     --profile LPT_FREE_EDITION \
     > dashboards/account_monitor_ibm.lvdash.json
   ```

3. **Store in Git**:
   ```bash
   git add dashboards/*.lvdash.json
   git commit -m "Add exportable dashboard files"
   git push
   ```

4. **Deploy to other workspaces** as needed

## Summary

- ✅ **Export** - Get `.lvdash.json` after building in UI
- ✅ **Store** - Keep in Git for version control
- ✅ **Import** - Deploy to other workspaces programmatically
- ✅ **Automate** - Use CLI/API for deployment pipelines

**Key Rule:** Path must always end with `.lvdash.json` for import to work.

## Resources

- [Workspace API Documentation](https://docs.databricks.com/en/dashboards/lakeview-api-tutorial.html)
- [Dashboard CRUD API](https://docs.databricks.com/en/dashboards/tutorials/dashboard-crud-api)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)
