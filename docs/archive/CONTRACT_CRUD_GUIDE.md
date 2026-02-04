# Contract Management CRUD Operations Guide

## Overview

The `contract_management_crud.py` notebook provides interactive CRUD operations for managing:
- **Contracts** - Contract tracking for consumption monitoring
- **Account Metadata** - Organizational information and team assignments

## Notebook Location

```
notebooks/contract_management_crud.py
```

## Quick Navigation

The notebook is organized into three main sections:

### 1. Contract Management
- **Read** - View all contracts or specific contracts
- **Create** - Add new contracts (3 methods: auto-detect, manual, Python bulk)
- **Update** - Modify contract status, value, dates, or bulk updates
- **Delete** - Remove contracts with safety previews

### 2. Account Metadata Management
- **Read** - View all metadata or search for specific accounts
- **Create** - Add new account info (3 methods: auto-detect, manual, Python bulk)
- **Update** - Modify team members, business units, or bulk assignments
- **Delete** - Remove metadata with relationship checks

### 3. Utilities & Helpers
- View contract-account joins
- Summary statistics
- Data validation checks
- CSV export functionality
- Refresh derived tables

## Key Features

### ✅ Safety First
- Preview operations before execution
- Comments marked with ⚠️ show what to change
- Validation checks for data integrity
- Relationship awareness (no orphaned records)

### 🎯 Multiple Operation Methods

Each CRUD operation provides multiple approaches:

1. **SQL** - Direct SQL statements for single operations
2. **Python** - Programmatic operations for bulk changes
3. **Auto-detect** - Smart defaults using existing usage data

### 🔄 Integration

- Automatically refreshes derived tables after changes
- Validates data relationships
- Provides export functionality for backup

## Common Use Cases

### Add a New Contract

**Quick Method (Auto-detect account):**
```sql
-- Cell: "CREATE - Add New Contract - Option 1"
-- Just change the total_value (5000.00) and run
```

**Full Control Method:**
```sql
-- Cell: "CREATE - Add New Contract - Option 2"
-- Change all values and run
INSERT INTO main.account_monitoring_dev.contracts (...)
VALUES ('CONTRACT_2026_001', 'your-account-id', 'AWS', ...)
```

### Update Team Members

```sql
-- Cell: "UPDATE - Update Team Members"
UPDATE main.account_monitoring_dev.account_metadata
SET
  account_executive = 'New AE Name',
  solutions_architect = 'New SA Name',
  updated_at = CURRENT_TIMESTAMP()
WHERE customer_name = 'Your Customer';
```

### View Contract Status

```sql
-- Cell: "READ - View All Contracts"
-- Shows all contracts with duration and remaining days
```

### Bulk Operations

```python
# Cell: "Python - Add Multiple Contracts"
contracts_data = [
    {"contract_id": "CONTRACT_001", ...},
    {"contract_id": "CONTRACT_002", ...}
]
# Uncomment write statement to execute
```

## Safety Features

### Preview Mode
Most delete and bulk operations default to preview mode:
```python
# Shows what would be deleted
delete_contracts("status = 'PENDING'", preview_only=True)

# Set to False to actually delete
delete_contracts("status = 'PENDING'", preview_only=False)
```

### Data Validation
Run validation after bulk operations:
```python
# Cell: "Data Validation"
validate_data()  # Checks for orphans, invalid dates, duplicates
```

### Refresh Derived Tables
After modifying contracts:
```sql
-- Cell: "Refresh Contract Burndown Data"
REFRESH TABLE main.account_monitoring_dev.contract_burndown;
REFRESH TABLE main.account_monitoring_dev.contract_burndown_summary;
```

## Table Structures

### Contracts Table
```
account_monitoring_dev.contracts
├── contract_id (STRING, PRIMARY KEY)
├── account_id (STRING)
├── cloud_provider (STRING) - AWS, AZURE, GCP
├── start_date (DATE)
├── end_date (DATE)
├── total_value (DECIMAL)
├── currency (STRING) - USD, EUR, etc.
├── commitment_type (STRING) - SPEND or DBU
├── status (STRING) - ACTIVE, EXPIRED, PENDING
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### Account Metadata Table
```
account_monitoring_dev.account_metadata
├── account_id (STRING, PRIMARY KEY)
├── customer_name (STRING)
├── salesforce_id (STRING)
├── business_unit_l0 (STRING) - Region
├── business_unit_l1 (STRING) - Country/Area
├── business_unit_l2 (STRING) - City/Office
├── business_unit_l3 (STRING) - Industry/Segment
├── account_executive (STRING)
├── solutions_architect (STRING)
├── delivery_solutions_architect (STRING)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

## Workflow Examples

### Scenario 1: Onboard New Customer

1. **Check if account exists** (Cell: "READ - View All Account Metadata")
2. **Add account metadata** (Cell: "CREATE - Add New Account Metadata")
3. **Create contract** (Cell: "CREATE - Add New Contract - Option 1")
4. **Validate data** (Cell: "Data Validation")
5. **Refresh dashboard** (Cell: "Refresh Contract Burndown Data")

### Scenario 2: Update Team Assignments

1. **View current assignments** (Cell: "READ - View All Account Metadata")
2. **Update team members** (Cell: "UPDATE - Update Team Members")
3. **Verify changes** (Cell: "READ - View Specific Account")

### Scenario 3: Extend Contract

1. **Find contract** (Cell: "READ - View Specific Contract")
2. **Update end date** (Cell: "UPDATE - Update Contract Dates")
3. **Refresh derived tables** (Cell: "Refresh Contract Burndown Data")
4. **Check dashboard** - Verify burndown chart updated

### Scenario 4: Clean Up Old Data

1. **Preview deletions** (Cell: "DELETE - Delete Expired Contracts")
2. **Run validation** (Cell: "Data Validation")
3. **Execute deletion** (uncomment DELETE statement)
4. **Export backup** (Cell: "Export to CSV") before deleting

## Best Practices

### Before Making Changes
1. ✅ Read the data first to understand current state
2. ✅ Use preview mode for bulk operations
3. ✅ Export to CSV for backup
4. ✅ Check relationships (contracts ↔ metadata)

### After Making Changes
1. ✅ Run data validation checks
2. ✅ Refresh derived tables
3. ✅ Verify dashboard displays correctly
4. ✅ Check contract-account joins

### General Guidelines
- Always update `updated_at` timestamp when modifying records
- Keep contract IDs unique and descriptive
- Ensure account metadata exists before creating contracts
- Use status transitions: PENDING → ACTIVE → EXPIRED
- Document significant changes in contract notes field

## Troubleshooting

### Issue: "No contracts showing in dashboard"
**Solution:**
1. Check contracts exist: Cell "READ - View All Contracts"
2. Verify contract dates overlap with query timeframe
3. Refresh derived tables: Cell "Refresh Contract Burndown Data"

### Issue: "Orphaned contracts (no metadata)"
**Solution:**
1. Run validation: Cell "Data Validation"
2. Add missing metadata: Cell "CREATE - Add New Account Metadata"

### Issue: "Cannot delete contract"
**Solution:**
- Check if contract is referenced in derived tables
- Refresh derived tables first
- Use preview mode to see impact

### Issue: "Bulk update affected wrong records"
**Solution:**
- Always preview first with `preview_only=True`
- Use specific WHERE clauses
- Test on subset before full update

## Integration with Dashboard

After making changes to contracts or metadata:

1. **Refresh derived tables** (required):
   ```sql
   REFRESH TABLE main.account_monitoring_dev.contract_burndown;
   REFRESH TABLE main.account_monitoring_dev.contract_burndown_summary;
   ```

2. **Refresh dashboard**:
   - Go to Lakeview dashboard
   - Click the refresh button
   - Verify charts updated correctly

3. **Check key visualizations**:
   - Contract Burndown Line Chart
   - Contract Summary Table
   - Account Information Table

## Export & Backup

### Export to CSV
```python
# Cell: "Export to CSV"
export_to_csv()
# Creates:
#   /dbfs/tmp/contracts_export.csv
#   /dbfs/tmp/account_metadata_export.csv
```

### Manual Backup
```sql
-- Create backup tables
CREATE TABLE account_monitoring_dev.contracts_backup AS
SELECT * FROM account_monitoring_dev.contracts;

CREATE TABLE account_monitoring_dev.account_metadata_backup AS
SELECT * FROM account_monitoring_dev.account_metadata;
```

## Related Files

- `account_monitor_notebook.py` - Initial data setup and sample data creation
- `lakeview_dashboard_queries.sql` - All dashboard queries
- `create_lakeview_dashboard.py` - Dashboard creation script
- `CREATE_LAKEVIEW_DASHBOARD.md` - Dashboard documentation

## Need Help?

1. Review the notebook markdown cells for detailed instructions
2. Look for ⚠️ warnings that indicate required changes
3. Use preview modes before executing destructive operations
4. Run validation checks after bulk operations
5. Check the dashboard after changes to verify data integrity
