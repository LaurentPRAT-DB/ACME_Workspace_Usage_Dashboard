# Configuration Quick Reference

## View Configuration
```bash
python update_config.py show
```

## Update Configuration

### Method 1: Edit config.yml and reload
```bash
# 1. Edit config.yml
vim config.yml

# 2. Reload all values
python update_config.py reload
```

### Method 2: Update individual value
```bash
python update_config.py set <key> <value> [type]

# Example:
python update_config.py set max_projected_end_date 2035-12-31 date
```

## Common Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| max_projected_end_date | date | 2032-12-31 | Max date for contract projections |
| pace_threshold_over | number | 1.2 | Over pace threshold (20%) |
| pace_threshold_above | number | 1.1 | Above pace threshold (10%) |
| pace_threshold_under | number | 0.8 | Under pace threshold (20%) |
| lookback_days | number | 365 | Dashboard data lookback period |
| freshness_threshold_days | number | 2 | Data freshness threshold |
| default_currency | string | USD | Default currency code |

## Configuration Files

- **config.yml** - Main configuration (edit this)
- **databricks.yml** - Bundle variables (environment-specific)
- **account_monitoring.config** table - Runtime storage (auto-updated)

## Initial Setup

```bash
# Creates config table and populates it
python setup_account_monitor.py
```

## Verification

```bash
# Show current config
python update_config.py show

# Query config table directly
databricks sql "SELECT * FROM account_monitoring.config ORDER BY config_key"
```

## Troubleshooting

**Config not taking effect?**
```bash
# 1. Verify update succeeded
python update_config.py show

# 2. Refresh the view
databricks sql "REFRESH VIEW account_monitoring.contract_burndown_summary"
```

**Config table missing?**
```bash
python setup_account_monitor.py
```

## Documentation

See `docs/CONFIGURATION_GUIDE.md` for complete documentation.
