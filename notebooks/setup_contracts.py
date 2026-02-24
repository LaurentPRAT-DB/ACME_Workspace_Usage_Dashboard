# Databricks notebook source
# MAGIC %md
# MAGIC # Contract & Discount Tier Setup from Configuration
# MAGIC
# MAGIC This notebook loads contract data and discount tiers from YAML configuration files.
# MAGIC
# MAGIC **Usage:**
# MAGIC - Edit `config/contracts.yml` to define your contracts
# MAGIC - Edit `config/discount_tiers.yml` to customize discount rates
# MAGIC - Run this notebook (or the setup job) to load the data
# MAGIC
# MAGIC **Parameters:**
# MAGIC - `config_files`: Comma-separated list of contract config files (default: `config/contracts.yml`)
# MAGIC - `discount_tiers_file`: Path to discount tiers config (default: `config/discount_tiers.yml`)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import yaml
from datetime import datetime, timedelta
from pyspark.sql import functions as F

# Get parameters with defaults
dbutils.widgets.text("config_files", "config/contracts.yml", "Config Files (comma-separated)")
dbutils.widgets.text("discount_tiers_file", "config/discount_tiers.yml", "Discount Tiers Config")
dbutils.widgets.text("catalog", "main", "Unity Catalog")
dbutils.widgets.text("schema", "account_monitoring_dev", "Schema")

# Configuration
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
CONFIG_FILES = dbutils.widgets.get("config_files").split(",")
CONFIG_FILES = [f.strip() for f in CONFIG_FILES if f.strip()]  # Clean up whitespace
DISCOUNT_TIERS_FILE = dbutils.widgets.get("discount_tiers_file").strip()

print(f"Contract & Discount Tier Setup v3.0")
print(f"Target: {CATALOG}.{SCHEMA}")
print(f"Contract config files: {CONFIG_FILES}")
print(f"Discount tiers file: {DISCOUNT_TIERS_FILE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Configuration File

# COMMAND ----------

def load_config(config_path: str) -> dict:
    """Load contract configuration from YAML file."""
    import os

    # Get current user for workspace path
    current_user = spark.sql("SELECT current_user()").collect()[0][0]

    # Try multiple paths (workspace vs local)
    paths_to_try = [
        config_path,
        f"../config/{config_path.split('/')[-1]}",  # Relative to notebook
        f"/Workspace/Users/{current_user}/account_monitor/files/{config_path}",
        f"/Workspace/Users/{current_user}/account_monitor/files/config/{config_path.split('/')[-1]}",
    ]

    for path in paths_to_try:
        try:
            # For workspace files
            if path.startswith("/Workspace"):
                content = dbutils.fs.head(f"file:{path}", 50000)
                config = yaml.safe_load(content)
                print(f"  ✓ Loaded config from: {path}")
                return config
            else:
                # For bundled files, read via open()
                try:
                    with open(path, 'r') as f:
                        config = yaml.safe_load(f.read())
                        print(f"  ✓ Loaded config from: {path}")
                        return config
                except FileNotFoundError:
                    continue
        except Exception as e:
            continue

    raise FileNotFoundError(f"Could not find config file. Tried: {paths_to_try}")

def get_default_config():
    """Return default configuration when no config file is found."""
    return {
        "account_metadata": {
            "account_id": "auto",
            "customer_name": "Default Organization",
            "business_unit_l0": "DEFAULT",
            "business_unit_l1": "DEFAULT",
            "business_unit_l2": "DEFAULT",
            "business_unit_l3": "DEFAULT",
            "account_executive": "TBD",
            "solutions_architect": "TBD",
            "delivery_solutions_architect": "TBD",
            "region": "DEFAULT",
            "industry": "DEFAULT"
        },
        "contracts": [{
            "contract_id": "DEFAULT-001",
            "cloud_provider": "auto",
            "start_date": "auto",
            "end_date": "auto",
            "total_value": 10000.00,
            "currency": "USD",
            "commitment_type": "SPEND",
            "status": "ACTIVE",
            "notes": "Default contract - please update config/contracts.yml"
        }]
    }

# Load all configuration files
all_configs = []
print(f"\nLoading {len(CONFIG_FILES)} config file(s)...")

for config_file in CONFIG_FILES:
    try:
        config = load_config(config_file)
        all_configs.append(config)
        print(f"    Account: {config.get('account_metadata', {}).get('customer_name', 'N/A')}")
        print(f"    Contracts: {len(config.get('contracts', []))}")
    except Exception as e:
        print(f"  ✗ Error loading {config_file}: {e}")

# If no configs loaded, use default
if not all_configs:
    print("\nNo config files loaded. Using default configuration...")
    all_configs = [get_default_config()]

# Merge all configs - combine contracts from all files
# Use first config's account_metadata, but merge all contracts
merged_config = {
    "account_metadata": all_configs[0].get("account_metadata", {}),
    "contracts": []
}

for cfg in all_configs:
    merged_config["contracts"].extend(cfg.get("contracts", []))

config = merged_config
print(f"\n✓ Total contracts to process: {len(config['contracts'])}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Resolve Auto Values

# COMMAND ----------

def get_actual_account_id() -> str:
    """Get the actual account_id from system.billing.usage."""
    result = spark.sql("""
        SELECT DISTINCT account_id
        FROM system.billing.usage
        LIMIT 1
    """).collect()
    if result:
        return result[0]['account_id']
    raise ValueError("No account_id found in system.billing.usage")

def get_actual_cloud_provider() -> str:
    """Get the cloud provider from system.billing.usage."""
    result = spark.sql("""
        SELECT DISTINCT cloud as cloud_provider
        FROM system.billing.usage
        WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
        LIMIT 1
    """).collect()
    if result:
        return result[0]['cloud_provider']
    return "AWS"  # Default

def resolve_date(date_value: str, is_start: bool = True) -> str:
    """Resolve 'auto' dates to actual dates."""
    if date_value == "auto":
        if is_start:
            # 1 year ago
            return (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        else:
            # 1 year from now
            return (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    return date_value

def calculate_optimal_commitment(start_date: str, end_date: str, target_utilization: float = 0.95) -> float:
    """
    Calculate optimal contract commitment based on historical consumption and forecasting.

    Uses the same logic as auto_commit_optimizer:
    - Analyzes historical consumption
    - Projects future consumption using linear trend
    - Finds commitment that achieves target utilization with best discount

    Args:
        start_date: Contract start date (YYYY-MM-DD)
        end_date: Contract end date (YYYY-MM-DD)
        target_utilization: Target utilization percentage (default 95%)

    Returns:
        Optimal commitment amount in dollars
    """
    from datetime import datetime as dt_class

    # Parse dates
    start = dt_class.strptime(start_date, '%Y-%m-%d').date()
    end = dt_class.strptime(end_date, '%Y-%m-%d').date()
    today = dt_class.now().date()

    # Calculate contract duration in days
    contract_days = (end - start).days
    duration_years = max(1, round(contract_days / 365))

    # Get historical consumption (last 365 days)
    historical_df = spark.sql("""
        SELECT
            usage_date,
            SUM(usage_quantity * pricing.default) as daily_cost
        FROM system.billing.usage
        WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
          AND usage_date < CURRENT_DATE()
        GROUP BY usage_date
        ORDER BY usage_date
    """).toPandas()

    if historical_df.empty:
        print("  WARNING: No historical consumption data found. Using default commitment.")
        return 10000.00

    # Calculate consumption metrics
    historical_df['daily_cost'] = historical_df['daily_cost'].astype(float)
    daily_avg = historical_df['daily_cost'].mean()
    daily_std = historical_df['daily_cost'].std()

    # Calculate trend (simple linear regression)
    if len(historical_df) > 7:
        import numpy as np
        x = np.arange(len(historical_df))
        y = historical_df['daily_cost'].values
        mask = np.isfinite(y)
        if mask.sum() > 2:
            slope, _ = np.polyfit(x[mask], y[mask], 1)
        else:
            slope = 0
    else:
        slope = 0

    # Project consumption over contract period
    # Historical portion (from start to today or contract start, whichever is later)
    if start < today:
        # Some historical data within contract period
        contract_historical_days = min((today - start).days, contract_days)
        forecast_days = contract_days - contract_historical_days
    else:
        # Future contract - all forecast
        contract_historical_days = 0
        forecast_days = contract_days

    # Calculate projected total
    # Historical portion uses actual average
    historical_portion = contract_historical_days * daily_avg

    # Forecast portion uses average + trend
    forecast_portion = 0
    for i in range(forecast_days):
        day_value = daily_avg + (slope * (contract_historical_days + i))
        forecast_portion += max(0, day_value)

    projected_total = historical_portion + forecast_portion

    # Calculate optimal commitment for target utilization
    optimal_commitment = projected_total / target_utilization

    # Round to nearest $1000 for cleaner numbers
    optimal_commitment = round(optimal_commitment / 1000) * 1000

    # Ensure minimum commitment
    optimal_commitment = max(optimal_commitment, 1000.00)

    print(f"  Auto-calculated commitment:")
    print(f"    Historical daily avg: ${daily_avg:,.2f}")
    print(f"    Projected total: ${projected_total:,.2f}")
    print(f"    Optimal commitment (at {target_utilization*100:.0f}% util): ${optimal_commitment:,.2f}")

    return optimal_commitment

# Resolve auto values
actual_account_id = get_actual_account_id()
actual_cloud_provider = get_actual_cloud_provider()

print(f"Resolved values:")
print(f"  Account ID: {actual_account_id}")
print(f"  Cloud Provider: {actual_cloud_provider}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Insert Account Metadata

# COMMAND ----------

account_meta = config.get('account_metadata', {})

# Resolve account_id
account_id = actual_account_id if account_meta.get('account_id') == 'auto' else account_meta.get('account_id')

# Build the merge statement
merge_sql = f"""
MERGE INTO {CATALOG}.{SCHEMA}.account_metadata AS target
USING (
  SELECT
    '{account_id}' as account_id,
    '{account_meta.get("customer_name", "Unknown")}' as customer_name,
    '{account_meta.get("business_unit_l0", "")}' as business_unit_l0,
    '{account_meta.get("business_unit_l1", "")}' as business_unit_l1,
    '{account_meta.get("business_unit_l2", "")}' as business_unit_l2,
    '{account_meta.get("business_unit_l3", "")}' as business_unit_l3,
    '{account_meta.get("account_executive", "")}' as account_executive,
    '{account_meta.get("solutions_architect", "")}' as solutions_architect,
    '{account_meta.get("delivery_solutions_architect", "")}' as delivery_solutions_architect,
    '{account_meta.get("region", "")}' as region,
    '{account_meta.get("industry", "")}' as industry,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as updated_at
) AS source
ON target.account_id = source.account_id
WHEN MATCHED THEN UPDATE SET
  customer_name = source.customer_name,
  business_unit_l0 = source.business_unit_l0,
  business_unit_l1 = source.business_unit_l1,
  business_unit_l2 = source.business_unit_l2,
  business_unit_l3 = source.business_unit_l3,
  account_executive = source.account_executive,
  solutions_architect = source.solutions_architect,
  delivery_solutions_architect = source.delivery_solutions_architect,
  region = source.region,
  industry = source.industry,
  updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT *
"""

spark.sql(merge_sql)
print(f"✓ Account metadata inserted/updated for: {account_meta.get('customer_name')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Insert Contracts

# COMMAND ----------

contracts = config.get('contracts', [])
print(f"Processing {len(contracts)} contract(s)...\n")

# Clear existing contracts before loading new ones
# This ensures only contracts from the current config file(s) exist
spark.sql(f"DELETE FROM {CATALOG}.{SCHEMA}.contracts WHERE 1=1")
print(f"Cleared existing contracts from {CATALOG}.{SCHEMA}.contracts")

for contract in contracts:
    # Resolve auto values
    contract_id = contract.get('contract_id')
    cloud_provider = actual_cloud_provider if contract.get('cloud_provider') == 'auto' else contract.get('cloud_provider')
    start_date = resolve_date(contract.get('start_date', 'auto'), is_start=True)
    end_date = resolve_date(contract.get('end_date', 'auto'), is_start=False)

    # Handle auto total_value - calculate optimal commitment from consumption data
    total_value_config = contract.get('total_value', 10000.00)
    if total_value_config == 'auto' or total_value_config == 'AUTO':
        print(f"\nCalculating optimal commitment for {contract_id}...")
        total_value = calculate_optimal_commitment(start_date, end_date)
    else:
        total_value = float(total_value_config)

    currency = contract.get('currency', 'USD')
    commitment_type = contract.get('commitment_type', 'SPEND')
    status = contract.get('status', 'ACTIVE')
    notes = contract.get('notes', '').replace("'", "''")  # Escape single quotes

    merge_sql = f"""
    MERGE INTO {CATALOG}.{SCHEMA}.contracts AS target
    USING (
      SELECT
        '{contract_id}' as contract_id,
        '{account_id}' as account_id,
        '{cloud_provider}' as cloud_provider,
        DATE '{start_date}' as start_date,
        DATE '{end_date}' as end_date,
        {total_value} as total_value,
        '{currency}' as currency,
        '{commitment_type}' as commitment_type,
        '{status}' as status,
        '{notes}' as notes,
        CURRENT_TIMESTAMP() as created_at,
        CURRENT_TIMESTAMP() as updated_at
    ) AS source
    ON target.contract_id = source.contract_id
    WHEN MATCHED THEN UPDATE SET
      account_id = source.account_id,
      cloud_provider = source.cloud_provider,
      start_date = source.start_date,
      end_date = source.end_date,
      total_value = source.total_value,
      currency = source.currency,
      commitment_type = source.commitment_type,
      status = source.status,
      notes = source.notes,
      updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT *
    """

    spark.sql(merge_sql)
    print(f"✓ Contract {contract_id}: ${total_value:,.2f} ({start_date} to {end_date})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Load Discount Tiers

# COMMAND ----------

def get_default_discount_tiers():
    """Return default discount tiers when no config file is found."""
    return {
        "discount_tiers": [
            {"tier_id": "DEFAULT_1Y", "tier_name": "Default - 1 Year", "min_commitment": 0, "max_commitment": None, "duration_years": 1, "discount_rate": 0.05, "notes": "Default tier"},
            {"tier_id": "DEFAULT_2Y", "tier_name": "Default - 2 Year", "min_commitment": 0, "max_commitment": None, "duration_years": 2, "discount_rate": 0.10, "notes": "Default tier"},
            {"tier_id": "DEFAULT_3Y", "tier_name": "Default - 3 Year", "min_commitment": 0, "max_commitment": None, "duration_years": 3, "discount_rate": 0.15, "notes": "Default tier"},
        ]
    }

# Load discount tiers configuration
print(f"\nLoading discount tiers from: {DISCOUNT_TIERS_FILE}")
try:
    discount_config = load_config(DISCOUNT_TIERS_FILE)
except Exception as e:
    print(f"  ✗ Could not load discount tiers config: {e}")
    print("  Using default discount tiers...")
    discount_config = get_default_discount_tiers()

discount_tiers = discount_config.get('discount_tiers', [])
print(f"  Found {len(discount_tiers)} discount tier(s)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Insert Discount Tiers

# COMMAND ----------

# Clear existing tiers that were loaded from config (keep manually added ones)
spark.sql(f"""
    DELETE FROM {CATALOG}.{SCHEMA}.discount_tiers
    WHERE tier_id LIKE 'TIER_%' OR tier_id LIKE 'DEFAULT_%'
""")
print(f"Cleared existing config-based discount tiers")

print(f"\nProcessing {len(discount_tiers)} discount tier(s)...")

for tier in discount_tiers:
    tier_id = tier.get('tier_id')
    tier_name = tier.get('tier_name', '').replace("'", "''")
    min_commitment = tier.get('min_commitment', 0)
    max_commitment = tier.get('max_commitment')
    duration_years = tier.get('duration_years', 1)
    discount_rate = tier.get('discount_rate', 0.05)
    cloud_provider = tier.get('cloud_provider')
    effective_date = tier.get('effective_date', '2024-01-01')
    expiration_date = tier.get('expiration_date')
    notes = tier.get('notes', '').replace("'", "''") if tier.get('notes') else ''

    # Handle NULL values for SQL
    max_commitment_sql = 'NULL' if max_commitment is None else str(max_commitment)
    cloud_provider_sql = 'NULL' if cloud_provider is None else f"'{cloud_provider}'"
    effective_date_sql = 'NULL' if effective_date is None else f"'{effective_date}'"
    expiration_date_sql = 'NULL' if expiration_date is None else f"'{expiration_date}'"

    insert_sql = f"""
    INSERT INTO {CATALOG}.{SCHEMA}.discount_tiers
    (tier_id, tier_name, min_commitment, max_commitment, duration_years,
     discount_rate, cloud_provider, effective_date, expiration_date, notes, created_at)
    VALUES (
        '{tier_id}',
        '{tier_name}',
        {min_commitment},
        {max_commitment_sql},
        {duration_years},
        {discount_rate},
        {cloud_provider_sql},
        {effective_date_sql},
        {expiration_date_sql},
        '{notes}',
        CURRENT_TIMESTAMP()
    )
    """

    spark.sql(insert_sql)
    discount_pct = int(discount_rate * 100)
    print(f"✓ Tier {tier_id}: {discount_pct}% for ${min_commitment:,.0f}+ / {duration_years}yr")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Verify Data

# COMMAND ----------

print("=" * 60)
print("SETUP COMPLETE")
print("=" * 60)

# Show account metadata
print("\n📋 Account Metadata:")
display(spark.sql(f"SELECT * FROM {CATALOG}.{SCHEMA}.account_metadata"))

# Show contracts
print("\n📄 Contracts:")
display(spark.sql(f"SELECT contract_id, cloud_provider, start_date, end_date, total_value, status, notes FROM {CATALOG}.{SCHEMA}.contracts ORDER BY contract_id"))

# Show discount tiers
print("\n💰 Discount Tiers:")
display(spark.sql(f"""
    SELECT
        tier_name,
        CONCAT('$', FORMAT_NUMBER(min_commitment, 0), ' - ',
               COALESCE(CONCAT('$', FORMAT_NUMBER(max_commitment, 0)), 'Unlimited')) as commitment_range,
        duration_years as years,
        CONCAT(CAST(discount_rate * 100 AS INT), '%') as discount
    FROM {CATALOG}.{SCHEMA}.discount_tiers
    ORDER BY min_commitment, duration_years
"""))

# Summary
account_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.account_metadata").collect()[0]['cnt']
contract_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.contracts").collect()[0]['cnt']
tier_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.discount_tiers").collect()[0]['cnt']

print(f"\n✅ Summary:")
print(f"   Accounts: {account_count}")
print(f"   Contracts: {contract_count}")
print(f"   Discount Tiers: {tier_count}")
print("=" * 60)
