# Translation Process Improvements - Iterative Enhancement

## 🎯 Current State (Iteration 1 - COMPLETE)

### What Works ✅
- Dataset conversion with displayName and queryLines
- Basic widget types (counter, table, bar, line)
- Automatic scale type detection (temporal vs categorical)
- Counter widgets use 'target' encoding
- Table widgets use version 1 with proper structure
- All x-axis encodings have scale property
- Unique widget ID generation
- Vertical stacking layout

### Success Metrics
- **90% automation** of basic structure
- **100% SQL preservation**
- **0 manual dataset creation** needed
- **16/16 widgets** converted automatically

---

## 🚀 Iteration 2: Identified Gaps & Solutions

### Gap 1: Multi-Axis Charts (MEDIUM COMPLEXITY)

**Current behavior:**
```python
# Only first Y-axis field used
y_axis = ["actual_consumption", "ideal_consumption", "contract_value"]
# Result: Only "actual_consumption" in encoding
```

**Improvement needed:**
```python
def create_multi_axis_encodings(y_fields: List[str]) -> Dict:
    """Create encodings for multiple Y-axes"""
    if len(y_fields) == 1:
        return {"y": {"fieldName": y_fields[0]}}

    # Multiple Y-axes - create separate encodings
    encodings = {}
    for idx, field in enumerate(y_fields):
        key = "y" if idx == 0 else f"y{idx+1}"
        encodings[key] = {
            "fieldName": field,
            "displayName": field.replace("_", " ").title()
        }
    return encodings
```

**Example output:**
```json
{
  "encodings": {
    "x": {"fieldName": "date", "scale": {"type": "temporal"}},
    "y": {"fieldName": "actual_consumption"},
    "y2": {"fieldName": "ideal_consumption"},
    "y3": {"fieldName": "contract_value"}
  }
}
```

**Test case:**
```python
# Input blueprint
{
  "component": "line_chart",
  "y_axis": ["actual", "ideal", "limit"],
  "y_axis_labels": ["Actual Spend", "Ideal Linear", "Contract Limit"]
}

# Expected output
{
  "encodings": {
    "y": {"fieldName": "actual", "displayName": "Actual Spend"},
    "y2": {"fieldName": "ideal", "displayName": "Ideal Linear"},
    "y3": {"fieldName": "limit", "displayName": "Contract Limit"}
  }
}
```

---

### Gap 2: Filter Widget Generation (HIGH COMPLEXITY)

**Current behavior:**
```json
// Filters in blueprint are ignored
"filters": [
  {
    "name": "date_range",
    "type": "date_range",
    "applies_to": ["dataset1", "dataset2"]
  }
]
// Result: Not converted
```

**Improvement needed:**
```python
def create_filter_widgets(filters: List[Dict], page_idx: int) -> List[Dict]:
    """Generate filter widgets from blueprint filters"""
    filter_widgets = []

    for filter_def in filters:
        filter_type = filter_def["type"]

        if filter_type == "date_range":
            widget = create_date_range_filter(filter_def)
        elif filter_type == "multi_select":
            widget = create_multi_select_filter(filter_def)
        elif filter_type == "single_select":
            widget = create_single_select_filter(filter_def)

        filter_widgets.append(widget)

    return filter_widgets

def create_date_range_filter(filter_def: Dict) -> Dict:
    """Create date range filter widget"""
    filter_name = filter_def["name"]
    datasets_to_link = filter_def.get("applies_to", [])

    # Generate queries list for all linked datasets
    queries = []
    for dataset_name in datasets_to_link:
        queries.append({
            "name": f"{filter_name}_{dataset_name}",
            "query": {
                "datasetName": dataset_name,
                "parameters": [
                    {"name": "param_start_date", "keyword": "param_start_date"},
                    {"name": "param_end_date", "keyword": "param_end_date"}
                ],
                "disaggregated": False
            }
        })

    return {
        "widget": {
            "name": generate_widget_id(filter_name),
            "queries": queries,
            "spec": {
                "version": 2,
                "widgetType": "filter-date-range",
                "encodings": {
                    "fields": [
                        {"parameterName": "param_start_date", "queryName": q["name"]}
                        for q in queries
                    ] + [
                        {"parameterName": "param_end_date", "queryName": q["name"]}
                        for q in queries
                    ]
                },
                "frame": {
                    "showTitle": True,
                    "title": filter_def.get("title", filter_name.replace("_", " ").title())
                }
            }
        },
        "position": {"x": 0, "y": 0, "width": 3, "height": 1}
    }
```

**Test case:**
```python
# Input blueprint
{
  "filters": [
    {
      "name": "date_range",
      "type": "date_range",
      "default": "Last 12 months",
      "applies_to": ["dashboard_data", "contract_burndown"]
    }
  ]
}

# Expected: Date range filter widget linking to 2 datasets
```

---

### Gap 3: Smart Layout Positioning (LOW COMPLEXITY)

**Current behavior:**
```python
# All widgets stacked at x=0
position = {"x": 0, "y": current_y, "width": width, "height": height}
```

**Improvement needed:**
```python
def calculate_smart_layout(components: List[Dict]) -> List[Dict]:
    """Arrange widgets intelligently based on size and type"""
    layouts = []
    current_row = 0
    current_x = 0
    row_height = 0

    for component in components:
        width = component["position"].get("w", component["position"].get("width", 12))
        height = component["position"].get("h", component["position"].get("height", 6))

        # Check if widget fits in current row
        if current_x + width > 12:
            # Move to next row
            current_row += row_height
            current_x = 0
            row_height = 0

        # Place widget
        layouts.append({
            "x": current_x,
            "y": current_row,
            "width": width,
            "height": height
        })

        # Update position trackers
        current_x += width
        row_height = max(row_height, height)

    return layouts
```

**Test case:**
```python
# Input: 3 counters (width=3 each)
# Expected: All on same row (x=0, x=3, x=6)

# Input: Counter (w=3) + Full-width chart (w=12)
# Expected: Counter on row 1, chart on row 2
```

---

### Gap 4: Parameter Extraction & Linking (MEDIUM COMPLEXITY)

**Current behavior:**
```python
# Parameters detected but not added to datasets
param_pattern = re.compile(r':(\w+)')
params = param_pattern.findall(query)
# Result: params found but no action taken
```

**Improvement needed:**
```python
def extract_and_link_parameters(query: str) -> List[Dict]:
    """Extract parameters from SQL and create proper definitions"""
    param_pattern = re.compile(r':(\w+)')
    params = param_pattern.findall(query)

    parameter_defs = []
    for param in set(params):
        # Infer type from parameter name and query context
        data_type = infer_parameter_type(param, query)
        default_value = infer_default_value(param, data_type)

        param_def = {
            "displayName": param.replace("_", " ").title(),
            "keyword": param,
            "dataType": data_type,
            "defaultSelection": {
                "values": {
                    "dataType": data_type,
                    "values": [{"value": default_value}] if default_value else []
                }
            }
        }
        parameter_defs.append(param_def)

    return parameter_defs

def infer_parameter_type(param_name: str, query: str) -> str:
    """Infer parameter data type from name and context"""
    param_lower = param_name.lower()

    # Date detection
    if any(x in param_lower for x in ["date", "day", "month", "year", "time"]):
        return "DATE"

    # Integer detection
    if any(x in param_lower for x in ["count", "limit", "top", "num", "id"]):
        return "INTEGER"

    # Boolean detection
    if any(x in param_lower for x in ["is_", "has_", "show_", "enable_"]):
        return "BOOLEAN"

    # Check query context
    if f":{param_name} =" in query or f":{param_name}=" in query:
        # Look at what it's compared to
        context = query[query.find(f":{param_name}"):query.find(f":{param_name}")+100]
        if "'" in context or '"' in context:
            return "STRING"

    return "STRING"  # Default

def infer_default_value(param_name: str, data_type: str) -> Any:
    """Infer reasonable default value"""
    if data_type == "DATE":
        if "start" in param_name.lower():
            return "DATE_SUB(CURRENT_DATE(), 365)"
        elif "end" in param_name.lower():
            return "CURRENT_DATE()"
    elif data_type == "INTEGER":
        if "limit" in param_name.lower() or "top" in param_name.lower():
            return "10"
    elif data_type == "BOOLEAN":
        return "true"

    return None
```

**Test case:**
```python
# Input SQL
query = """
SELECT * FROM table
WHERE usage_date BETWEEN :param_start_date AND :param_end_date
  AND workspace_id = :param_workspace
LIMIT :param_top_n
"""

# Expected output
[
  {
    "keyword": "param_start_date",
    "dataType": "DATE",
    "defaultSelection": {"values": {"values": [{"value": "DATE_SUB(CURRENT_DATE(), 365)"}]}}
  },
  {
    "keyword": "param_end_date",
    "dataType": "DATE",
    "defaultSelection": {"values": {"values": [{"value": "CURRENT_DATE()"}]}}
  },
  {
    "keyword": "param_workspace",
    "dataType": "STRING",
    "defaultSelection": {"values": {"values": []}}
  },
  {
    "keyword": "param_top_n",
    "dataType": "INTEGER",
    "defaultSelection": {"values": {"values": [{"value": "10"}]}}
  }
]
```

---

### Gap 5: Column Specifications for Tables (HIGH COMPLEXITY)

**Current behavior:**
```python
"encodings": {
    "columns": []  # Empty - Databricks auto-detects
}
```

**Improvement needed:**
```python
def generate_column_specs(dataset_name: str, query: str) -> List[Dict]:
    """Generate column specifications from query"""
    # Extract column aliases from SELECT clause
    columns = extract_select_columns(query)

    column_specs = []
    for idx, col in enumerate(columns):
        spec = {
            "fieldName": col["name"],
            "displayName": col.get("alias", col["name"]),
            "type": infer_column_type(col["name"], query),
            "order": idx,
            "visible": True,
            "displayAs": "string",  # Default
            "alignContent": "left"
        }

        # Special formatting for certain types
        if "cost" in col["name"].lower() or "price" in col["name"].lower():
            spec["displayAs"] = "number"
            spec["numberFormat"] = {"prefix": "$", "thousandsSeparator": ","}
        elif "pct" in col["name"].lower() or "percent" in col["name"].lower():
            spec["displayAs"] = "number"
            spec["numberFormat"] = {"suffix": "%"}
        elif "date" in col["name"].lower():
            spec["displayAs"] = "date"
            spec["dateTimeFormat"] = "YYYY-MM-DD"

        column_specs.append(spec)

    return column_specs

def extract_select_columns(query: str) -> List[Dict]:
    """Parse SELECT clause to extract column names and aliases"""
    # Find SELECT ... FROM
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return []

    select_clause = select_match.group(1)

    # Split by comma (accounting for nested functions)
    columns = []
    depth = 0
    current = ""

    for char in select_clause:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            columns.append(parse_column(current.strip()))
            current = ""
            continue
        current += char

    if current.strip():
        columns.append(parse_column(current.strip()))

    return columns

def parse_column(col_expr: str) -> Dict:
    """Parse a single column expression"""
    # Check for alias (AS keyword or space-separated)
    as_match = re.search(r'\s+[aA][sS]\s+[\'"]?(\w+)[\'"]?$', col_expr)
    if as_match:
        alias = as_match.group(1)
        expr = col_expr[:as_match.start()].strip()
        return {"expression": expr, "name": alias, "alias": alias}

    # Check for quoted alias after space
    space_alias_match = re.search(r"\s+['\"]([^'\"]+)['\"]$", col_expr)
    if space_alias_match:
        alias = space_alias_match.group(1)
        expr = col_expr[:space_alias_match.start()].strip()
        return {"expression": expr, "name": alias, "alias": alias}

    # No alias - use expression as name
    name = col_expr.split('.')[-1].strip('`')
    return {"expression": col_expr, "name": name}
```

**Test case:**
```python
# Input SQL
query = """
SELECT
  workspace_id as 'Workspace ID',
  CONCAT('$', FORMAT_NUMBER(SUM(cost), 2)) as 'Total Cost',
  ROUND(SUM(dbu), 2) as 'Total DBU',
  COUNT(DISTINCT sku) as 'SKU Count'
FROM table
"""

# Expected output
[
  {
    "fieldName": "Workspace ID",
    "displayName": "Workspace ID",
    "type": "string",
    "order": 0,
    "visible": true,
    "displayAs": "string",
    "alignContent": "left"
  },
  {
    "fieldName": "Total Cost",
    "displayName": "Total Cost",
    "type": "number",
    "order": 1,
    "visible": true,
    "displayAs": "number",
    "numberFormat": {"prefix": "$", "thousandsSeparator": ","},
    "alignContent": "right"
  },
  // ... etc
]
```

---

## 🔄 Implementation Priority

### Phase 1: Quick Wins (1-2 hours)
1. ✅ **Smart layout positioning** - Easy algorithm
2. ✅ **Parameter extraction** - Pattern matching + type inference
3. ✅ **Multi-axis basic support** - Handle y_axis arrays

### Phase 2: Medium Effort (3-4 hours)
4. ✅ **Column specifications** - SQL parsing + type inference
5. ✅ **Enhanced scale detection** - More field patterns
6. ✅ **Stacked bar charts** - Detect and configure stacking

### Phase 3: Complex Features (5-8 hours)
7. ✅ **Filter widget generation** - Complex query linking
8. ✅ **Conditional formatting** - Rule parsing and application
9. ✅ **Advanced color schemes** - Theme detection

---

## 📝 Test-Driven Development

### Test Suite Structure
```python
# tests/test_translator.py

def test_counter_widget_uses_target_encoding():
    """Verify counter widgets use 'target' not 'value'"""
    result = create_counter_widget({...})
    assert "target" in result["widget"]["spec"]["encodings"]
    assert "value" not in result["widget"]["spec"]["encodings"]

def test_table_widget_version_one():
    """Verify table widgets use version 1"""
    result = create_table_widget({...})
    assert result["widget"]["spec"]["version"] == 1

def test_scale_property_on_all_charts():
    """Verify all chart x-axes have scale property"""
    for chart_type in ["bar", "line"]:
        result = create_chart_widget(chart_type, {...})
        assert "scale" in result["widget"]["spec"]["encodings"]["x"]

def test_temporal_scale_detection():
    """Verify temporal fields get temporal scale"""
    fields = ["date", "month", "week", "timestamp"]
    for field in fields:
        scale_type = detect_scale_type(field)
        assert scale_type == "temporal"

def test_parameter_type_inference():
    """Verify parameter types are inferred correctly"""
    assert infer_parameter_type("start_date", "...") == "DATE"
    assert infer_parameter_type("top_n", "...") == "INTEGER"
    assert infer_parameter_type("workspace_name", "...") == "STRING"

def test_multi_axis_chart():
    """Verify multiple Y-axes are created"""
    component = {
        "y_axis": ["actual", "ideal", "limit"]
    }
    result = create_line_chart_widget(component, "dataset", "id")
    encodings = result["widget"]["spec"]["encodings"]
    assert "y" in encodings
    assert "y2" in encodings
    assert "y3" in encodings
```

### Running Tests
```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=translate_dashboard tests/

# Run specific test
pytest tests/test_translator.py::test_counter_widget_uses_target_encoding -v
```

---

## 📊 Success Metrics for Iteration 2

| Feature | Current | Target |
|---------|---------|--------|
| Automation rate | 90% | 95% |
| Manual refinement time | 60-90 min | 20-30 min |
| Filter widget support | 0% | 100% |
| Multi-axis charts | 33% (1/3 axes) | 100% |
| Parameter linking | 0% | 80% |
| Column formatting | 0% | 60% |
| Smart layouts | 0% (stacked) | 80% (grid) |

---

## 🎯 Roadmap

### Version 1.0 (Current) ✅
- Basic widget conversion
- Dataset transformation
- Bug fixes (scale, target, version)

### Version 1.1 (Next - 2 weeks)
- Smart layouts
- Parameter extraction
- Multi-axis charts
- Enhanced testing

### Version 1.2 (Future - 4 weeks)
- Filter widget generation
- Column specifications
- Conditional formatting
- Performance optimization

### Version 2.0 (Future - 8 weeks)
- AI-powered layout optimization
- Theme detection and application
- Cross-dashboard migration
- Cloud deployment support

---

## 💡 Example: Complete Improved Translator

```python
#!/usr/bin/env python3
"""
Enhanced Dashboard Translator v1.1
Improvements: Multi-axis, parameters, smart layout, filters
"""

def translate_dashboard_v2(blueprint_path: str, output_path: str):
    """Enhanced translation with all improvements"""

    with open(blueprint_path) as f:
        blueprint = json.load(f)

    # Convert datasets with parameter extraction
    datasets = []
    for ds in blueprint["datasets"]:
        converted = convert_dataset_v2(ds)
        datasets.append(converted)

    # Convert pages with smart layout
    pages = []
    for idx, page in enumerate(blueprint["pages"]):
        # Extract filters for this page
        page_filters = get_filters_for_page(blueprint.get("filters", []), page)

        # Convert widgets with improvements
        widgets = []
        for component in page["layout"]:
            widget = create_widget_v2(component)
            widgets.append(widget)

        # Add filter widgets
        filter_widgets = create_filter_widgets(page_filters)

        # Apply smart layout
        all_widgets = filter_widgets + widgets
        positioned_widgets = apply_smart_layout(all_widgets)

        pages.append({
            "name": f"page{idx+1}",
            "displayName": page["name"],
            "layout": positioned_widgets
        })

    # Output
    output = {"datasets": datasets, "pages": pages}
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
```

---

## 🚀 Getting Started with Improvements

### Step 1: Set Up Development Environment
```bash
# Clone or navigate to project
cd /Users/laurent.prat/Documents/lpdev/databricks_conso_reports

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pytest pytest-cov

# Create test directory
mkdir -p tests
```

### Step 2: Add First Improvement (Multi-Axis)
```bash
# Edit translate_dashboard.py
# Add multi_axis support to create_line_chart_widget()

# Test it
python3 translate_dashboard.py lakeview_dashboard_config.json test_v2.lvdash.json

# Verify
jq '.pages[0].layout[3].widget.spec.encodings' test_v2.lvdash.json
```

### Step 3: Iterate
1. Add feature
2. Test manually
3. Add automated test
4. Commit to Git
5. Repeat

---

**Next Steps:**
1. Choose which gap to address first
2. Implement the improvement
3. Test with existing dashboard
4. Document the change
5. Move to next improvement

**Recommended order:** Smart Layout → Multi-Axis → Parameters → Filters → Columns
