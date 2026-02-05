# Deprecated Files

This directory contains legacy scripts and files that are no longer actively used but kept for reference.

## Contents

### Old Setup Scripts
- `setup_account_monitor.py` - Original Python setup script
- `setup_account_monitor_UC.py` - Unity Catalog version of setup script
- `sync_to_workspace.py` - Workspace sync utility
- `sync.sh.DEPRECATED` - Shell sync script

### Old Query Files
- `account_monitor_queries.sql` - Original SQL queries
- `account_monitor_queries_CORRECTED.sql` - Corrected version

### Dashboard Scripts
- `create_lakeview_dashboard.py` - Lakeview dashboard creation script
- `translate_dashboard.py` - Dashboard translation utility
- `test_dashboard_queries.py` - Query testing script

### Configuration Files
- `api_payload.json` - API payload template
- `dashboard_payload.json` - Dashboard configuration
- `lakeview_dashboard_config.json` - Lakeview config

### Utilities
- `update_config.py` - Configuration update script

### Directories
- `dashboard/` - Old dashboard files
- `scripts/` - Utility scripts

## Note

These files have been superseded by:
- Databricks Asset Bundles (DAB) for deployment
- SQL files in `/sql` directory
- Notebooks in `/notebooks` directory
- Job definitions in `/resources/jobs.yml`

Do not delete - kept for historical reference and potential rollback scenarios.
