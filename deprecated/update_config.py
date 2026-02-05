"""
Update Account Monitor Configuration
Utility script to update configuration parameters in the database
"""

from databricks.sdk import WorkspaceClient
import sys
import yaml
import os
from datetime import datetime


# Configuration schema (can be overridden with environment variables)
CATALOG = os.getenv('CATALOG', 'main')
SCHEMA = os.getenv('SCHEMA', 'account_monitoring_dev')
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"


def get_default_warehouse(w: WorkspaceClient):
    """Get the first available SQL warehouse"""
    warehouses = list(w.warehouses.list())
    if not warehouses:
        raise Exception("No SQL warehouses found. Please create one first.")
    return warehouses[0].id


def update_config_value(w: WorkspaceClient, key: str, value: str, value_type: str = 'string'):
    """Update a single configuration value"""
    try:
        warehouse_id = get_default_warehouse(w)

        # Update or insert using statement execution
        w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"""
                MERGE INTO {FULL_SCHEMA}.config AS target
                USING (SELECT '{key}' as config_key) AS source
                ON target.config_key = source.config_key
                WHEN MATCHED THEN
                  UPDATE SET
                    config_value = '{value}',
                    config_type = '{value_type}',
                    updated_at = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN
                  INSERT (config_key, config_value, config_type, updated_at)
                  VALUES ('{key}', '{value}', '{value_type}', CURRENT_TIMESTAMP())
            """,
            wait_timeout='30s'
        )

        print(f"✓ Updated {key} = {value}")
        return True
    except Exception as e:
        print(f"✗ Error updating {key}: {e}")
        return False


def reload_from_yaml(w: WorkspaceClient):
    """Reload all configuration from config.yml"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yml')

    if not os.path.exists(config_path):
        print(f"✗ Config file not found: {config_path}")
        return False

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Update max_projected_end_date
        max_date = config.get('contract_burndown', {}).get('max_projected_end_date', '2032-12-31')
        update_config_value(w, 'max_projected_end_date', max_date, 'date')

        # Update pace thresholds
        thresholds = config.get('contract_burndown', {}).get('pace_thresholds', {})
        update_config_value(w, 'pace_threshold_over', str(thresholds.get('over_pace', 1.2)), 'number')
        update_config_value(w, 'pace_threshold_above', str(thresholds.get('above_pace', 1.1)), 'number')
        update_config_value(w, 'pace_threshold_under', str(thresholds.get('under_pace', 0.8)), 'number')

        # Update refresh settings
        refresh = config.get('refresh', {})
        update_config_value(w, 'lookback_days', str(refresh.get('lookback_days', 365)), 'number')
        update_config_value(w, 'freshness_threshold_days', str(refresh.get('freshness_threshold_days', 2)), 'number')

        # Update account settings
        account = config.get('account', {})
        update_config_value(w, 'default_currency', account.get('default_currency', 'USD'), 'string')

        print("\n✓ All configuration values reloaded from config.yml")
        return True

    except Exception as e:
        print(f"✗ Error loading config file: {e}")
        return False


def show_current_config(w: WorkspaceClient):
    """Display current configuration values"""
    try:
        warehouse_id = get_default_warehouse(w)

        result = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=f"""
                SELECT
                  config_key,
                  config_value,
                  config_type,
                  description,
                  updated_at
                FROM {FULL_SCHEMA}.config
                ORDER BY config_key
            """,
            wait_timeout='30s'
        )

        print("\nCurrent Configuration:")
        print("=" * 80)

        # Display results
        if result.result and result.result.data_array:
            for row in result.result.data_array:
                print(f"{row[0]:30} = {row[1]:20} ({row[2]})")
                if row[3]:
                    print(f"  → {row[3]}")
                print()
        else:
            print("No configuration found")

        print("=" * 80)
        return True

    except Exception as e:
        print(f"✗ Error retrieving config: {e}")
        return False


def main():
    """Main function"""
    print("=" * 70)
    print("Account Monitor - Update Configuration")
    print("=" * 70)
    print()

    # Initialize workspace client
    try:
        w = WorkspaceClient()
        print(f"✓ Connected to workspace: {w.config.host}")
        print(f"✓ Using schema: {FULL_SCHEMA}\n")
    except Exception as e:
        print(f"✗ Failed to connect to Databricks workspace: {e}")
        sys.exit(1)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'show':
            show_current_config(w)

        elif command == 'reload':
            reload_from_yaml(w)

        elif command == 'set' and len(sys.argv) >= 4:
            key = sys.argv[2]
            value = sys.argv[3]
            value_type = sys.argv[4] if len(sys.argv) > 4 else 'string'
            update_config_value(w, key, value, value_type)

        else:
            print("Invalid command")
            print_usage()

    else:
        print_usage()
        print()
        show_current_config(w)


def print_usage():
    """Print usage instructions"""
    print("Usage:")
    print("  python update_config.py show")
    print("    → Display current configuration values")
    print()
    print("  python update_config.py reload")
    print("    → Reload all values from config.yml")
    print()
    print("  python update_config.py set <key> <value> [type]")
    print("    → Update a specific configuration value")
    print("    → Example: python update_config.py set max_projected_end_date 2035-12-31 date")
    print()


if __name__ == "__main__":
    main()
