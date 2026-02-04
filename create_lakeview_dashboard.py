#!/usr/bin/env python3
"""
Create Lakeview Dashboard using Databricks Dashboard API
Based on queries from lakeview_dashboard_queries.sql and account_monitor_notebook.py
"""

import json
import uuid
import subprocess
import sys
from typing import Dict, List, Any

# Dashboard Configuration
DASHBOARD_NAME = "Account Monitor - Cost & Usage Tracking with Contract Burndown"
DASHBOARD_DESCRIPTION = "Comprehensive cost and usage tracking with real-time contract burn down analysis"
CATALOG = "main"
SCHEMA = "account_monitoring_dev"


def generate_uid(prefix: str = "") -> str:
    """Generate unique 8-character hex ID for widgets and datasets"""
    return f"{prefix}{uuid.uuid4().hex[:8]}"


class LakeviewDashboardBuilder:
    """Builder class for Lakeview dashboard JSON structure"""

    def __init__(self, name: str):
        self.dashboard = {
            "datasets": [],
            "pages": [],
            "uiSettings": {
                "theme": {
                    "widgetHeaderAlignment": "ALIGNMENT_UNSPECIFIED"
                },
                "applyModeEnabled": False
            }
        }
        self.dataset_map = {}  # Maps dataset name to uid

    def add_dataset(self, name: str, display_name: str, query: str) -> str:
        """Add a dataset (SQL query) to the dashboard"""
        uid = generate_uid("ds_")
        self.dataset_map[name] = uid

        self.dashboard["datasets"].append({
            "name": uid,
            "displayName": display_name,
            "queryLines": [query]
        })
        return uid

    def create_page(self, name: str, display_name: str) -> Dict:
        """Create a new page"""
        page = {
            "name": generate_uid("page_"),
            "displayName": display_name,
            "pageType": "PAGE_TYPE_CANVAS",
            "layout": []
        }
        self.dashboard["pages"].append(page)
        return page

    def add_counter(self, page: Dict, dataset_name: str, field: str, title: str,
                    position: Dict) -> None:
        """Add a counter widget"""
        widget = {
            "widget": {
                "name": generate_uid("widget_"),
                "queries": [{
                    "name": "main_query",
                    "query": {
                        "datasetName": self.dataset_map[dataset_name],
                        "fields": [{"name": field, "expression": f"`{field}`"}],
                        "disaggregated": True
                    }
                }],
                "spec": {
                    "version": 2,
                    "widgetType": "counter",
                    "encodings": {
                        "value": {
                            "fieldName": field,
                            "displayName": title
                        }
                    },
                    "frame": {
                        "showTitle": True,
                        "title": title
                    }
                }
            },
            "position": position
        }
        page["layout"].append(widget)

    def add_line_chart(self, page: Dict, dataset_name: str, x_field: str,
                       y_fields: List[str], title: str, position: Dict,
                       series_field: str = None) -> None:
        """Add a line chart widget"""
        fields = [{"name": x_field, "expression": f"`{x_field}`"}]
        for y in y_fields:
            fields.append({"name": y, "expression": f"`{y}`"})

        if series_field:
            fields.append({"name": series_field, "expression": f"`{series_field}`"})

        encodings = {
            "x": {
                "fieldName": x_field,
                "scale": {"type": "temporal"},
                "displayName": x_field.replace("_", " ").title()
            },
            "y": {
                "fieldName": y_fields[0],  # Primary y-axis
                "scale": {"type": "quantitative"},
                "displayName": "Amount ($)"
            }
        }

        if series_field:
            encodings["color"] = {
                "fieldName": series_field,
                "scale": {"type": "categorical"},
                "displayName": series_field.replace("_", " ").title()
            }

        widget = {
            "widget": {
                "name": generate_uid("widget_"),
                "queries": [{
                    "name": "main_query",
                    "query": {
                        "datasetName": self.dataset_map[dataset_name],
                        "fields": fields,
                        "disaggregated": False
                    }
                }],
                "spec": {
                    "version": 3,
                    "widgetType": "line",
                    "encodings": encodings,
                    "frame": {
                        "showTitle": True,
                        "title": title
                    }
                }
            },
            "position": position
        }
        page["layout"].append(widget)

    def add_bar_chart(self, page: Dict, dataset_name: str, x_field: str,
                      y_field: str, title: str, position: Dict,
                      series_field: str = None, stacked: bool = False) -> None:
        """Add a bar chart widget"""
        fields = [
            {"name": x_field, "expression": f"`{x_field}`"},
            {"name": y_field, "expression": f"`{y_field}`"}
        ]

        if series_field:
            fields.append({"name": series_field, "expression": f"`{series_field}`"})

        encodings = {
            "x": {
                "fieldName": x_field,
                "scale": {"type": "categorical"},
                "displayName": x_field.replace("_", " ").title()
            },
            "y": {
                "fieldName": y_field,
                "scale": {"type": "quantitative"},
                "displayName": y_field.replace("_", " ").title()
            }
        }

        if series_field:
            encodings["color"] = {
                "fieldName": series_field,
                "scale": {"type": "categorical"},
                "displayName": series_field.replace("_", " ").title()
            }

        mark = {"type": "bar"}
        if stacked:
            mark["stacked"] = "stacked"

        widget = {
            "widget": {
                "name": generate_uid("widget_"),
                "queries": [{
                    "name": "main_query",
                    "query": {
                        "datasetName": self.dataset_map[dataset_name],
                        "fields": fields,
                        "disaggregated": False
                    }
                }],
                "spec": {
                    "version": 3,
                    "widgetType": "bar",
                    "encodings": encodings,
                    "mark": mark,
                    "frame": {
                        "showTitle": True,
                        "title": title
                    }
                }
            },
            "position": position
        }
        page["layout"].append(widget)

    def add_pie_chart(self, page: Dict, dataset_name: str, value_field: str,
                      label_field: str, title: str, position: Dict) -> None:
        """Add a pie chart widget"""
        widget = {
            "widget": {
                "name": generate_uid("widget_"),
                "queries": [{
                    "name": "main_query",
                    "query": {
                        "datasetName": self.dataset_map[dataset_name],
                        "fields": [
                            {"name": value_field, "expression": f"`{value_field}`"},
                            {"name": label_field, "expression": f"`{label_field}`"}
                        ],
                        "disaggregated": False
                    }
                }],
                "spec": {
                    "version": 3,
                    "widgetType": "pie",
                    "encodings": {
                        "angle": {
                            "fieldName": value_field,
                            "scale": {"type": "quantitative"},
                            "displayName": value_field.replace("_", " ").title()
                        },
                        "color": {
                            "fieldName": label_field,
                            "scale": {"type": "categorical"},
                            "displayName": label_field.replace("_", " ").title()
                        }
                    },
                    "frame": {
                        "showTitle": True,
                        "title": title
                    }
                }
            },
            "position": position
        }
        page["layout"].append(widget)

    def add_table(self, page: Dict, dataset_name: str, title: str,
                  position: Dict, columns: List[str] = None) -> None:
        """Add a table widget"""
        # If no columns specified, use all fields from query (this is a simplified version)
        # In production, you'd want to specify exact columns with types
        widget = {
            "widget": {
                "name": generate_uid("widget_"),
                "queries": [{
                    "name": "main_query",
                    "query": {
                        "datasetName": self.dataset_map[dataset_name],
                        "fields": [],  # Empty = all columns
                        "disaggregated": True
                    }
                }],
                "spec": {
                    "version": 1,
                    "widgetType": "table",
                    "encodings": {
                        "columns": []  # Empty = auto-detect columns
                    },
                    "frame": {
                        "showTitle": True,
                        "title": title
                    }
                }
            },
            "position": position
        }
        page["layout"].append(widget)

    def add_area_chart(self, page: Dict, dataset_name: str, x_field: str,
                       y_field: str, series_field: str, title: str,
                       position: Dict) -> None:
        """Add an area chart widget"""
        widget = {
            "widget": {
                "name": generate_uid("widget_"),
                "queries": [{
                    "name": "main_query",
                    "query": {
                        "datasetName": self.dataset_map[dataset_name],
                        "fields": [
                            {"name": x_field, "expression": f"`{x_field}`"},
                            {"name": y_field, "expression": f"`{y_field}`"},
                            {"name": series_field, "expression": f"`{series_field}`"}
                        ],
                        "disaggregated": False
                    }
                }],
                "spec": {
                    "version": 3,
                    "widgetType": "area",
                    "encodings": {
                        "x": {
                            "fieldName": x_field,
                            "scale": {"type": "temporal"},
                            "displayName": x_field.replace("_", " ").title()
                        },
                        "y": {
                            "fieldName": y_field,
                            "scale": {"type": "quantitative"},
                            "displayName": "Cost ($)"
                        },
                        "color": {
                            "fieldName": series_field,
                            "scale": {"type": "categorical"},
                            "displayName": series_field.replace("_", " ").title()
                        }
                    },
                    "frame": {
                        "showTitle": True,
                        "title": title
                    }
                }
            },
            "position": position
        }
        page["layout"].append(widget)

    def to_json(self) -> str:
        """Convert dashboard to JSON string"""
        return json.dumps(self.dashboard, indent=2)


def build_dashboard() -> LakeviewDashboardBuilder:
    """Build the complete dashboard structure"""
    builder = LakeviewDashboardBuilder(DASHBOARD_NAME)

    # Add all datasets from the SQL queries
    print("Adding datasets...")

    # Dataset 1: Contract Burndown Chart
    builder.add_dataset(
        "contract_burndown_chart",
        "Contract Burndown Chart",
        f"""SELECT
  contract_id,
  CONCAT(contract_id, ' (USD ', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
  usage_date as date,
  ROUND(cumulative_cost, 2) as actual_consumption,
  ROUND(projected_linear_burn, 2) as ideal_consumption,
  ROUND(commitment, 2) as contract_value,
  ROUND(budget_pct_consumed, 1) as pct_consumed
FROM {CATALOG}.{SCHEMA}.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
ORDER BY contract_id, usage_date"""
    )

    # Dataset 2: Contract Summary Table
    builder.add_dataset(
        "contract_summary_table",
        "Contract Summary",
        f"""SELECT
  contract_id,
  cloud_provider,
  start_date,
  end_date,
  commitment,
  total_consumed,
  budget_remaining,
  consumed_pct,
  pace_status,
  days_remaining,
  projected_end_date
FROM {CATALOG}.{SCHEMA}.contract_burndown_summary
ORDER BY consumed_pct DESC"""
    )

    # Dataset 3: Daily Consumption Counter
    builder.add_dataset(
        "daily_consumption_counter",
        "Daily Consumption",
        f"""SELECT
  SUM(daily_cost) as daily_cost,
  COUNT(DISTINCT contract_id) as active_contracts,
  usage_date as date
FROM {CATALOG}.{SCHEMA}.contract_burndown
WHERE usage_date = CURRENT_DATE() - 1
GROUP BY usage_date"""
    )

    # Dataset 4: Pace Distribution Pie
    builder.add_dataset(
        "pace_distribution_pie",
        "Pace Distribution",
        f"""SELECT
  pace_status,
  COUNT(*) as contract_count
FROM {CATALOG}.{SCHEMA}.contract_burndown_summary
GROUP BY pace_status
ORDER BY
  CASE
    WHEN pace_status LIKE '%OVER%' THEN 1
    WHEN pace_status LIKE '%ABOVE%' THEN 2
    WHEN pace_status LIKE '%ON%' THEN 3
    ELSE 4
  END"""
    )

    # Dataset 5: Contract Monthly Trend
    builder.add_dataset(
        "contract_monthly_trend",
        "Monthly Trend by Contract",
        f"""SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  contract_id,
  SUM(daily_cost) as monthly_cost,
  COUNT(*) as days_active
FROM {CATALOG}.{SCHEMA}.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), contract_id
ORDER BY month, contract_id"""
    )

    # Dataset 6: Top Workspaces Detailed
    builder.add_dataset(
        "top_workspaces_detailed",
        "Top Workspaces (30 days)",
        f"""SELECT
  workspace_id,
  cloud_provider,
  SUM(actual_cost) as total_cost,
  SUM(usage_quantity) as total_dbu,
  COUNT(DISTINCT sku_name) as unique_skus,
  COUNT(DISTINCT usage_date) as active_days
FROM {CATALOG}.{SCHEMA}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id, cloud_provider
ORDER BY SUM(actual_cost) DESC
LIMIT 10"""
    )

    # Dataset 7: Contract Detailed Analysis
    builder.add_dataset(
        "contract_detailed_analysis",
        "Contract Analysis",
        f"""SELECT
  contract_id,
  commitment,
  total_consumed,
  consumed_pct,
  pace_status,
  days_remaining,
  DATEDIFF(projected_end_date, end_date) as days_variance,
  CASE
    WHEN projected_end_date < end_date THEN 'Will deplete early'
    WHEN projected_end_date > end_date THEN 'Under budget'
    ELSE 'On track'
  END as budget_health,
  projected_end_date,
  end_date as contract_end_date
FROM {CATALOG}.{SCHEMA}.contract_burndown_summary
ORDER BY days_remaining"""
    )

    # Dataset 8: Account Overview
    builder.add_dataset(
        "account_overview",
        "Account Overview",
        f"""SELECT
  COUNT(DISTINCT sku_name) as top_sku_count,
  COUNT(DISTINCT workspace_id) as top_workspace_count,
  MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)"""
    )

    # Dataset 9: Data Freshness
    builder.add_dataset(
        "data_freshness",
        "Data Freshness",
        f"""SELECT
  'Consumption' as source,
  MAX(usage_date) as latest_date,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
    ELSE 'False'
  END as verified
FROM system.billing.usage
UNION ALL
SELECT
  'Metrics' as source,
  MAX(usage_date) as latest_date,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
    ELSE 'False'
  END as verified
FROM system.billing.usage"""
    )

    # Dataset 10: Total Spend
    builder.add_dataset(
        "total_spend",
        "Total Spend by Cloud",
        f"""SELECT
  customer_name,
  cloud_provider,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 3) as dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM {CATALOG}.{SCHEMA}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider"""
    )

    # Dataset 11: Monthly Trend
    builder.add_dataset(
        "monthly_trend",
        "Monthly Cost Trend",
        f"""SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  ROUND(SUM(usage_quantity), 2) as monthly_dbu,
  ROUND(SUM(actual_cost), 2) as monthly_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces
FROM {CATALOG}.{SCHEMA}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), cloud_provider
ORDER BY month"""
    )

    # Dataset 12: Top Workspaces (90 days)
    builder.add_dataset(
        "top_workspaces",
        "Top Workspaces (90 days)",
        f"""SELECT
  workspace_id,
  cloud_provider,
  COUNT(DISTINCT sku_name) as sku_count,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM {CATALOG}.{SCHEMA}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY workspace_id, cloud_provider
ORDER BY total_cost DESC
LIMIT 10"""
    )

    # Dataset 13: Top SKUs
    builder.add_dataset(
        "top_skus",
        "Top Consuming SKUs",
        f"""SELECT
  sku_name,
  cloud_provider,
  usage_unit,
  ROUND(SUM(usage_quantity), 2) as total_usage,
  ROUND(SUM(actual_cost), 2) as total_cost,
  COUNT(DISTINCT workspace_id) as workspace_count
FROM {CATALOG}.{SCHEMA}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY sku_name, cloud_provider, usage_unit
ORDER BY total_cost DESC
LIMIT 10"""
    )

    # Dataset 14: Product Category
    builder.add_dataset(
        "product_category",
        "Cost by Product Category",
        f"""SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  product_category as category,
  cloud_provider,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM {CATALOG}.{SCHEMA}.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), product_category, cloud_provider
ORDER BY month"""
    )

    # Dataset 15: Account Info
    builder.add_dataset(
        "account_info",
        "Account Information",
        f"""SELECT
  customer_name,
  CONCAT_WS(' > ', business_unit_l0, business_unit_l1, business_unit_l2, business_unit_l3) as business_unit,
  account_executive,
  solutions_architect,
  delivery_solutions_architect
FROM {CATALOG}.{SCHEMA}.account_metadata
LIMIT 1"""
    )

    # Dataset 16: Combined Burndown
    builder.add_dataset(
        "combined_burndown",
        "Combined Contract Burndown",
        f"""SELECT
  usage_date as date,
  SUM(commitment) as total_commitment,
  SUM(cumulative_cost) as total_consumption,
  ROUND(SUM(cumulative_cost) / SUM(commitment) * 100, 1) as overall_pct_consumed
FROM {CATALOG}.{SCHEMA}.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY usage_date
ORDER BY usage_date"""
    )

    print(f"Added {len(builder.dashboard['datasets'])} datasets")

    # PAGE 1: CONTRACT BURNDOWN
    print("\nBuilding Contract Burndown page...")
    page1 = builder.create_page("contract_burndown", "Contract Burndown")

    # Row 1: Counters (y=0, height=3)
    builder.add_counter(page1, "daily_consumption_counter", "daily_cost",
                       "Yesterday's Consumption", {"x": 0, "y": 0, "width": 2, "height": 3})
    builder.add_counter(page1, "daily_consumption_counter", "active_contracts",
                       "Active Contracts", {"x": 2, "y": 0, "width": 2, "height": 3})

    # Row 1: Pie Chart (y=0, height=6)
    builder.add_pie_chart(page1, "pace_distribution_pie", "contract_count", "pace_status",
                         "Contract Pace Distribution", {"x": 4, "y": 0, "width": 2, "height": 6})

    # Row 2: Main Burndown Line Chart (y=3, height=8)
    builder.add_line_chart(page1, "contract_burndown_chart", "date",
                          ["actual_consumption", "ideal_consumption", "contract_value"],
                          "Contract Burndown - Actual vs Ideal vs Limit",
                          {"x": 0, "y": 3, "width": 4, "height": 8},
                          series_field="contract_label")

    # Row 3: Contract Summary Table (y=6, height=6)
    builder.add_table(page1, "contract_summary_table",
                     "Active Contracts - Status Summary",
                     {"x": 4, "y": 6, "width": 2, "height": 6})

    # Row 4: Monthly Trend Bar Chart (y=11, height=6)
    builder.add_bar_chart(page1, "contract_monthly_trend", "month", "monthly_cost",
                         "Monthly Consumption by Contract",
                         {"x": 0, "y": 11, "width": 6, "height": 6},
                         series_field="contract_id", stacked=True)

    # Row 5: Tables (y=17, height=6)
    builder.add_table(page1, "top_workspaces_detailed",
                     "Top 10 Consuming Workspaces (Last 30 Days)",
                     {"x": 0, "y": 17, "width": 3, "height": 6})
    builder.add_table(page1, "contract_detailed_analysis",
                     "Contract Analysis - Detailed View",
                     {"x": 3, "y": 17, "width": 3, "height": 6})

    # PAGE 2: ACCOUNT OVERVIEW
    print("Building Account Overview page...")
    page2 = builder.create_page("account_overview", "Account Overview")

    # Row 1: Counters and Account Info (y=0)
    builder.add_counter(page2, "account_overview", "top_sku_count",
                       "Unique SKUs", {"x": 0, "y": 0, "width": 2, "height": 3})
    builder.add_counter(page2, "account_overview", "top_workspace_count",
                       "Active Workspaces", {"x": 2, "y": 0, "width": 2, "height": 3})
    builder.add_table(page2, "account_info", "Account Information",
                     {"x": 4, "y": 0, "width": 2, "height": 3})

    # Row 2: Data Freshness (y=3)
    builder.add_table(page2, "data_freshness", "Data Freshness",
                     {"x": 0, "y": 3, "width": 6, "height": 3})

    # Row 3: Total Spend (y=6)
    builder.add_table(page2, "total_spend", "Total Spend by Cloud Provider",
                     {"x": 0, "y": 6, "width": 6, "height": 5})

    # Row 4: Monthly Cost Trend (y=11)
    builder.add_bar_chart(page2, "monthly_trend", "month", "monthly_cost",
                         "Monthly Cost Trend by Cloud",
                         {"x": 0, "y": 11, "width": 6, "height": 6},
                         series_field="cloud_provider")

    # Row 5: Combined Burndown (y=17)
    builder.add_line_chart(page2, "combined_burndown", "date",
                          ["total_consumption", "total_commitment"],
                          "All Contracts Combined - Burndown",
                          {"x": 0, "y": 17, "width": 6, "height": 6})

    # PAGE 3: USAGE ANALYTICS
    print("Building Usage Analytics page...")
    page3 = builder.create_page("usage_analytics", "Usage Analytics")

    # Row 1: Top Tables (y=0)
    builder.add_table(page3, "top_workspaces", "Top Consuming Workspaces (90 days)",
                     {"x": 0, "y": 0, "width": 3, "height": 6})
    builder.add_table(page3, "top_skus", "Top Consuming SKUs (90 days)",
                     {"x": 3, "y": 0, "width": 3, "height": 6})

    # Row 2: Product Category Area Chart (y=6)
    builder.add_area_chart(page3, "product_category", "month", "total_cost", "category",
                          "Cost by Product Category Over Time",
                          {"x": 0, "y": 6, "width": 6, "height": 6})

    print(f"✅ Dashboard built with {len(builder.dashboard['pages'])} pages")
    return builder


def create_dashboard_via_api(profile: str, warehouse_id: str, parent_path: str) -> str:
    """Create dashboard using Databricks CLI API"""
    builder = build_dashboard()

    # Get the dashboard as a dictionary (not a string yet)
    dashboard_dict = builder.dashboard

    # Save dashboard JSON to file for debugging (pretty printed)
    with open("dashboard_payload.json", "w") as f:
        json.dump(dashboard_dict, f, indent=2)
    print(f"\n📄 Dashboard JSON saved to: dashboard_payload.json")

    # Serialize the dashboard as a JSON string (required by API)
    serialized_dashboard_str = json.dumps(dashboard_dict)

    # Prepare API payload
    api_payload = {
        "display_name": DASHBOARD_NAME,
        "warehouse_id": warehouse_id,
        "parent_path": parent_path,
        "serialized_dashboard": serialized_dashboard_str
    }

    # Save full payload
    with open("api_payload.json", "w") as f:
        json.dump(api_payload, f, indent=2)
    print(f"📄 API payload saved to: api_payload.json")

    # Create dashboard via Databricks CLI
    print(f"\n🚀 Creating dashboard via Databricks CLI...")
    print(f"   Profile: {profile}")
    print(f"   Warehouse: {warehouse_id}")
    print(f"   Path: {parent_path}")

    try:
        result = subprocess.run(
            ["databricks", "api", "post", "/api/2.0/lakeview/dashboards",
             "--profile", profile, "--json", "@api_payload.json"],
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        dashboard_id = response.get("dashboard_id")
        dashboard_path = response.get("path")

        print(f"\n✅ Dashboard created successfully!")
        print(f"   Dashboard ID: {dashboard_id}")
        print(f"   Path: {dashboard_path}")

        return dashboard_id

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error creating dashboard:")
        print(f"   {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n❌ Error parsing API response:")
        print(f"   {e}")
        sys.exit(1)


def publish_dashboard(profile: str, dashboard_id: str) -> None:
    """Publish the dashboard"""
    print(f"\n📤 Publishing dashboard {dashboard_id}...")

    try:
        subprocess.run(
            ["databricks", "api", "post", f"/api/2.0/lakeview/dashboards/{dashboard_id}/published",
             "--profile", profile],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Dashboard published successfully!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error publishing dashboard:")
        print(f"   {e.stderr}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Create Lakeview Dashboard")
    parser.add_argument("--profile", required=True, help="Databricks CLI profile")
    parser.add_argument("--warehouse-id", required=True, help="SQL Warehouse ID")
    parser.add_argument("--parent-path", default="/Shared", help="Dashboard parent path")
    parser.add_argument("--publish", action="store_true", help="Publish dashboard after creation")

    args = parser.parse_args()

    print(f"🎨 Creating Lakeview Dashboard: {DASHBOARD_NAME}")
    print(f"📊 Using catalog: {CATALOG}.{SCHEMA}")

    dashboard_id = create_dashboard_via_api(args.profile, args.warehouse_id, args.parent_path)

    if args.publish:
        publish_dashboard(args.profile, dashboard_id)

    print(f"\n🎉 Done! Dashboard ID: {dashboard_id}")
    print(f"\n💡 To publish later, run:")
    print(f"   databricks api post /api/2.0/lakeview/dashboards/{dashboard_id}/published --profile {args.profile}")


if __name__ == "__main__":
    main()
