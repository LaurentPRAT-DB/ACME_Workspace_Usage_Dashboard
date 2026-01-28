# Configuration Guide

## Overview

The Account Monitor uses a configuration system that stores runtime parameters in a database table. This allows you to change settings without modifying SQL code.

## Configuration Files

### config.yml

The main configuration file that defines all parameters:

```yaml
contract_burndown:
  max_projected_end_date: '2032-12-31'
  pace_thresholds:
    over_pace: 1.2  # 20% over pace
    above_pace: 1.1  # 10% above pace
    under_pace: 0.8  # 20% under pace

refresh:
  lookback_days: 365
  freshness_threshold_days: 2

account:
  default_currency: 'USD'
```

### databricks.yml

The Databricks Asset Bundle configuration includes the max_projected_end_date as a variable:

```yaml
variables:
  max_projected_end_date:
    description: Maximum projected end date for contract burndown calculations
    default: "2032-12-31"
```

## Configuration Table

The configuration is stored in the `account_monitoring.config` table:

| Column | Type | Description |
|--------|------|-------------|
| config_key | STRING | Parameter name |
| config_value | STRING | Parameter value |
| config_type | STRING | Data type (string, date, number, boolean) |
| description | STRING | Parameter description |
| updated_at | TIMESTAMP | Last update time |

## Configuration Parameters

### max_projected_end_date

**Type:** date
**Default:** 2032-12-31
**Description:** Maximum projected end date for contract burndown calculations

This parameter caps the projected completion date to prevent unrealistic projections when contracts have very low burn rates.

**Example:** If a contract has minimal consumption, the projection might extend to 2050 or beyond. This parameter caps it at a reasonable date.

### pace_threshold_over

**Type:** number
**Default:** 1.2
**Description:** Threshold for "over pace" warning (20% over expected consumption)

### pace_threshold_above

**Type:** number
**Default:** 1.1
**Description:** Threshold for "above pace" warning (10% over expected consumption)

### pace_threshold_under

**Type:** number
**Default:** 0.8
**Description:** Threshold for "under pace" indicator (20% under expected consumption)

### lookback_days

**Type:** number
**Default:** 365
**Description:** Number of days to look back for dashboard data

### freshness_threshold_days

**Type:** number
**Default:** 2
**Description:** Maximum age of data before it's considered stale

### default_currency

**Type:** string
**Default:** USD
**Description:** Default currency code for display

## Managing Configuration

### Initial Setup

Configuration is automatically loaded during setup:

```bash
python setup_account_monitor.py
```

This creates the config table and populates it with values from `config.yml`.

### Viewing Current Configuration

To see current configuration values:

```bash
python update_config.py show
```

### Updating Configuration

#### Option 1: Update config.yml and reload

1. Edit `config.yml` with your desired values
2. Reload configuration:

```bash
python update_config.py reload
```

#### Option 2: Update individual values

```bash
python update_config.py set max_projected_end_date 2035-12-31 date
```

Syntax:
```bash
python update_config.py set <key> <value> [type]
```

### Using Configuration in SQL

The SQL queries read configuration values using a CTE:

```sql
WITH config AS (
  SELECT config_value as max_projected_end_date
  FROM account_monitoring.config
  WHERE config_key = 'max_projected_end_date'
),
-- ... rest of query
CROSS JOIN config
```

## Example: Changing Max Projected End Date

### Method 1: Via config.yml

1. Edit `config.yml`:
```yaml
contract_burndown:
  max_projected_end_date: '2035-12-31'
```

2. Reload:
```bash
python update_config.py reload
```

### Method 2: Direct update

```bash
python update_config.py set max_projected_end_date 2035-12-31 date
```

### Verify the change

```bash
python update_config.py show
```

The new date will be used immediately in all queries that reference the configuration.

## Configuration per Environment

You can use different configurations per environment (dev/prod) by:

1. Setting environment-specific values in `databricks.yml`:

```yaml
targets:
  dev:
    variables:
      max_projected_end_date: "2032-12-31"

  prod:
    variables:
      max_projected_end_date: "2035-12-31"
```

2. Running the setup for each environment:

```bash
databricks bundle deploy -t dev
databricks bundle deploy -t prod
```

## Troubleshooting

### Configuration not taking effect

After updating configuration:

1. Verify the update was successful:
```bash
python update_config.py show
```

2. Re-run the query or refresh the view:
```sql
-- Refresh the materialized view if needed
REFRESH VIEW account_monitoring.contract_burndown_summary;
```

### Config table doesn't exist

Run the setup script to create it:
```bash
python setup_account_monitor.py
```

### YAML parsing errors

Ensure your `config.yml` is valid YAML:
- Use spaces (not tabs) for indentation
- Quote date strings
- Check for syntax errors

## Best Practices

1. **Version control:** Keep `config.yml` in version control
2. **Documentation:** Document any custom configuration changes
3. **Testing:** Test configuration changes in dev before applying to prod
4. **Backup:** Export current config before making changes:
```bash
python update_config.py show > config_backup.txt
```

5. **Validation:** After updating, verify queries still work correctly

## Related Files

- `config.yml` - Main configuration file
- `databricks.yml` - Bundle configuration
- `setup_account_monitor.py` - Initial setup and config table creation
- `update_config.py` - Configuration management utility
- `sql/refresh_contract_burndown.sql` - SQL that uses configuration
