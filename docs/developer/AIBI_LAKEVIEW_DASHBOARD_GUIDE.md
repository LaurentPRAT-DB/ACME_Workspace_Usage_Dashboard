# AI/BI Lakeview Dashboard - Comprehensive Guide

**Complete guide for creating Databricks AI/BI Lakeview dashboards programmatically**

**Version:** 1.0
**Created:** 2026-01-29
**Skill:** `fe-databricks-tools:databricks-lakeview-dashboard`

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What is Lakeview (AI/BI)](#what-is-lakeview-aibi)
3. [Available Skill](#available-skill)
4. [Dashboard Architecture](#dashboard-architecture)
5. [Creating Dashboards Programmatically](#creating-dashboards-programmatically)
6. [Widget Types Reference](#widget-types-reference)
7. [Your Project Implementation](#your-project-implementation)
8. [Step-by-Step Examples](#step-by-step-examples)

---

## Overview

### What This Guide Covers

This guide explains:
- ✅ **Lakeview/AI/BI** dashboard concepts
- ✅ **Programmatic creation** using Databricks API
- ✅ **Available Claude skill** for dashboard generation
- ✅ **Your project's** 17 pre-built queries
- ✅ **Complete examples** for all widget types

---

## What is Lakeview (AI/BI)?

### Databricks AI/BI Dashboards (formerly Lakeview)

**Official Name:** Databricks AI/BI Dashboards
**Common Names:** Lakeview, AI/BI, Lakeview Dashboards

**What it is:**
- Next-generation dashboarding solution in Databricks
- Replaces legacy Databricks SQL dashboards
- Built on modern visualization framework
- Native Unity Catalog integration
- AI-powered insights and recommendations

**Key Features:**
- 📊 **Interactive visualizations** - Line, bar, pie, scatter, area charts
- 🎨 **Modern UI** - Beautiful, responsive dashboard layouts
- 🔄 **Real-time updates** - Live data refresh
- 🎯 **Filters** - Date range, dropdowns, multi-select
- 📱 **Mobile responsive** - Works on all devices
- 🤖 **AI insights** - Automated anomaly detection

---

## Available Skill

### Databricks Lakeview Dashboard Skill

**Skill Name:** `fe-databricks-tools:databricks-lakeview-dashboard`

**Location:** `~/.claude/plugins/cache/fe-vibe/fe-databricks-tools/1.0.0/skills/databricks-lakeview-dashboard`

**Usage:**
```
/databricks-lakeview-dashboard [command]
```

**What it Provides:**
1. ✅ **Complete API documentation** for Lakeview dashboards
2. ✅ **Widget schemas** for all visualization types
3. ✅ **Python helper classes** for programmatic creation
4. ✅ **Complete examples** for each widget type
5. ✅ **Filter widgets** (date range, dropdowns, etc.)

---

## Dashboard Architecture

### How Lakeview Dashboards Work

```
┌─────────────────────────────────────────────────────────┐
│                   Lakeview Dashboard                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │               Datasets (SQL Queries)             │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ dataset_1: SELECT * FROM sales                   │   │
│  │ dataset_2: SELECT * FROM contracts               │   │
│  │ dataset_3: SELECT * FROM usage                   │   │
│  └─────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Pages (Dashboard Layouts)              │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Page 1: Overview                                 │   │
│  │   ├─ Widget 1 (Bar Chart) ← dataset_1           │   │
│  │   ├─ Widget 2 (Counter) ← dataset_2             │   │
│  │   └─ Widget 3 (Line Chart) ← dataset_1          │   │
│  │                                                   │   │
│  │ Page 2: Details                                  │   │
│  │   ├─ Widget 4 (Table) ← dataset_3               │   │
│  │   └─ Widget 5 (Pie Chart) ← dataset_2           │   │
│  └─────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Filters (Interactive Controls)        │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ Date Range Picker                                │   │
│  │ Category Dropdown                                │   │
│  │ Multi-select Region                              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Dashboard JSON Structure

```json
{
  "display_name": "My Dashboard",
  "warehouse_id": "<warehouse_id>",
  "parent_path": "/Users/<email>",
  "serialized_dashboard": "{
    \"datasets\": [...],
    \"pages\": [...],
    \"uiSettings\": {...}
  }"
}
```

**Key Components:**
1. **Datasets** - SQL queries that provide data
2. **Pages** - Dashboard pages with layouts
3. **Widgets** - Visualizations (charts, tables, filters)
4. **Layout** - 6-column grid positioning system

---

## Creating Dashboards Programmatically

### Method 1: Using Databricks CLI (API)

**Create Dashboard:**
```bash
databricks api post /api/2.0/lakeview/dashboards \
  --profile <profile> \
  --json '{
    "display_name": "Account Monitor",
    "warehouse_id": "<warehouse_id>",
    "parent_path": "/Users/<email>",
    "serialized_dashboard": "<json_string>"
  }'
```

**Update Dashboard:**
```bash
databricks api patch /api/2.0/lakeview/dashboards/<dashboard_id> \
  --profile <profile> \
  --json '{
    "serialized_dashboard": "<updated_json>"
  }'
```

**Get Dashboard:**
```bash
databricks api get /api/2.0/lakeview/dashboards/<dashboard_id> \
  --profile <profile>
```

**List Dashboards:**
```bash
databricks api get /api/2.0/lakeview/dashboards \
  --profile <profile>
```

**Publish Dashboard:**
```bash
databricks api post /api/2.0/lakeview/dashboards/<dashboard_id>/published \
  --profile <profile>
```

### Method 2: Using Python Helper (from skill)

```python
from lakeview_builder import LakeviewDashboard

# Create dashboard
dashboard = LakeviewDashboard("Account Monitor")

# Add dataset
dashboard.add_dataset(
    "contract_data",
    "Contract Burndown Data",
    """
    SELECT
      usage_date,
      contract_id,
      cumulative_cost,
      commitment
    FROM main.account_monitoring_dev.contract_burndown
    """
)

# Add line chart
dashboard.add_line_chart(
    dataset_name="contract_data",
    x_field="usage_date",
    y_fields=["cumulative_cost", "commitment"],
    title="Contract Burndown",
    position={"x": 0, "y": 0, "width": 6, "height": 4}
)

# Add counter
dashboard.add_counter(
    dataset_name="contract_data",
    value_field="cumulative_cost",
    value_agg="MAX",
    title="Total Spend",
    position={"x": 0, "y": 4, "width": 2, "height": 2}
)

# Get JSON payload for API
json_payload = dashboard.to_json()
```

### Method 3: Manual JSON Construction

```json
{
  "datasets": [
    {
      "name": "abc12345",
      "displayName": "Sales Data",
      "queryLines": [
        "SELECT * FROM catalog.schema.sales"
      ]
    }
  ],
  "pages": [
    {
      "name": "page123",
      "displayName": "Overview",
      "pageType": "PAGE_TYPE_CANVAS",
      "layout": [
        {
          "widget": {
            "name": "widget1",
            "queries": [{"name": "main", "query": {...}}],
            "spec": {...}
          },
          "position": {"x": 0, "y": 0, "width": 3, "height": 4}
        }
      ]
    }
  ]
}
```

---

## Widget Types Reference

### 1. Line Chart

**Use Case:** Trends over time (contract burndown, usage trends)

**JSON Schema:**
```json
{
  "spec": {
    "version": 3,
    "widgetType": "line",
    "encodings": {
      "x": {
        "fieldName": "date",
        "scale": {"type": "temporal"},
        "displayName": "Date"
      },
      "y": {
        "fieldName": "value",
        "scale": {"type": "quantitative"},
        "displayName": "Amount"
      },
      "color": {
        "fieldName": "series",
        "scale": {"type": "categorical"},
        "displayName": "Category"
      }
    },
    "frame": {
      "showTitle": true,
      "title": "Trend Over Time"
    }
  }
}
```

**Your Project Example:**
- Query 1: Contract Burndown Chart
- Shows: actual_consumption, ideal_consumption, contract_value

---

### 2. Bar Chart

**Use Case:** Comparing categories (spend by cloud, top SKUs)

**JSON Schema:**
```json
{
  "spec": {
    "version": 3,
    "widgetType": "bar",
    "encodings": {
      "x": {
        "fieldName": "category",
        "scale": {"type": "categorical"},
        "displayName": "Category"
      },
      "y": {
        "fieldName": "amount",
        "scale": {"type": "quantitative"},
        "displayName": "Total"
      },
      "color": {
        "scale": {
          "mappings": [
            {"value": "aws", "color": "#FF9900"},
            {"value": "azure", "color": "#0078D4"},
            {"value": "gcp", "color": "#4285F4"}
          ]
        }
      }
    }
  }
}
```

**Your Project Examples:**
- Query 5: Monthly Consumption (stacked bar)
- Query 11: Monthly Cost Trend

---

### 3. Pie Chart

**Use Case:** Distribution/proportions (pace distribution, cloud breakdown)

**JSON Schema:**
```json
{
  "spec": {
    "version": 3,
    "widgetType": "pie",
    "encodings": {
      "angle": {
        "fieldName": "count",
        "scale": {"type": "quantitative"}
      },
      "color": {
        "fieldName": "category",
        "scale": {"type": "categorical"}
      }
    }
  }
}
```

**Your Project Example:**
- Query 4: Pace Distribution Pie Chart
- Shows: contract_count by pace_status

---

### 4. Counter (KPI)

**Use Case:** Single metrics (total spend, SKU count, workspace count)

**JSON Schema:**
```json
{
  "spec": {
    "version": 2,
    "widgetType": "counter",
    "encodings": {
      "value": {
        "fieldName": "total",
        "displayName": "Total Revenue"
      }
    },
    "frame": {
      "showTitle": true,
      "title": "Total Revenue"
    }
  }
}
```

**Your Project Examples:**
- Query 3: Daily Consumption Counter
- Query 8: Account Overview Counters (SKU/Workspace counts)

---

### 5. Table

**Use Case:** Detailed data (contract summary, top workspaces)

**JSON Schema:**
```json
{
  "spec": {
    "version": 1,
    "widgetType": "table",
    "encodings": {
      "columns": [
        {
          "fieldName": "col1",
          "type": "string",
          "displayAs": "string",
          "title": "Column 1"
        },
        {
          "fieldName": "col2",
          "type": "float",
          "displayAs": "number",
          "numberFormat": "0.00",
          "alignContent": "right"
        }
      ]
    }
  }
}
```

**Your Project Examples:**
- Query 2: Contract Summary Table
- Query 6: Top Workspaces Detailed
- Query 7: Contract Detailed Analysis
- Query 9: Data Freshness
- Query 12: Top Workspaces

---

### 6. Area Chart

**Use Case:** Stacked trends (product category over time)

**JSON Schema:**
```json
{
  "spec": {
    "version": 3,
    "widgetType": "area",
    "encodings": {
      "x": {"fieldName": "date", "scale": {"type": "temporal"}},
      "y": {"fieldName": "value", "scale": {"type": "quantitative"}},
      "color": {"fieldName": "series", "scale": {"type": "categorical"}}
    }
  }
}
```

**Your Project Example:**
- Query 14: Cost by Product Category (stacked area)

---

### 7. Scatter Plot

**Use Case:** Correlation analysis

**JSON Schema:**
```json
{
  "spec": {
    "version": 3,
    "widgetType": "scatter",
    "encodings": {
      "x": {"fieldName": "x_val", "scale": {"type": "quantitative"}},
      "y": {"fieldName": "y_val", "scale": {"type": "quantitative"}},
      "color": {"fieldName": "group", "scale": {"type": "categorical"}}
    }
  }
}
```

---

### 8. Filter Widgets

**Date Range Picker:**
```json
{
  "spec": {
    "version": 2,
    "widgetType": "filter-date-range-picker",
    "encodings": {
      "fields": [{
        "fieldName": "usage_date",
        "displayName": "Date Range"
      }]
    }
  }
}
```

**Single Select Dropdown:**
```json
{
  "spec": {
    "version": 2,
    "widgetType": "filter-single-select",
    "encodings": {
      "fields": [{
        "fieldName": "account_name",
        "displayName": "Account"
      }]
    }
  }
}
```

**Multi-Select:**
```json
{
  "spec": {
    "version": 2,
    "widgetType": "filter-multi-select",
    "encodings": {
      "fields": [{
        "fieldName": "cloud_provider",
        "displayName": "Cloud Provider"
      }]
    }
  }
}
```

---

## Your Project Implementation

### Current Setup

**File:** `notebooks/lakeview_dashboard_queries.sql`
**Version:** 1.6.0 (Build: 2026-01-29-015)
**Total Queries:** 17

### Dashboard Structure

**Page 1: Contract Burndown (8 visualizations)**
1. Line Chart - Contract burndown with projections
2. Table - Contract summary with status
3. Counter - Daily consumption
4. Pie Chart - Pace distribution
5. Bar Chart - Monthly consumption trend
6. Table - Top workspaces detailed
7. Table - Contract detailed analysis
17. Line Chart - Combined burndown (all contracts)

**Page 2: Account Overview (5 visualizations)**
8. Counters - SKU/Workspace counts
9. Table - Data freshness check
10. Table - Total spend by cloud
11. Bar Chart - Monthly cost trend
16. Table - Account information (team/org)

**Page 3: Usage Analytics (4 visualizations)**
12. Table - Top consuming workspaces
13. Table - Top consuming SKUs
14. Area Chart - Cost by product category
15. Base Data - Dashboard data source

### Data Sources

**System Tables (Read-Only):**
- `system.billing.usage` - Usage records
- `system.billing.list_prices` - Pricing data

**Unity Catalog Tables (Your Data):**
- `main.account_monitoring_dev.dashboard_data` - Pre-aggregated
- `main.account_monitoring_dev.contract_burndown` - Consumption tracking
- `main.account_monitoring_dev.contract_burndown_summary` - Current status
- `main.account_monitoring_dev.account_metadata` - Org information

---

## Step-by-Step Examples

### Example 1: Create Simple Dashboard with 1 Chart

```python
import json
import subprocess

# Dashboard configuration
dashboard_config = {
    "display_name": "Simple Contract Dashboard",
    "warehouse_id": "your_warehouse_id",
    "parent_path": "/Users/your.email@company.com",
    "serialized_dashboard": json.dumps({
        "datasets": [
            {
                "name": "dataset1",
                "displayName": "Contract Data",
                "queryLines": [
                    "SELECT usage_date, cumulative_cost, commitment",
                    "FROM main.account_monitoring_dev.contract_burndown",
                    "WHERE contract_id = 'CONTRACT-2026-001'"
                ]
            }
        ],
        "pages": [
            {
                "name": "page1",
                "displayName": "Overview",
                "pageType": "PAGE_TYPE_CANVAS",
                "layout": [
                    {
                        "widget": {
                            "name": "widget1",
                            "queries": [{
                                "name": "main",
                                "query": {
                                    "datasetName": "dataset1",
                                    "fields": [
                                        {"name": "date", "expression": "`usage_date`"},
                                        {"name": "actual", "expression": "`cumulative_cost`"},
                                        {"name": "limit", "expression": "`commitment`"}
                                    ],
                                    "disaggregated": true
                                }
                            }],
                            "spec": {
                                "version": 3,
                                "widgetType": "line",
                                "encodings": {
                                    "x": {
                                        "fieldName": "date",
                                        "scale": {"type": "temporal"},
                                        "displayName": "Date"
                                    },
                                    "y": [
                                        {
                                            "fieldName": "actual",
                                            "scale": {"type": "quantitative"},
                                            "displayName": "Actual Spend"
                                        },
                                        {
                                            "fieldName": "limit",
                                            "scale": {"type": "quantitative"},
                                            "displayName": "Contract Limit"
                                        }
                                    ]
                                },
                                "frame": {
                                    "showTitle": true,
                                    "title": "Contract Burndown"
                                }
                            }
                        },
                        "position": {"x": 0, "y": 0, "width": 6, "height": 4}
                    }
                ]
            }
        ],
        "uiSettings": {}
    })
}

# Create dashboard via API
result = subprocess.run([
    "databricks", "api", "post", "/api/2.0/lakeview/dashboards",
    "--json", json.dumps(dashboard_config)
], capture_output=True, text=True)

print(result.stdout)
```

### Example 2: Add Counter Widget

```json
{
  "widget": {
    "name": "counter_total_spend",
    "queries": [{
      "name": "main",
      "query": {
        "datasetName": "contract_data",
        "fields": [
          {"name": "total", "expression": "SUM(`cumulative_cost`)"}
        ],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "counter",
      "encodings": {
        "value": {
          "fieldName": "total",
          "displayName": "Total Spend to Date"
        }
      },
      "frame": {
        "showTitle": true,
        "title": "Total Spend"
      }
    }
  },
  "position": {"x": 0, "y": 4, "width": 2, "height": 2}
}
```

### Example 3: Add Filter (Date Range)

```json
{
  "widget": {
    "name": "filter_date",
    "queries": [{
      "name": "filter_query",
      "query": {
        "datasetName": "contract_data",
        "fields": [
          {"name": "date", "expression": "`usage_date`"}
        ],
        "disaggregated": true
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "filter-date-range-picker",
      "encodings": {
        "fields": [{
          "fieldName": "date",
          "displayName": "Date Range",
          "queryName": "filter_query"
        }]
      },
      "frame": {
        "showTitle": true,
        "title": "Select Date Range"
      }
    }
  },
  "position": {"x": 0, "y": 0, "width": 2, "height": 1}
}
```

---

## Grid Layout System

### 6-Column Grid

```
┌─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  ← Columns (x)
├─────┴─────┴─────┴─────┴─────┴─────┤
│                                     │  ← Row 0 (y=0)
├─────────────────────────────────────┤
│                                     │  ← Row 1 (y=1)
├─────────────────────────────────────┤
│                                     │  ← Row 2 (y=2)
└─────────────────────────────────────┘
```

**Position Object:**
```json
{
  "x": 0,        // Column start (0-5)
  "y": 0,        // Row start (0-∞)
  "width": 3,    // Columns to span (1-6)
  "height": 4    // Rows to span (1-∞)
}
```

**Common Layouts:**

**Full Width:**
```json
{"x": 0, "y": 0, "width": 6, "height": 4}
```

**Half Width (Left):**
```json
{"x": 0, "y": 0, "width": 3, "height": 4}
```

**Half Width (Right):**
```json
{"x": 3, "y": 0, "width": 3, "height": 4}
```

**Third Width:**
```json
{"x": 0, "y": 0, "width": 2, "height": 3}
{"x": 2, "y": 0, "width": 2, "height": 3}
{"x": 4, "y": 0, "width": 2, "height": 3}
```

---

## Color Palettes

### Default Databricks Colors

```json
[
  "#FFAB00",  // Orange
  "#00A972",  // Green
  "#FF3621",  // Red
  "#8BCAE7",  // Light Blue
  "#AB4057",  // Burgundy
  "#99DDB4",  // Mint
  "#FCA4A1",  // Pink
  "#919191",  // Gray
  "#BF7080"   // Rose
]
```

### Custom Color Mappings

```json
{
  "scale": {
    "type": "categorical",
    "mappings": [
      {"value": "ON PACE", "color": "#00A972"},
      {"value": "ABOVE PACE", "color": "#FFAB00"},
      {"value": "OVER PACE", "color": "#FF3621"},
      {"value": "UNDER PACE", "color": "#8BCAE7"}
    ]
  }
}
```

### Cloud Provider Colors

```json
{
  "scale": {
    "mappings": [
      {"value": "aws", "color": "#FF9900"},
      {"value": "azure", "color": "#0078D4"},
      {"value": "gcp", "color": "#4285F4"}
    ]
  }
}
```

---

## Tips & Best Practices

### 1. Widget IDs
- Generate unique 8-character hex IDs
- Use consistent naming: `widget_chart_1`, `dataset_sales`

### 2. Dataset Reuse
- One dataset can power multiple widgets
- Define datasets once, reference in all widgets

### 3. Query Optimization
- Pre-aggregate in datasets when possible
- Use `disaggregated: false` for aggregations
- Use `disaggregated: true` for raw data (tables)

### 4. Layout Planning
- Sketch layout on 6-column grid first
- Group related widgets together
- Keep filters at top for visibility

### 5. Color Consistency
- Use color mappings for categorical data
- Maintain brand colors across dashboards
- Use semantic colors (green=good, red=bad)

---

## Troubleshooting

### Dashboard Not Rendering
**Cause:** Invalid JSON in serialized_dashboard
**Solution:** Validate JSON before API call
```bash
echo '<json>' | jq .
```

### Widget Shows No Data
**Cause:** Dataset name mismatch
**Solution:** Verify `datasetName` matches exactly

### Filters Not Working
**Cause:** Missing query name association
**Solution:** Ensure filter `queryName` matches dataset query

### Colors Not Applying
**Cause:** Incorrect scale type or mappings
**Solution:** Use categorical scale with explicit mappings

---

## Next Steps

### To Create Your Dashboard Programmatically:

1. **Use the skill:**
   ```
   /databricks-lakeview-dashboard
   ```

2. **Reference your 17 queries** from `lakeview_dashboard_queries.sql`

3. **Build dashboard JSON** using schemas in this guide

4. **Deploy via API** using Databricks CLI

5. **Publish** for end users

### Documentation References:
- [CREATE_LAKEVIEW_DASHBOARD.md](CREATE_LAKEVIEW_DASHBOARD.md) - Manual creation guide
- [TEAM_DEPLOYMENT_GUIDE.md](TEAM_DEPLOYMENT_GUIDE.md) - Complete deployment
- Skill: `~/.claude/plugins/cache/fe-vibe/fe-databricks-tools/1.0.0/skills/databricks-lakeview-dashboard`

---

**Created:** 2026-01-29
**Version:** 1.0
**For:** Databricks Account Monitor Project
