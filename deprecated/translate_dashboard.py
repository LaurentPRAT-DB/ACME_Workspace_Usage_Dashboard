#!/usr/bin/env python3
"""
Translate dashboard blueprint JSON to AIBI .lvdash.json format
"""
import json
import hashlib
import re
from typing import Dict, List, Any, Tuple

def generate_widget_id(context: str, max_length: int = 8) -> str:
    """Generate a short unique ID based on context"""
    hash_obj = hashlib.md5(context.encode())
    return hash_obj.hexdigest()[:max_length]

def convert_query_to_querylines(query: str) -> List[str]:
    """Convert single query string to queryLines array format"""
    # Split by newlines and preserve formatting
    lines = query.split('\n')
    return [line + '\n' for line in lines]

def generate_display_name(name: str) -> str:
    """Generate human-readable display name from dataset name"""
    # Replace underscores with spaces and title case
    return ' '.join(word.capitalize() for word in name.split('_'))

def extract_query_fields(query: str) -> List[str]:
    """Extract column names/aliases from SELECT clause"""
    # Find SELECT ... FROM
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return []

    select_clause = select_match.group(1)

    # Split by comma (simple approach)
    parts = []
    depth = 0
    current = ""

    for char in select_clause:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += char

    if current.strip():
        parts.append(current.strip())

    # Extract field names (aliases or column names)
    fields = []
    for part in parts:
        # Check for AS alias (with or without quotes)
        as_match = re.search(r'\s+[aA][sS]\s+[\'"]?(\w+)[\'"]?$', part)
        if as_match:
            fields.append(as_match.group(1))
            continue

        # Check for quoted alias without AS
        quote_match = re.search(r"\s+['\"]([^'\"]+)['\"]$", part)
        if quote_match:
            fields.append(quote_match.group(1))
            continue

        # No alias - use column name (last part after dot, remove backticks)
        col_name = part.split('.')[-1].strip().strip('`').strip()
        # Remove function calls
        if '(' not in col_name:
            fields.append(col_name)
        else:
            # Try to extract from simple functions
            simple_match = re.match(r'\w+\((.*?)\)', col_name)
            if simple_match:
                inner = simple_match.group(1).strip()
                if ',' not in inner and '(' not in inner:
                    fields.append(inner.split('.')[-1].strip('`'))

    return fields

def get_dataset_query(datasets: List[Dict], dataset_name: str) -> str:
    """Get query for a dataset by name"""
    for ds in datasets:
        if ds["name"] == dataset_name:
            return ds.get("query", "")
    return ""

def convert_dataset(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Convert blueprint dataset to AIBI format"""
    result = {
        "name": dataset["name"],
        "displayName": generate_display_name(dataset["name"]),
        "queryLines": convert_query_to_querylines(dataset["query"])
    }

    # Check if query has parameters (contains :param_)
    param_pattern = re.compile(r':(\w+)')
    params = param_pattern.findall(dataset["query"])

    if params:
        parameters = []
        for param in set(params):  # unique params only
            # Infer data type from parameter name
            data_type = "STRING"
            if "date" in param.lower():
                data_type = "DATE"
            elif any(x in param.lower() for x in ["count", "limit", "top", "num"]):
                data_type = "INTEGER"

            param_def = {
                "displayName": param,
                "keyword": param,
                "dataType": data_type,
                "defaultSelection": {
                    "values": {
                        "dataType": data_type,
                        "values": []
                    }
                }
            }
            parameters.append(param_def)

        result["parameters"] = parameters

    return result

def create_counter_widget(component: Dict, dataset_name: str, widget_id: str) -> Dict:
    """Create counter widget specification"""
    return {
        "widget": {
            "name": widget_id,
            "queries": [{
                "name": f"{widget_id}_query",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [{
                        "name": component["field"],
                        "expression": f"`{component['field']}`"
                    }],
                    "disaggregated": False
                }
            }],
            "spec": {
                "version": 2,
                "widgetType": "counter",
                "encodings": {
                    "target": {  # Changed from "value" to "target"
                        "fieldName": component["field"],
                        "displayName": component["field"]
                    }
                },
                "frame": {
                    "showTitle": True,
                    "title": component.get("title", "Counter"),
                    "showDescription": component.get("description") is not None,
                    "description": component.get("description", "")
                }
            }
        }
    }

def create_table_widget(component: Dict, dataset_name: str, widget_id: str) -> Dict:
    """Create table widget specification"""
    return {
        "widget": {
            "name": widget_id,
            "queries": [{
                "name": f"{widget_id}_query",
                "query": {
                    "datasetName": dataset_name,
                    "disaggregated": False
                }
            }],
            "spec": {
                "version": 1,  # Tables use version 1
                "widgetType": "table",
                "encodings": {
                    "columns": []  # Empty array lets Databricks auto-detect columns
                },
                "frame": {
                    "showTitle": True,
                    "title": component.get("title", "Table"),
                    "showDescription": component.get("description") is not None,
                    "description": component.get("description", "")
                },
                "invisibleColumns": [],
                "withRowNumber": False
            }
        }
    }

def create_line_chart_widget(component: Dict, dataset_name: str, widget_id: str, query: str = "") -> Dict:
    """Create line chart widget specification"""
    y_fields = component.get("y_axis", [])
    if isinstance(y_fields, str):
        y_fields = [y_fields]

    x_field = component.get("x_axis", "date")

    # Extract fields from query to add to query definition
    query_fields = []
    if query:
        available_fields = extract_query_fields(query)
        # Add x-axis field
        if x_field in available_fields:
            query_fields.append({"name": x_field, "expression": f"`{x_field}`"})
        # Add y-axis fields
        for y_field in y_fields:
            if y_field in available_fields:
                query_fields.append({"name": y_field, "expression": f"`{y_field}`"})
        # Add series field
        if component.get("series") and component["series"] in available_fields:
            query_fields.append({"name": component["series"], "expression": f"`{component['series']}`"})

    encodings = {
        "x": {
            "fieldName": x_field,
            "scale": {"type": "temporal"}
        }
    }

    # Add y-axis (first field) with scale property
    if y_fields:
        encodings["y"] = {
            "fieldName": y_fields[0],
            "scale": {"type": "quantitative"}
        }

    # Add series/color if specified
    if component.get("series"):
        encodings["color"] = {
            "fieldName": component["series"]
        }

    query_def = {
        "datasetName": dataset_name,
        "disaggregated": False
    }
    if query_fields:
        query_def["fields"] = query_fields

    return {
        "widget": {
            "name": widget_id,
            "queries": [{
                "name": f"{widget_id}_query",
                "query": query_def
            }],
            "spec": {
                "version": 2,
                "widgetType": "line",
                "encodings": encodings,
                "frame": {
                    "showTitle": True,
                    "title": component.get("title", "Line Chart"),
                    "showDescription": component.get("description") is not None,
                    "description": component.get("description", "")
                }
            }
        }
    }

def create_bar_chart_widget(component: Dict, dataset_name: str, widget_id: str, query: str = "") -> Dict:
    """Create bar chart widget specification"""
    x_field = component.get("x_axis", "category")
    y_field = component.get("y_axis", "value")

    # Extract fields from query
    query_fields = []
    if query:
        available_fields = extract_query_fields(query)
        # Add x-axis field
        if x_field in available_fields:
            query_fields.append({"name": x_field, "expression": f"`{x_field}`"})
        # Add y-axis field
        if y_field in available_fields:
            query_fields.append({"name": y_field, "expression": f"`{y_field}`"})
        # Add series field
        if component.get("series") and component["series"] in available_fields:
            query_fields.append({"name": component["series"], "expression": f"`{component['series']}`"})

    # Determine scale type based on field name
    x_scale_type = "temporal" if any(t in x_field.lower() for t in ["date", "month", "week", "day", "time"]) else "categorical"

    encodings = {
        "x": {
            "fieldName": x_field,
            "scale": {"type": x_scale_type}
        },
        "y": {
            "fieldName": y_field,
            "scale": {"type": "quantitative"}
        }
    }

    # Add series/color if specified
    if component.get("series"):
        encodings["color"] = {
            "fieldName": component["series"]
        }

    query_def = {
        "datasetName": dataset_name,
        "disaggregated": False
    }
    if query_fields:
        query_def["fields"] = query_fields

    return {
        "widget": {
            "name": widget_id,
            "queries": [{
                "name": f"{widget_id}_query",
                "query": query_def
            }],
            "spec": {
                "version": 2,
                "widgetType": "bar",
                "encodings": encodings,
                "frame": {
                    "showTitle": True,
                    "title": component.get("title", "Bar Chart"),
                    "showDescription": component.get("description") is not None,
                    "description": component.get("description", "")
                }
            }
        }
    }

def create_pie_chart_widget(component: Dict, dataset_name: str, widget_id: str, query: str = "") -> Dict:
    """Create pie chart widget specification (approximation)"""
    label_field = component.get("label_field", "label")
    value_field = component.get("value_field", "value")

    # Extract fields from query
    query_fields = []
    if query:
        available_fields = extract_query_fields(query)
        if label_field in available_fields:
            query_fields.append({"name": label_field, "expression": f"`{label_field}`"})
        if value_field in available_fields:
            query_fields.append({"name": value_field, "expression": f"`{value_field}`"})

    query_def = {
        "datasetName": dataset_name,
        "disaggregated": False
    }
    if query_fields:
        query_def["fields"] = query_fields

    return {
        "widget": {
            "name": widget_id,
            "queries": [{
                "name": f"{widget_id}_query",
                "query": query_def
            }],
            "spec": {
                "version": 2,
                "widgetType": "bar",  # Pie might need to be bar in AIBI
                "encodings": {
                    "x": {
                        "fieldName": label_field,
                        "scale": {"type": "categorical"}
                    },
                    "y": {
                        "fieldName": value_field,
                        "scale": {"type": "quantitative"}
                    }
                },
                "frame": {
                    "showTitle": True,
                    "title": component.get("title", "Pie Chart"),
                    "showDescription": component.get("description") is not None,
                    "description": component.get("description", "")
                }
            }
        }
    }

def create_widget_from_component(component: Dict, widget_id: str, datasets: List[Dict]) -> Dict:
    """Create widget based on component type"""
    dataset_name = component.get("dataset", "unknown")
    component_type = component.get("component", "table")

    # Get query for this dataset
    query = get_dataset_query(datasets, dataset_name)

    widget_creators = {
        "counter": create_counter_widget,
        "table": create_table_widget,
        "line_chart": lambda c, d, w: create_line_chart_widget(c, d, w, query),
        "bar_chart": lambda c, d, w: create_bar_chart_widget(c, d, w, query),
        "stacked_area_chart": lambda c, d, w: create_line_chart_widget(c, d, w, query),
        "pie_chart": lambda c, d, w: create_pie_chart_widget(c, d, w, query)
    }

    creator = widget_creators.get(component_type, create_table_widget)
    return creator(component, dataset_name, widget_id)

def convert_page_layout(page: Dict, page_idx: int, datasets: List[Dict]) -> Dict:
    """Convert blueprint page to AIBI format with stacked layout"""
    page_name = f"page{page_idx + 1}"

    layout = []
    current_y = 0

    for component in page.get("layout", []):
        # Generate widget ID from title or component type
        context = f"{page['name']}_{component.get('title', component.get('component', 'widget'))}"
        widget_id = generate_widget_id(context)

        # Get original position or create stacked position
        orig_pos = component.get("position", {})
        height = orig_pos.get("h", orig_pos.get("height", 6))
        width = orig_pos.get("w", orig_pos.get("width", 12))

        # Create widget (pass datasets for query lookup)
        widget_spec = create_widget_from_component(component, widget_id, datasets)

        # Add position (stacked vertically)
        layout.append({
            **widget_spec,
            "position": {
                "x": 0,
                "y": current_y,
                "width": width,
                "height": height
            }
        })

        current_y += height

    return {
        "name": page_name,
        "displayName": page.get("name", f"Page {page_idx + 1}"),
        "layout": layout
    }

def translate_dashboard(blueprint_path: str, output_path: str) -> Dict[str, Any]:
    """Main translation function"""

    # Load blueprint
    with open(blueprint_path, 'r') as f:
        blueprint = json.load(f)

    # Track progress
    progress = {
        "datasets_converted": 0,
        "pages_converted": 0,
        "widgets_converted": 0,
        "warnings": [],
        "todo": []
    }

    # Convert datasets
    aibi_datasets = []
    for dataset in blueprint.get("datasets", []):
        try:
            converted = convert_dataset(dataset)
            aibi_datasets.append(converted)
            progress["datasets_converted"] += 1
        except Exception as e:
            progress["warnings"].append(f"Dataset '{dataset.get('name')}': {str(e)}")

    # Convert pages (pass datasets for query lookup)
    aibi_pages = []
    for idx, page in enumerate(blueprint.get("pages", [])):
        try:
            converted_page = convert_page_layout(page, idx, blueprint.get("datasets", []))
            aibi_pages.append(converted_page)
            progress["pages_converted"] += 1
            progress["widgets_converted"] += len(converted_page["layout"])
        except Exception as e:
            progress["warnings"].append(f"Page '{page.get('name')}': {str(e)}")

    # Create AIBI format
    aibi_dashboard = {
        "datasets": aibi_datasets,
        "pages": aibi_pages
    }

    # Save output
    with open(output_path, 'w') as f:
        json.dump(aibi_dashboard, f, indent=2)

    # Identify what's left to do
    progress["todo"].extend([
        "✓ Datasets converted with displayName and queryLines",
        "✓ Basic widget types converted (counter, table, line, bar)",
        "✓ Widgets stacked vertically in layout",
        "✓ Widget IDs generated from context",
        "⚠ Parameters auto-detected but need manual validation",
        "⚠ Complex encodings may need refinement (multi-axis charts)",
        "⚠ Filter widgets not included (date_range, multi_select)",
        "⚠ Refresh schedule and permissions not in interchange format",
        "⚠ Conditional formatting not included",
        "TODO: Test import in Databricks",
        "TODO: Add filter widgets if needed",
        "TODO: Refine encodings for complex visualizations",
        "TODO: Add field expressions for calculated fields"
    ])

    return progress

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python translate_dashboard.py <blueprint.json> [output.lvdash.json]")
        sys.exit(1)

    blueprint_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else blueprint_file.replace('.json', '.lvdash.json')

    print(f"📖 Reading blueprint: {blueprint_file}")
    progress = translate_dashboard(blueprint_file, output_file)

    print(f"\n✅ Translation complete!")
    print(f"📊 Output: {output_file}")
    print(f"\n📈 Progress Summary:")
    print(f"  - Datasets converted: {progress['datasets_converted']}")
    print(f"  - Pages converted: {progress['pages_converted']}")
    print(f"  - Widgets converted: {progress['widgets_converted']}")

    if progress['warnings']:
        print(f"\n⚠️  Warnings ({len(progress['warnings'])}):")
        for warning in progress['warnings']:
            print(f"  - {warning}")

    print(f"\n📋 Status & TODO:")
    for item in progress['todo']:
        print(f"  {item}")
