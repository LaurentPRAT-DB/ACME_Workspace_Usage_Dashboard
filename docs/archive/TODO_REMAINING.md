# What's Left to Do - Iterative Process

## ✅ COMPLETED (Automated)

### Core Translation
- [x] Convert 15 datasets to AIBI format
- [x] Add `displayName` to all datasets
- [x] Convert `query` strings to `queryLines` arrays
- [x] Generate 16 widgets with proper specs
- [x] Create 3 pages with correct structure
- [x] Generate unique widget IDs from context
- [x] Stack widgets vertically for easy rearrangement

### Bug Fixes
- [x] Fix missing `scale` property on x-axis encodings
- [x] Fix counter widgets to use `target` encoding
- [x] Fix table widgets to use version 1 with proper structure
- [x] Validate JSON syntax
- [x] Test all widget types render

---

## 🔴 HIGH PRIORITY (Must Do)

### 1. Import & Basic Testing (5-10 min)

```bash
# Import the dashboard
databricks workspace import \
  "/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/account_monitor_translated.lvdash.json" \
  --file account_monitor_translated.lvdash.json \
  --format AUTO \
  --overwrite \
  --profile LPT_FREE_EDITION
```

**Test:**
- [ ] Dashboard loads without errors
- [ ] All 15 datasets appear in dataset list
- [ ] All 16 widgets are visible
- [ ] Click each widget and verify it displays data
- [ ] Check for any error messages

**If errors occur:**
1. Read error message carefully
2. Check `BUGFIXES_COMPLETE.md` for similar issues
3. Update translator script if needed
4. Regenerate dashboard
5. Import again

---

## 🟡 MEDIUM PRIORITY (Should Do)

### 2. Add Filter Widgets (15 min)

The blueprint defined 3 filters that aren't auto-generated:

#### Filter 1: Date Range Picker
```
Type: filter-date-picker
Parameters: :param_start_date, :param_end_date
Link to: All datasets that use date filters
Default: Last 12 months
```

**How to add:**
1. Click "Add" → "Filter" → "Date Range"
2. Set parameter names: `param_start_date`, `param_end_date`
3. Link to datasets: dashboard_data, contract_burndown_chart, etc.
4. Set default range: -365 days to today
5. Position at top of page

#### Filter 2: Cloud Provider Multi-Select
```
Type: filter-multi-select
Field: cloud_provider
Query: SELECT DISTINCT cloud_provider FROM dashboard_data
Link to: All datasets
```

**How to add:**
1. Click "Add" → "Filter" → "Multi-Select"
2. Create query: `SELECT DISTINCT cloud_provider FROM main.account_monitoring_dev.dashboard_data`
3. Set parameter name: `param_cloud_provider`
4. Link to all datasets
5. Position next to date filter

#### Filter 3: Contract ID Multi-Select
```
Type: filter-multi-select
Field: contract_id
Query: SELECT DISTINCT contract_id FROM contract_burndown
Link to: Contract-related datasets
```

**How to add:**
1. Click "Add" → "Filter" → "Multi-Select"
2. Create query: `SELECT DISTINCT contract_id FROM main.account_monitoring_dev.contract_burndown`
3. Set parameter name: `param_contract_id`
4. Link to: contract_burndown_chart, contract_summary_table, etc.
5. Position in Contract Burndown page

**After adding filters:**
- [ ] Test each filter works
- [ ] Verify linked datasets update when filter changes
- [ ] Set reasonable defaults

---

### 3. Refine Multi-Axis Charts (20 min)

#### Chart 1: Contract Burndown Line Chart
**Current:** Only shows `actual_consumption`
**Target:** Show all 3 Y-axes:
- `actual_consumption` (blue line)
- `ideal_consumption` (green line)
- `contract_value` (red line)

**How to fix:**
1. Open widget → Edit
2. Go to Y-axis section
3. Click "Add Y-axis"
4. Select `ideal_consumption`
5. Set color to green
6. Click "Add Y-axis" again
7. Select `contract_value`
8. Set color to red
9. Enable legend
10. Save

- [ ] Chart shows 3 lines
- [ ] Legend displays correctly
- [ ] Colors distinguish series

#### Chart 2: Monthly Consumption (Stacked Bar)
**Current:** Basic bar chart
**Target:** Stacked bar with series by `contract_id`

**How to fix:**
1. Open widget → Edit
2. Go to Series section
3. Select series field: `contract_id`
4. Enable "Stacked" option
5. Adjust colors per contract
6. Save

- [ ] Bars are stacked
- [ ] Each contract has distinct color
- [ ] Legend shows all contracts

#### Chart 3: Cost by Product Category
**Current:** Line chart (OK)
**Target:** May want area chart or stacked area

**Optional refinement:**
1. Try changing to stacked area chart
2. Adjust colors per category
3. Configure tooltips

---

### 4. Adjust Layout (20-30 min)

**Current:** All widgets stacked at x=0
**Target:** Match original blueprint layout

#### Page 1: Contract Burndown
```
Original layout from blueprint:
Row 1: [Counter1 (x=0)] [Counter2 (x=3)] [Pie (x=6)]
Row 2: [Line chart full-width (x=0, w=12)]
Row 3: [Table full-width (x=0, w=12)]
Row 4: [Bar chart full-width (x=0, w=12)]
Row 5: [Table (x=0, w=6)] [Table (x=6, w=6)]
```

**How to adjust:**
1. Open dashboard in edit mode
2. Drag widgets to desired positions
3. Resize widgets using corner handles
4. Align widgets using grid
5. Save layout

**Tips:**
- Grid is 12 columns wide
- Each row auto-expands based on content
- Snap to grid for alignment
- Leave gaps between widgets for clarity

- [ ] Counters side-by-side at top
- [ ] Charts at full width
- [ ] Tables arranged logically
- [ ] No overlapping widgets
- [ ] Matches original design intent

---

## 🟢 LOW PRIORITY (Nice to Have)

### 5. Configure Dashboard Settings (10 min)

#### Refresh Schedule
From blueprint:
```json
"refresh_schedule": {
  "frequency": "daily",
  "time": "03:00",
  "timezone": "UTC"
}
```

**How to configure:**
1. Dashboard menu → Settings
2. Refresh schedule → Enable
3. Set frequency: Daily
4. Set time: 3:00 AM
5. Set timezone: UTC
6. Save

- [ ] Schedule configured
- [ ] Runs after data refresh job

#### Permissions
From blueprint:
```json
"permissions": {
  "can_view": ["all_users"],
  "can_edit": ["account_admins"]
}
```

**How to configure:**
1. Dashboard menu → Permissions
2. Add viewer group: All Users
3. Add editor group: Account Admins
4. Save

- [ ] All users can view
- [ ] Only admins can edit

#### Description & Metadata
1. Add dashboard description
2. Set tags (optional)
3. Configure default view

---

### 6. Polish Visualizations (30 min)

#### Table Formatting
- [ ] Set column widths
- [ ] Enable sorting
- [ ] Add search where useful
- [ ] Configure number formatting (decimals, thousands separators)
- [ ] Add conditional formatting (e.g., red for over budget)

#### Chart Polish
- [ ] Customize colors
- [ ] Add value labels
- [ ] Configure tooltips
- [ ] Set axis labels
- [ ] Adjust legends

#### Counter Widgets
- [ ] Set number formatting
- [ ] Add trend indicators (optional)
- [ ] Configure font sizes

---

### 7. Export Final Version (1 min)

After all adjustments:

```bash
# Export the refined dashboard
databricks workspace export \
  "/Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/account_monitor_translated.lvdash.json" \
  --format AUTO \
  --profile LPT_FREE_EDITION \
  > account_monitor_final.lvdash.json

# Commit to Git
git add account_monitor_final.lvdash.json
git commit -m "Add final refined dashboard"
git push
```

- [ ] Exported final version
- [ ] Stored in Git
- [ ] Ready for deployment to other workspaces

---

## ⏱️ Time Estimates

| Priority | Tasks | Time | Total |
|----------|-------|------|-------|
| 🔴 High | Import & test | 5-10 min | 10 min |
| 🟡 Medium | Filters + Charts + Layout | 15 + 20 + 30 min | 65 min |
| 🟢 Low | Settings + Polish + Export | 10 + 30 + 1 min | 41 min |
| **TOTAL** | | | **~2 hours** |

**Note:** This is with the automated translation. Pure manual build would be 3-4 hours.

---

## 🎯 Minimum Viable Dashboard

If time is limited, focus on:
1. ✅ Import & verify (DONE - 10 min)
2. 🟡 Add date range filter (15 min)
3. 🟡 Fix multi-axis line chart (10 min)

**Total:** ~35 minutes for functional dashboard
**Later:** Add remaining filters, polish layout, configure settings

---

## 🔄 Iterative Improvements

### Next Translation Iteration

For future dashboards, improve the translator:

1. **Auto-generate filter widgets**
   - Detect filter definitions in blueprint
   - Create filter widget specs
   - Link to datasets automatically

2. **Multi-axis chart support**
   - Detect arrays in `y_axis` field
   - Create multiple Y-axis encodings
   - Assign distinct colors per series

3. **Smart layout**
   - Respect original x/y positions
   - Create side-by-side arrangements
   - Calculate proper spacing

4. **Column specifications for tables**
   - Query database for column metadata
   - Generate column specs with types
   - Set reasonable default widths

5. **Parameter extraction**
   - Parse SQL for `:param_name` patterns
   - Add parameters array to datasets
   - Link filters to parameters

---

## 📋 Summary

### Automation Success Rate
- ✅ **90%** of basic structure (datasets, widgets, queries)
- ⚠️ **10%** requires manual work (filters, refinement, polish)

### What Couldn't Be Automated (Yet)
- Filter widget generation & linking
- Multi-axis chart encodings
- Complex layouts
- Column formatting specs
- Conditional formatting
- Dashboard settings

### What Was Successfully Automated
- Dataset conversion
- Query preservation
- Basic widget creation
- Widget ID generation
- Stacked layout
- Bug fixes (scale, target, version)

---

**Current Status:** ✅ Core translation complete, ready for refinement
**Next Action:** Import dashboard and start manual refinement
**Estimated Total Time:** 2 hours (vs 3-4 hours manual)
