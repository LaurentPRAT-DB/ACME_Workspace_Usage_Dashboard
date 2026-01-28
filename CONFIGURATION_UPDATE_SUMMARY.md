# Configuration System Implementation - Summary

## Overview

The maximum projected end date for contract burndown calculations has been moved from a hardcoded value to a configurable parameter stored in a database table.

## Changes Made

### 1. Configuration Files

#### Created: `config.yml`
- Central configuration file for all runtime parameters
- Contains `max_projected_end_date` (default: '2032-12-31')
- Includes additional parameters: pace thresholds, lookback days, etc.

#### Updated: `databricks.yml`
- Added `max_projected_end_date` variable (lines 23-25)
- Can be overridden per environment (dev/prod)

### 2. Database Changes

#### New Table: `account_monitoring.config`
- Stores configuration parameters as key-value pairs
- Columns: config_key, config_value, config_type, description, updated_at
- Created by `setup_account_monitor.py`

### 3. Setup Script Updates

#### Updated: `setup_account_monitor.py`
- Added imports: `yaml`, `os`
- New function: `create_config_table()` - creates config table
- New function: `load_config_from_yaml()` - reads config.yml
- New function: `populate_config_table()` - populates config from YAML
- Updated `main()` to create and populate config table

### 4. SQL Query Updates

#### Updated: `sql/refresh_contract_burndown.sql` (lines 67-71, 117, 121)

**Before:**
```sql
CREATE OR REPLACE VIEW ... AS
WITH latest_burndown AS (
  ...
)
SELECT
  ...
  LEAST(..., CAST('2032-12-31' AS DATE)) as projected_end_date
FROM latest_burndown
```

**After:**
```sql
CREATE OR REPLACE VIEW ... AS
WITH config AS (
  SELECT config_value as max_projected_end_date
  FROM account_monitoring.config
  WHERE config_key = 'max_projected_end_date'
),
latest_burndown AS (
  ...
)
SELECT
  ...
  LEAST(..., CAST(config.max_projected_end_date AS DATE)) as projected_end_date
FROM latest_burndown
CROSS JOIN config
```

### 5. Utility Scripts

#### Created: `update_config.py`
Management utility for configuration:
- `show` - Display current configuration
- `reload` - Reload all values from config.yml
- `set <key> <value> [type]` - Update specific values

#### Created: `docs/CONFIGURATION_GUIDE.md`
Complete documentation covering:
- Configuration file structure
- Configuration parameters
- Management commands
- Best practices
- Troubleshooting

## How It Works

1. **Initial Setup:**
   - Run `python setup_account_monitor.py`
   - Creates `account_monitoring.config` table
   - Populates it with values from `config.yml`

2. **SQL Query Execution:**
   - Query reads `max_projected_end_date` from config table
   - Uses `CROSS JOIN config` to make value available
   - Applies `LEAST()` function with configured date

3. **Configuration Updates:**
   - Option 1: Edit `config.yml` and run `python update_config.py reload`
   - Option 2: Direct update with `python update_config.py set max_projected_end_date 2035-12-31 date`
   - Changes take effect immediately in subsequent query executions

## Benefits

1. **No Code Changes:** Update max date without modifying SQL
2. **Environment-Specific:** Different values for dev/prod
3. **Centralized:** All configuration in one place
4. **Auditable:** Track when configuration was changed
5. **Extensible:** Easy to add new configuration parameters

## Migration Steps

### For Existing Installations

1. Pull latest code with configuration changes
2. Run setup to create config table:
   ```bash
   python setup_account_monitor.py
   ```

3. Verify configuration:
   ```bash
   python update_config.py show
   ```

4. Re-run the SQL to update the view:
   ```bash
   # Execute sql/refresh_contract_burndown.sql in your workspace
   ```

### For New Installations

Configuration is automatically set up during initial setup. Just run:
```bash
python setup_account_monitor.py
```

## Usage Examples

### View current configuration
```bash
python update_config.py show
```

### Change max projected end date to 2035
```bash
# Edit config.yml
python update_config.py reload
```

### Direct update
```bash
python update_config.py set max_projected_end_date 2035-12-31 date
```

### Environment-specific values
```yaml
# In databricks.yml
targets:
  dev:
    variables:
      max_projected_end_date: "2032-12-31"
  prod:
    variables:
      max_projected_end_date: "2040-12-31"
```

## Files Modified

- `databricks.yml` - Added max_projected_end_date variable
- `setup_account_monitor.py` - Added config table creation and population
- `sql/refresh_contract_burndown.sql` - Modified to read from config table

## Files Created

- `config.yml` - Main configuration file
- `update_config.py` - Configuration management utility
- `docs/CONFIGURATION_GUIDE.md` - Complete documentation
- `CONFIGURATION_UPDATE_SUMMARY.md` - This file

## Testing

To verify the configuration system works:

1. Run setup (creates config table)
2. Check config values: `python update_config.py show`
3. Update max date: `python update_config.py set max_projected_end_date 2030-12-31 date`
4. Execute the SQL query
5. Verify projected_end_date never exceeds 2030-12-31

## Future Enhancements

The configuration system can be extended to include:
- Email notification settings
- Alert thresholds
- Dashboard refresh schedules
- Custom business rules
- Integration endpoints

## Support

For questions or issues:
1. See `docs/CONFIGURATION_GUIDE.md` for detailed instructions
2. Check configuration values with `python update_config.py show`
3. Verify config table exists: `SELECT * FROM account_monitoring.config`
