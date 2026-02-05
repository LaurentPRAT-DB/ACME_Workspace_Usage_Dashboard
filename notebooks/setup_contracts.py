# Databricks notebook source
# MAGIC %md
# MAGIC # Contract Setup from Configuration
# MAGIC
# MAGIC This notebook loads contract data from `config/contracts.yml` and inserts it into the database.
# MAGIC
# MAGIC **Usage:**
# MAGIC - Edit `config/contracts.yml` to define your contracts
# MAGIC - Run this notebook (or the setup job) to load the data

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import yaml
from datetime import datetime, timedelta
from pyspark.sql import functions as F

# Configuration
CATALOG = "main"
SCHEMA = "account_monitoring_dev"
CONFIG_PATH = "../config/contracts.yml"

print(f"Contract Setup v1.0")
print(f"Target: {CATALOG}.{SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Configuration File

# COMMAND ----------

def load_config(config_path: str) -> dict:
    """Load contract configuration from YAML file."""
    import os

    # Try multiple paths (workspace vs local)
    paths_to_try = [
        config_path,
        "/Workspace/Users/" + spark.sql("SELECT current_user()").collect()[0][0] + "/account_monitor/files/config/contracts.yml",
        "config/contracts.yml",
        "./config/contracts.yml"
    ]

    for path in paths_to_try:
        try:
            # For workspace files
            if path.startswith("/Workspace"):
                content = dbutils.fs.head(f"file:{path}", 10000)
                config = yaml.safe_load(content)
                print(f"Loaded config from: {path}")
                return config
            else:
                # For bundled files, read via spark
                try:
                    with open(path, 'r') as f:
                        config = yaml.safe_load(f.read())
                        print(f"Loaded config from: {path}")
                        return config
                except FileNotFoundError:
                    continue
        except Exception as e:
            continue

    raise FileNotFoundError(f"Could not find contracts.yml in any of: {paths_to_try}")

# Load the configuration
try:
    config = load_config(CONFIG_PATH)
    print(f"\nConfiguration loaded successfully!")
    print(f"  Account: {config.get('account_metadata', {}).get('customer_name', 'N/A')}")
    print(f"  Contracts: {len(config.get('contracts', []))}")
except Exception as e:
    print(f"Error loading config: {e}")
    print("\nUsing default configuration...")
    config = {
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

for contract in contracts:
    # Resolve auto values
    contract_id = contract.get('contract_id')
    cloud_provider = actual_cloud_provider if contract.get('cloud_provider') == 'auto' else contract.get('cloud_provider')
    start_date = resolve_date(contract.get('start_date', 'auto'), is_start=True)
    end_date = resolve_date(contract.get('end_date', 'auto'), is_start=False)
    total_value = contract.get('total_value', 10000.00)
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
# MAGIC ## 6. Verify Data

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

# Summary
account_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.account_metadata").collect()[0]['cnt']
contract_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.contracts").collect()[0]['cnt']

print(f"\n✅ Summary:")
print(f"   Accounts: {account_count}")
print(f"   Contracts: {contract_count}")
print("=" * 60)
