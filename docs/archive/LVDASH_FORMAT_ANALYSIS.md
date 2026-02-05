# Lakeview Dashboard Format Analysis (.lvdash.json)

## Executive Summary

**Finding:** Our current JSON configuration files are **NOT compatible** with the official Databricks `.lvdash.json` format. They serve as **blueprints/documentation** only, while `.lvdash.json` is the actual exportable/importable dashboard format.

## What is .lvdash.json?

The `.lvdash.json` format is the **official Databricks AI/BI (formerly Lakeview) dashboard interchange format** that allows you to:
- ✅ Export dashboards from Databricks UI
- ✅ Import dashboards programmatically via API
- ✅ Version control dashboards in Git
- ✅ Share dashboards across workspaces
- ✅ Automate dashboard deployment

## Format Comparison

### Official .lvdash.json Format

```json
{
  "datasets": [
    {
      "name": "cf431d29",
      "displayName": "combined_usage_and_payloads",
      "query": "SELECT ... FROM system.serving.endpoint_usage...",
      "parameters": [
        {
          "displayName": "inference_table_name",
          "keyword": "inference_table_name",
          "dataType": "STRING",
          "defaultSelection": {}
        }
      ]
    }
  ],
  "pages": [
    {
      "name": "880de22a",
      "displayName": "New Page",
      "layout": [
        {
          "widget": {
            "name": "bb060cd3",
            "queries": [
              {
                "name": "main_query",
                "query": {
                  "datasetName": "cf431d29",
                  "fields": [
                    {
                      "name": "entity_name",
                      "expression": "`entity_name`"
                    }
                  ],
                  "disaggregated": false
                }
              }
            ],
            "spec": {
              "version": 3,
              "widgetType": "line",
              "encodings": {
                "x": {
                  "fieldName": "daily(request_time)",
                  "scale": {"type": "temporal"}
                },
                "y": {
                  "fieldName": "avg(execution_duration_seconds)"
                },
                "color": {
                  "fieldName": "entity_name"
                }
              },
              "frame": {
                "title": "Average Execution Duration by Model",
                "showTitle": true,
                "description": "Monitor daily average..."
              }
            }
          },
          "position": {
            "x": 0,
            "y": 36,
            "width": 3,
            "height": 6
          }
        }
      ]
    }
  ]
}
```

### Our Current Format (Blueprint Only)

```json
{
  "dashboard_name": "Account Monitor",
  "datasets": [
    {
      "name": "contract_burndown_chart",
      "query": "SELECT ... FROM main.account_monitoring_dev.contract_burndown"
    }
  ],
  "pages": [
    {
      "name": "Contract Burndown",
      "layout": [
        {
          "component": "line_chart",
          "title": "Contract Burndown",
          "dataset": "contract_burndown_chart",
          "x_axis": "date",
          "y_axis": ["actual_consumption", "ideal_consumption"],
          "position": {"x": 0, "y": 6, "w": 12, "h": 8}
        }
      ]
    }
  ]
}
```

## Key Differences

| Feature | .lvdash.json (Official) | Our JSON (Blueprint) | Compatible? |
|---------|------------------------|----------------------|-------------|
| **File Extension** | `.lvdash.json` | `.json` | ❌ |
| **Dataset Structure** | `name`, `displayName`, `query`, `parameters` | `name`, `query` | ⚠️ Partial |
| **Widget Format** | Full widget spec with `encodings` | Simple component config | ❌ |
| **Widget Queries** | References datasets with field mappings | Direct dataset reference | ❌ |
| **Position Format** | `{x, y, width, height}` | `{x, y, w, h}` | ⚠️ Similar |
| **Encodings** | Vega-Lite style encodings | Simple axis names | ❌ |
| **Version** | Has spec.version field | No version | ❌ |
| **Widget Names** | UUID-like identifiers | Descriptive names | ❌ |
| **Import/Export** | ✅ Supported via API | ❌ Not supported | ❌ |

## How to Get Real .lvdash.json Files

### Method 1: Export from UI (Recommended)

1. **Open your dashboard** in Databricks
2. **Click the ⋮ menu** (three dots) in top-right
3. **Select "Export"**
4. **File downloads** as `Dashboard_Name.lvdash.json`

### Method 2: Export via API

```bash
# Using databricks CLI
databricks workspace export \
  "/path/to/dashboard" \
  --format AUTO \
  --profile LPT_FREE_EDITION \
  > dashboard.lvdash.json

# Using Workspace API directly
curl -X GET \
  "https://<workspace>.cloud.databricks.com/api/2.0/workspace/export" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "path": "/path/to/dashboard",
    "format": "AUTO",
    "direct_download": true
  }' > dashboard.lvdash.json
```

### Method 3: Create from Scratch (Advanced)

Build the JSON structure following the official format with:
- UUID-style widget names
- Full widget specs with encodings
- Dataset parameters
- Proper version numbers

## How to Import .lvdash.json Files

### Method 1: Import via UI

1. **Go to Dashboards** in Databricks
2. **Click "Create"** → **"Import Dashboard"**
3. **Upload** your `.lvdash.json` file
4. **Configure** workspace path
5. **Click "Import"**

### Method 2: Import via API

```bash
# Using databricks CLI
databricks workspace import \
  "/path/to/new/dashboard" \
  --file dashboard.lvdash.json \
  --format AUTO \
  --language PYTHON \
  --profile LPT_FREE_EDITION

# Using Workspace API
curl -X POST \
  "https://<workspace>.cloud.databricks.com/api/2.0/workspace/import" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/new/dashboard.lvdash.json",
    "format": "AUTO",
    "content": "<base64_encoded_content>"
  }'
```

**CRITICAL:** The path MUST end with `.lvdash.json` for the import to work.

## What Our Current JSON Files Are For

Our configuration files (`lakeview_dashboard_config.json`) serve as:

✅ **Documentation** - Describes what should be built
✅ **Blueprint** - Provides structure and layout guidance
✅ **Query Repository** - Contains all SQL queries
✅ **Design Reference** - Specifies colors, positions, sizes
✅ **Team Communication** - Shares dashboard specifications

❌ **NOT for direct import** - Cannot be imported into Databricks
❌ **NOT programmatically deployable** - No API support
❌ **NOT exportable format** - Different structure

## Migration Path: Blueprint → Real Dashboard

### Current Workflow (Manual)
```
Blueprint JSON → Manual UI Creation → Export .lvdash.json
```

### Recommended Workflow
```
1. Build dashboard manually in UI (using blueprint as guide)
2. Export as .lvdash.json
3. Store .lvdash.json in Git for version control
4. Use .lvdash.json for deployment across workspaces
```

## Real-World Examples

### Example 1: Databricks Usage Dashboard
**Source:** [GitHub Gist by rohit-db](https://gist.github.com/rohit-db/6a5ae039d5df5eb74e8c52a67f9549fe)

Features:
- 13 datasets querying system tables
- Multiple widget types (bar, line, table, scatter, counter)
- Filter widgets (multi-select, single-select)
- Organized page layout

### Example 2: AI Gateway Dashboard
**Source:** [GitHub - mingyu89](https://github.com/mingyu89/ai-gateway/blob/main/%5BExample%5D%20AI%20Gateway%20Dashboard.lvdash.json)

Features:
- Parameterized datasets
- Complex encodings (temporal scales, color mapping)
- Rich frame metadata (titles, descriptions)
- Professional layout

## Converting Our Blueprint to .lvdash.json

### Option 1: Manual Build + Export (Recommended)

1. **Use our blueprint** files as reference
2. **Build dashboard** manually in Databricks UI
3. **Export** to get proper `.lvdash.json`
4. **Store** in version control
5. **Deploy** using import API

**Advantages:**
- ✅ Guaranteed compatibility
- ✅ Visual validation during build
- ✅ Proper widget specs generated
- ✅ No format conversion errors

**Time:** 45-60 minutes per dashboard

### Option 2: Programmatic Conversion (Complex)

Create a converter script that:
1. Reads our blueprint JSON
2. Generates UUID widget names
3. Converts simple config to widget specs
4. Builds encodings from axis definitions
5. Outputs valid `.lvdash.json`

**Challenges:**
- ⚠️ Complex encoding mapping
- ⚠️ Widget spec version compatibility
- ⚠️ Parameter handling
- ⚠️ No official schema documentation

**Time:** 8-16 hours development + testing

### Option 3: Hybrid Approach

1. **Create minimal dashboard** in UI (1 widget)
2. **Export** to get valid `.lvdash.json` template
3. **Modify** the template with our datasets/queries
4. **Import** modified version
5. **Iterate** and refine

**Time:** 2-4 hours per dashboard

## Recommendations

### For Your Project

1. ✅ **Keep current blueprint JSON** - Great documentation
2. ✅ **Build dashboards manually** using blueprints as guides
3. ✅ **Export each dashboard** after building
4. ✅ **Store .lvdash.json files** in Git alongside blueprints
5. ✅ **Use .lvdash.json for deployment** across environments

### File Organization
```
project/
├── blueprints/
│   ├── lakeview_dashboard_config.json          # Documentation
│   └── lakeview_dashboard_config_ibm_style.json # Documentation
├── dashboards/
│   ├── account_monitor.lvdash.json             # Deployable
│   └── account_monitor_ibm_style.lvdash.json   # Deployable
├── notebooks/
│   └── dashboard_queries.sql                    # Queries
└── docs/
    └── CREATE_*_DASHBOARD.md                    # Build guides
```

## API Reference

### Export Dashboard
```bash
GET /api/2.0/workspace/export
{
  "path": "/path/to/dashboard.lvdash.json",
  "format": "AUTO",
  "direct_download": true
}
```

### Import Dashboard
```bash
POST /api/2.0/workspace/import
{
  "path": "/path/to/new/dashboard.lvdash.json",
  "format": "AUTO",
  "content": "<base64_encoded_content>",
  "overwrite": false
}
```

### Publish Dashboard
```bash
POST /api/2.0/lakeview/dashboards/{dashboard_id}/published
{
  "embed_credentials": true
}
```

## Important Notes for 2026

### Legacy Dashboard Migration
- ⚠️ As of **January 12, 2026**, legacy dashboards are deprecated
- ⚠️ Migration page available until **March 2, 2026**
- ✅ All new dashboards should use AI/BI (Lakeview) format
- ✅ `.lvdash.json` is the current standard

### Format Stability
- ✅ `.lvdash.json` format is stable and officially supported
- ✅ Workspace API supports import/export
- ✅ Version control friendly (JSON format)
- ✅ Cross-workspace deployment supported

## Next Steps

1. **Build your first dashboard** manually using the IBM-style blueprint
2. **Export it** as `.lvdash.json`
3. **Inspect the structure** - compare to our blueprint
4. **Store in Git** for version control
5. **Document any custom fields** specific to your use case
6. **Create deployment scripts** using the import API

## Resources

- [Databricks Dashboard Documentation](https://docs.databricks.com/aws/en/dashboards/)
- [Workspace API Tutorial](https://docs.databricks.com/aws/en/dashboards/tutorials/workspace-dashboard-api)
- [Dashboard CRUD API](https://docs.databricks.com/aws/en/dashboards/tutorials/dashboard-crud-api)
- [Example: Databricks Usage Dashboard](https://gist.github.com/rohit-db/6a5ae039d5df5eb74e8c52a67f9549fe)
- [Example: AI Gateway Dashboard](https://github.com/mingyu89/ai-gateway/blob/main/%5BExample%5D%20AI%20Gateway%20Dashboard.lvdash.json)

---

**Summary:** Our JSON files are excellent blueprints but not compatible with `.lvdash.json` format. Build dashboards manually, then export to get proper `.lvdash.json` files for programmatic deployment.
