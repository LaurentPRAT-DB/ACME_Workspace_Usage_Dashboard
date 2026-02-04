# Databricks notebook source
# MAGIC %md
# MAGIC # Contract & Account Metadata Management
# MAGIC ## CRUD Operations for Account Monitoring
# MAGIC
# MAGIC This notebook provides interactive CRUD (Create, Read, Update, Delete) operations for:
# MAGIC - `account_monitoring.contracts` - Contract tracking data
# MAGIC - `account_monitoring.account_metadata` - Account organizational information
# MAGIC
# MAGIC **Version:** 1.0.0
# MAGIC **Created:** 2026-02-04
# MAGIC
# MAGIC ### Quick Navigation
# MAGIC - [Contract Management](#contract-management)
# MAGIC - [Account Metadata Management](#account-metadata-management)
# MAGIC - [Utilities & Helpers](#utilities)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup & Configuration

# COMMAND ----------

from pyspark.sql import functions as F
from datetime import datetime, timedelta
import pandas as pd

# Configuration
CATALOG = "main"
SCHEMA = "account_monitoring_dev"
CONTRACTS_TABLE = f"{CATALOG}.{SCHEMA}.contracts"
METADATA_TABLE = f"{CATALOG}.{SCHEMA}.account_metadata"

print(f"📊 Contract Management CRUD Operations")
print(f"   Contracts Table: {CONTRACTS_TABLE}")
print(f"   Metadata Table: {METADATA_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Contract Management
# MAGIC <a id="contract-management"></a>
# MAGIC
# MAGIC Manage contract records for consumption tracking.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📖 READ - View All Contracts

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View all contracts with key details
# MAGIC SELECT
# MAGIC   contract_id,
# MAGIC   account_id,
# MAGIC   cloud_provider,
# MAGIC   start_date,
# MAGIC   end_date,
# MAGIC   DATEDIFF(end_date, start_date) as duration_days,
# MAGIC   DATEDIFF(CURRENT_DATE(), start_date) as days_elapsed,
# MAGIC   DATEDIFF(end_date, CURRENT_DATE()) as days_remaining,
# MAGIC   total_value,
# MAGIC   currency,
# MAGIC   commitment_type,
# MAGIC   status,
# MAGIC   created_at,
# MAGIC   updated_at
# MAGIC FROM main.account_monitoring_dev.contracts
# MAGIC ORDER BY start_date DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📖 READ - View Specific Contract
# MAGIC
# MAGIC **Instructions:** Modify the `contract_id` in the WHERE clause below.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View specific contract details
# MAGIC SELECT *
# MAGIC FROM main.account_monitoring_dev.contracts
# MAGIC WHERE contract_id = '1694992';

# COMMAND ----------

# MAGIC %md
# MAGIC ## ➕ CREATE - Add New Contract
# MAGIC
# MAGIC ### Option 1: Add Contract with Auto-Detected Account Info

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Auto-detect account_id and cloud from usage data
# MAGIC INSERT INTO main.account_monitoring_dev.contracts (
# MAGIC   contract_id,
# MAGIC   account_id,
# MAGIC   cloud_provider,
# MAGIC   start_date,
# MAGIC   end_date,
# MAGIC   total_value,
# MAGIC   currency,
# MAGIC   commitment_type,
# MAGIC   status,
# MAGIC   created_at,
# MAGIC   updated_at
# MAGIC )
# MAGIC SELECT
# MAGIC   'CONTRACT_' || CAST(UNIX_TIMESTAMP() AS STRING) as contract_id,  -- Generate unique ID
# MAGIC   account_id,
# MAGIC   cloud as cloud_provider,
# MAGIC   CURRENT_DATE() as start_date,
# MAGIC   DATE_ADD(CURRENT_DATE(), 365) as end_date,  -- 1 year contract
# MAGIC   5000.00 as total_value,  -- ⚠️ CHANGE THIS VALUE
# MAGIC   'USD' as currency,
# MAGIC   'SPEND' as commitment_type,
# MAGIC   'ACTIVE' as status,
# MAGIC   CURRENT_TIMESTAMP() as created_at,
# MAGIC   CURRENT_TIMESTAMP() as updated_at
# MAGIC FROM (
# MAGIC   SELECT account_id, cloud
# MAGIC   FROM system.billing.usage
# MAGIC   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
# MAGIC   GROUP BY account_id, cloud
# MAGIC   ORDER BY SUM(usage_quantity) DESC
# MAGIC   LIMIT 1
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ### Option 2: Add Contract with Specific Values
# MAGIC
# MAGIC **Instructions:** Replace the values in the INSERT statement below with your contract details.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insert contract with specific values
# MAGIC INSERT INTO main.account_monitoring_dev.contracts (
# MAGIC   contract_id,
# MAGIC   account_id,
# MAGIC   cloud_provider,
# MAGIC   start_date,
# MAGIC   end_date,
# MAGIC   total_value,
# MAGIC   currency,
# MAGIC   commitment_type,
# MAGIC   status,
# MAGIC   created_at,
# MAGIC   updated_at
# MAGIC )
# MAGIC VALUES (
# MAGIC   'CONTRACT_2026_001',           -- ⚠️ Change: Unique contract ID
# MAGIC   'your-account-id',             -- ⚠️ Change: Your account ID
# MAGIC   'AWS',                         -- ⚠️ Change: AWS, AZURE, or GCP
# MAGIC   '2026-01-01',                  -- ⚠️ Change: Start date
# MAGIC   '2027-01-01',                  -- ⚠️ Change: End date
# MAGIC   10000.00,                      -- ⚠️ Change: Total contract value
# MAGIC   'USD',                         -- Currency (USD, EUR, etc.)
# MAGIC   'SPEND',                       -- SPEND or DBU
# MAGIC   'ACTIVE',                      -- ACTIVE, EXPIRED, or PENDING
# MAGIC   CURRENT_TIMESTAMP(),
# MAGIC   CURRENT_TIMESTAMP()
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ### Option 3: Python - Add Multiple Contracts

# COMMAND ----------

# Add multiple contracts using Python
contracts_data = [
    {
        "contract_id": "CONTRACT_2026_Q1",
        "account_id": "your-account-id",  # ⚠️ Change this
        "cloud_provider": "AWS",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "total_value": 2500.00,
        "currency": "USD",
        "commitment_type": "SPEND",
        "status": "ACTIVE"
    },
    {
        "contract_id": "CONTRACT_2026_Q2",
        "account_id": "your-account-id",  # ⚠️ Change this
        "cloud_provider": "AZURE",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
        "total_value": 3000.00,
        "currency": "USD",
        "commitment_type": "DBU",
        "status": "PENDING"
    }
]

# Convert to DataFrame and add timestamps
from datetime import datetime
df = spark.createDataFrame(contracts_data)
df = df.withColumn("created_at", F.current_timestamp())
df = df.withColumn("updated_at", F.current_timestamp())

# Uncomment to insert
# df.write.mode("append").saveAsTable(CONTRACTS_TABLE)
# print(f"✅ Added {len(contracts_data)} contracts")

print("⚠️ Uncomment the write statement above to execute")
df.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✏️ UPDATE - Modify Contract

# COMMAND ----------

# MAGIC %md
# MAGIC ### Update Contract Status

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Update contract status
# MAGIC UPDATE main.account_monitoring_dev.contracts
# MAGIC SET
# MAGIC   status = 'EXPIRED',  -- ⚠️ Change: ACTIVE, EXPIRED, or PENDING
# MAGIC   updated_at = CURRENT_TIMESTAMP()
# MAGIC WHERE contract_id = '1694992';  -- ⚠️ Change: Your contract ID

# COMMAND ----------

# MAGIC %md
# MAGIC ### Update Contract Value

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Update contract total value
# MAGIC UPDATE main.account_monitoring_dev.contracts
# MAGIC SET
# MAGIC   total_value = 5000.00,  -- ⚠️ Change: New value
# MAGIC   updated_at = CURRENT_TIMESTAMP()
# MAGIC WHERE contract_id = '1694992';  -- ⚠️ Change: Your contract ID

# COMMAND ----------

# MAGIC %md
# MAGIC ### Update Contract Dates

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Extend contract end date
# MAGIC UPDATE main.account_monitoring_dev.contracts
# MAGIC SET
# MAGIC   end_date = DATE_ADD(end_date, 90),  -- Extend by 90 days
# MAGIC   updated_at = CURRENT_TIMESTAMP()
# MAGIC WHERE contract_id = '1694992';  -- ⚠️ Change: Your contract ID

# COMMAND ----------

# MAGIC %md
# MAGIC ### Python - Bulk Update Contracts

# COMMAND ----------

# Bulk update contract statuses based on end date
from pyspark.sql.functions import when, col, current_timestamp

# Read contracts
contracts_df = spark.table(CONTRACTS_TABLE)

# Update status based on end date
updated_df = contracts_df.withColumn(
    "status",
    when(col("end_date") < F.current_date(), "EXPIRED")
    .when(col("start_date") > F.current_date(), "PENDING")
    .otherwise("ACTIVE")
).withColumn("updated_at", current_timestamp())

# Show changes (don't save yet)
print("📊 Contracts that would be updated:")
contracts_df.alias("old").join(
    updated_df.alias("new"),
    "contract_id"
).filter(
    col("old.status") != col("new.status")
).select(
    "contract_id",
    col("old.status").alias("old_status"),
    col("new.status").alias("new_status"),
    "end_date"
).show()

# Uncomment to execute update
# updated_df.write.mode("overwrite").saveAsTable(CONTRACTS_TABLE)
# print("✅ Contracts updated")

print("⚠️ Uncomment the write statement above to execute")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ❌ DELETE - Remove Contract

# COMMAND ----------

# MAGIC %md
# MAGIC ### Delete Specific Contract

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Delete a specific contract
# MAGIC -- ⚠️ WARNING: This permanently removes the contract
# MAGIC DELETE FROM main.account_monitoring_dev.contracts
# MAGIC WHERE contract_id = 'CONTRACT_2026_001';  -- ⚠️ Change: Contract ID to delete

# COMMAND ----------

# MAGIC %md
# MAGIC ### Delete Expired Contracts

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Delete all expired contracts
# MAGIC -- ⚠️ WARNING: This permanently removes ALL expired contracts
# MAGIC DELETE FROM main.account_monitoring_dev.contracts
# MAGIC WHERE status = 'EXPIRED'
# MAGIC   AND end_date < DATE_SUB(CURRENT_DATE(), 365);  -- Expired over 1 year ago

# COMMAND ----------

# MAGIC %md
# MAGIC ### Python - Conditional Delete

# COMMAND ----------

# Delete contracts matching conditions
def delete_contracts(condition_sql: str, preview_only: bool = True):
    """
    Delete contracts based on SQL condition

    Args:
        condition_sql: WHERE clause condition (e.g., "status = 'EXPIRED'")
        preview_only: If True, only show what would be deleted
    """
    # Preview what would be deleted
    preview_df = spark.sql(f"""
        SELECT * FROM {CONTRACTS_TABLE}
        WHERE {condition_sql}
    """)

    count = preview_df.count()
    print(f"📊 {count} contract(s) match the condition:")
    preview_df.show()

    if not preview_only and count > 0:
        spark.sql(f"""
            DELETE FROM {CONTRACTS_TABLE}
            WHERE {condition_sql}
        """)
        print(f"✅ Deleted {count} contract(s)")
    else:
        print("⚠️ Set preview_only=False to execute deletion")

# Example: Preview deletion of pending contracts
delete_contracts("status = 'PENDING'", preview_only=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Account Metadata Management
# MAGIC <a id="account-metadata-management"></a>
# MAGIC
# MAGIC Manage account organizational information and team assignments.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📖 READ - View All Account Metadata

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View all account metadata
# MAGIC SELECT
# MAGIC   account_id,
# MAGIC   customer_name,
# MAGIC   salesforce_id,
# MAGIC   business_unit_l0,
# MAGIC   business_unit_l1,
# MAGIC   business_unit_l2,
# MAGIC   business_unit_l3,
# MAGIC   account_executive,
# MAGIC   solutions_architect,
# MAGIC   delivery_solutions_architect,
# MAGIC   created_at,
# MAGIC   updated_at
# MAGIC FROM main.account_monitoring_dev.account_metadata
# MAGIC ORDER BY customer_name;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📖 READ - View Specific Account

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View specific account metadata
# MAGIC SELECT *
# MAGIC FROM main.account_monitoring_dev.account_metadata
# MAGIC WHERE customer_name LIKE '%Sample%';  -- ⚠️ Change: Search criteria

# COMMAND ----------

# MAGIC %md
# MAGIC ## ➕ CREATE - Add New Account Metadata

# COMMAND ----------

# MAGIC %md
# MAGIC ### Option 1: Add with Auto-Detected Account ID

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Auto-detect account_id from usage data
# MAGIC INSERT INTO main.account_monitoring_dev.account_metadata (
# MAGIC   account_id,
# MAGIC   customer_name,
# MAGIC   salesforce_id,
# MAGIC   business_unit_l0,
# MAGIC   business_unit_l1,
# MAGIC   business_unit_l2,
# MAGIC   business_unit_l3,
# MAGIC   account_executive,
# MAGIC   solutions_architect,
# MAGIC   delivery_solutions_architect,
# MAGIC   created_at,
# MAGIC   updated_at
# MAGIC )
# MAGIC SELECT
# MAGIC   account_id,
# MAGIC   'My Company Inc.' as customer_name,           -- ⚠️ Change
# MAGIC   'SF_ID_12345' as salesforce_id,               -- ⚠️ Change
# MAGIC   'AMER' as business_unit_l0,                   -- ⚠️ Change
# MAGIC   'East' as business_unit_l1,                   -- ⚠️ Change
# MAGIC   'New York' as business_unit_l2,               -- ⚠️ Change
# MAGIC   'Enterprise' as business_unit_l3,             -- ⚠️ Change
# MAGIC   'Alice Johnson' as account_executive,         -- ⚠️ Change
# MAGIC   'Bob Smith' as solutions_architect,           -- ⚠️ Change
# MAGIC   'Carol Davis' as delivery_solutions_architect,-- ⚠️ Change
# MAGIC   CURRENT_TIMESTAMP() as created_at,
# MAGIC   CURRENT_TIMESTAMP() as updated_at
# MAGIC FROM (
# MAGIC   SELECT DISTINCT account_id
# MAGIC   FROM system.billing.usage
# MAGIC   WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
# MAGIC   LIMIT 1
# MAGIC )
# MAGIC WHERE account_id NOT IN (
# MAGIC   SELECT account_id FROM main.account_monitoring_dev.account_metadata
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ### Option 2: Add with Specific Values

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insert account metadata with specific values
# MAGIC INSERT INTO main.account_monitoring_dev.account_metadata (
# MAGIC   account_id,
# MAGIC   customer_name,
# MAGIC   salesforce_id,
# MAGIC   business_unit_l0,
# MAGIC   business_unit_l1,
# MAGIC   business_unit_l2,
# MAGIC   business_unit_l3,
# MAGIC   account_executive,
# MAGIC   solutions_architect,
# MAGIC   delivery_solutions_architect,
# MAGIC   created_at,
# MAGIC   updated_at
# MAGIC )
# MAGIC VALUES (
# MAGIC   'account-12345',                     -- ⚠️ Change: Account ID
# MAGIC   'Acme Corporation',                  -- ⚠️ Change: Customer name
# MAGIC   '0014N00001ABCDEFG',                 -- ⚠️ Change: Salesforce ID
# MAGIC   'EMEA',                              -- ⚠️ Change: Region
# MAGIC   'UK',                                -- ⚠️ Change: Country/Area
# MAGIC   'London',                            -- ⚠️ Change: City/Office
# MAGIC   'Financial Services',                -- ⚠️ Change: Industry/Segment
# MAGIC   'David Wilson',                      -- ⚠️ Change: AE name
# MAGIC   'Emma Thompson',                     -- ⚠️ Change: SA name
# MAGIC   'Frank Miller',                      -- ⚠️ Change: DSA name
# MAGIC   CURRENT_TIMESTAMP(),
# MAGIC   CURRENT_TIMESTAMP()
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ### Option 3: Python - Add Multiple Accounts

# COMMAND ----------

# Add multiple account metadata records
accounts_data = [
    {
        "account_id": "account-001",
        "customer_name": "TechCorp Industries",
        "salesforce_id": "0014N00001XYZ123",
        "business_unit_l0": "AMER",
        "business_unit_l1": "West",
        "business_unit_l2": "San Francisco",
        "business_unit_l3": "Technology",
        "account_executive": "Sarah Johnson",
        "solutions_architect": "Mike Chen",
        "delivery_solutions_architect": "Lisa Wang"
    },
    {
        "account_id": "account-002",
        "customer_name": "Global Finance Ltd",
        "salesforce_id": "0014N00001ABC789",
        "business_unit_l0": "EMEA",
        "business_unit_l1": "Germany",
        "business_unit_l2": "Frankfurt",
        "business_unit_l3": "Financial Services",
        "account_executive": "Hans Schmidt",
        "solutions_architect": "Anna Mueller",
        "delivery_solutions_architect": "Klaus Weber"
    }
]

# Convert to DataFrame and add timestamps
df = spark.createDataFrame(accounts_data)
df = df.withColumn("created_at", F.current_timestamp())
df = df.withColumn("updated_at", F.current_timestamp())

# Uncomment to insert
# df.write.mode("append").saveAsTable(METADATA_TABLE)
# print(f"✅ Added {len(accounts_data)} account metadata records")

print("⚠️ Uncomment the write statement above to execute")
df.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✏️ UPDATE - Modify Account Metadata

# COMMAND ----------

# MAGIC %md
# MAGIC ### Update Team Members

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Update team members for an account
# MAGIC UPDATE main.account_monitoring_dev.account_metadata
# MAGIC SET
# MAGIC   account_executive = 'New AE Name',              -- ⚠️ Change
# MAGIC   solutions_architect = 'New SA Name',            -- ⚠️ Change
# MAGIC   delivery_solutions_architect = 'New DSA Name',  -- ⚠️ Change
# MAGIC   updated_at = CURRENT_TIMESTAMP()
# MAGIC WHERE customer_name = 'Sample Customer Inc.';     -- ⚠️ Change: Customer to update

# COMMAND ----------

# MAGIC %md
# MAGIC ### Update Business Unit

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Update business unit hierarchy
# MAGIC UPDATE main.account_monitoring_dev.account_metadata
# MAGIC SET
# MAGIC   business_unit_l0 = 'APAC',           -- ⚠️ Change
# MAGIC   business_unit_l1 = 'Japan',          -- ⚠️ Change
# MAGIC   business_unit_l2 = 'Tokyo',          -- ⚠️ Change
# MAGIC   business_unit_l3 = 'Manufacturing',  -- ⚠️ Change
# MAGIC   updated_at = CURRENT_TIMESTAMP()
# MAGIC WHERE account_id = 'your-account-id';  -- ⚠️ Change

# COMMAND ----------

# MAGIC %md
# MAGIC ### Update Salesforce ID

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Update Salesforce ID
# MAGIC UPDATE main.account_monitoring_dev.account_metadata
# MAGIC SET
# MAGIC   salesforce_id = '0014N00001NEWSFID',  -- ⚠️ Change
# MAGIC   updated_at = CURRENT_TIMESTAMP()
# MAGIC WHERE customer_name = 'Sample Customer Inc.';  -- ⚠️ Change

# COMMAND ----------

# MAGIC %md
# MAGIC ### Python - Bulk Update Team Assignments

# COMMAND ----------

# Bulk update team assignments based on business unit
updates = {
    "AMER": {
        "account_executive": "John Doe - AMER Lead",
        "solutions_architect": "Jane Smith - AMER SA"
    },
    "EMEA": {
        "account_executive": "Hans Mueller - EMEA Lead",
        "solutions_architect": "Sophie Dubois - EMEA SA"
    },
    "APAC": {
        "account_executive": "Yuki Tanaka - APAC Lead",
        "solutions_architect": "Wei Zhang - APAC SA"
    }
}

# Show what would be updated
metadata_df = spark.table(METADATA_TABLE)
print("📊 Accounts that would be updated:")

for region, team in updates.items():
    count = metadata_df.filter(col("business_unit_l0") == region).count()
    print(f"  {region}: {count} accounts → AE: {team['account_executive']}, SA: {team['solutions_architect']}")

# Uncomment to execute update
# for region, team in updates.items():
#     spark.sql(f"""
#         UPDATE {METADATA_TABLE}
#         SET
#             account_executive = '{team['account_executive']}',
#             solutions_architect = '{team['solutions_architect']}',
#             updated_at = CURRENT_TIMESTAMP()
#         WHERE business_unit_l0 = '{region}'
#     """)
# print("✅ Team assignments updated")

print("⚠️ Uncomment the update statements above to execute")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ❌ DELETE - Remove Account Metadata

# COMMAND ----------

# MAGIC %md
# MAGIC ### Delete Specific Account

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Delete specific account metadata
# MAGIC -- ⚠️ WARNING: This permanently removes the account metadata
# MAGIC DELETE FROM main.account_monitoring_dev.account_metadata
# MAGIC WHERE account_id = 'account-to-delete';  -- ⚠️ Change

# COMMAND ----------

# MAGIC %md
# MAGIC ### Delete Accounts Without Contracts

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Delete account metadata for accounts with no contracts
# MAGIC DELETE FROM main.account_monitoring_dev.account_metadata
# MAGIC WHERE account_id NOT IN (
# MAGIC   SELECT DISTINCT account_id
# MAGIC   FROM main.account_monitoring_dev.contracts
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC # Utilities & Helpers
# MAGIC <a id="utilities"></a>

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 View Contract-Account Join

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View contracts with associated account metadata
# MAGIC SELECT
# MAGIC   c.contract_id,
# MAGIC   c.account_id,
# MAGIC   am.customer_name,
# MAGIC   am.salesforce_id,
# MAGIC   c.cloud_provider,
# MAGIC   c.start_date,
# MAGIC   c.end_date,
# MAGIC   c.total_value,
# MAGIC   c.status,
# MAGIC   am.account_executive,
# MAGIC   am.solutions_architect,
# MAGIC   CONCAT_WS(' > ', am.business_unit_l0, am.business_unit_l1, am.business_unit_l2) as business_unit
# MAGIC FROM main.account_monitoring_dev.contracts c
# MAGIC LEFT JOIN main.account_monitoring_dev.account_metadata am
# MAGIC   ON c.account_id = am.account_id
# MAGIC ORDER BY c.start_date DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Summary Statistics

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Summary statistics
# MAGIC SELECT
# MAGIC   'Contracts' as entity,
# MAGIC   COUNT(*) as total_records,
# MAGIC   COUNT(DISTINCT account_id) as unique_accounts,
# MAGIC   SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_count,
# MAGIC   SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) as expired_count,
# MAGIC   SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending_count,
# MAGIC   SUM(total_value) as total_contract_value
# MAGIC FROM main.account_monitoring_dev.contracts
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Account Metadata' as entity,
# MAGIC   COUNT(*) as total_records,
# MAGIC   COUNT(DISTINCT account_id) as unique_accounts,
# MAGIC   COUNT(DISTINCT business_unit_l0) as regions,
# MAGIC   COUNT(DISTINCT account_executive) as unique_aes,
# MAGIC   COUNT(DISTINCT solutions_architect) as unique_sas,
# MAGIC   NULL as total_contract_value
# MAGIC FROM main.account_monitoring_dev.account_metadata;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔄 Refresh Contract Burndown Data
# MAGIC
# MAGIC After making changes to contracts, refresh the derived tables.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Trigger refresh of contract_burndown table
# MAGIC -- This should be run after modifying contracts
# MAGIC REFRESH TABLE main.account_monitoring_dev.contract_burndown;
# MAGIC REFRESH TABLE main.account_monitoring_dev.contract_burndown_summary;
# MAGIC
# MAGIC SELECT '✅ Burndown tables refreshed' as status;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧹 Data Validation

# COMMAND ----------

# Data validation checks
def validate_data():
    """Run validation checks on contracts and metadata"""

    print("🔍 Running data validation checks...\n")

    # Check 1: Orphaned contracts (no metadata)
    orphaned = spark.sql("""
        SELECT COUNT(*) as count
        FROM main.account_monitoring_dev.contracts c
        LEFT JOIN main.account_monitoring_dev.account_metadata am
          ON c.account_id = am.account_id
        WHERE am.account_id IS NULL
    """).collect()[0][0]

    if orphaned > 0:
        print(f"⚠️  Found {orphaned} contract(s) without account metadata")
    else:
        print("✅ All contracts have associated metadata")

    # Check 2: Invalid date ranges
    invalid_dates = spark.sql("""
        SELECT COUNT(*) as count
        FROM main.account_monitoring_dev.contracts
        WHERE end_date <= start_date
    """).collect()[0][0]

    if invalid_dates > 0:
        print(f"⚠️  Found {invalid_dates} contract(s) with invalid date ranges")
    else:
        print("✅ All contracts have valid date ranges")

    # Check 3: Duplicate contract IDs
    duplicates = spark.sql("""
        SELECT contract_id, COUNT(*) as count
        FROM main.account_monitoring_dev.contracts
        GROUP BY contract_id
        HAVING COUNT(*) > 1
    """).count()

    if duplicates > 0:
        print(f"⚠️  Found {duplicates} duplicate contract ID(s)")
    else:
        print("✅ All contract IDs are unique")

    # Check 4: Missing required fields
    missing_fields = spark.sql("""
        SELECT COUNT(*) as count
        FROM main.account_monitoring_dev.account_metadata
        WHERE customer_name IS NULL
           OR account_executive IS NULL
           OR solutions_architect IS NULL
    """).collect()[0][0]

    if missing_fields > 0:
        print(f"⚠️  Found {missing_fields} metadata record(s) with missing required fields")
    else:
        print("✅ All metadata records have required fields")

    print("\n✅ Validation complete")

# Run validation
validate_data()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📤 Export to CSV

# COMMAND ----------

# Export contracts and metadata to CSV files
def export_to_csv():
    """Export tables to CSV files"""

    # Export contracts
    contracts_df = spark.table(CONTRACTS_TABLE).toPandas()
    contracts_df.to_csv("/dbfs/tmp/contracts_export.csv", index=False)
    print(f"✅ Exported {len(contracts_df)} contracts to /dbfs/tmp/contracts_export.csv")

    # Export metadata
    metadata_df = spark.table(METADATA_TABLE).toPandas()
    metadata_df.to_csv("/dbfs/tmp/account_metadata_export.csv", index=False)
    print(f"✅ Exported {len(metadata_df)} metadata records to /dbfs/tmp/account_metadata_export.csv")

    print("\n📥 Download files from:")
    print("   /dbfs/tmp/contracts_export.csv")
    print("   /dbfs/tmp/account_metadata_export.csv")

# Uncomment to export
# export_to_csv()
print("⚠️ Uncomment the export_to_csv() call above to execute")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 📝 Notes
# MAGIC
# MAGIC ### Important Reminders
# MAGIC - ⚠️ Always preview changes before executing DELETE or bulk UPDATE operations
# MAGIC - 🔄 Refresh derived tables after making changes to contracts
# MAGIC - 💾 Run data validation after bulk operations
# MAGIC - 📊 Check the dashboard after changes to verify data integrity
# MAGIC
# MAGIC ### Table Relationships
# MAGIC ```
# MAGIC account_monitoring.contracts
# MAGIC     └─ account_id ──┐
# MAGIC                     ├── JOIN
# MAGIC account_monitoring.account_metadata
# MAGIC     └─ account_id ──┘
# MAGIC ```
# MAGIC
# MAGIC ### Next Steps
# MAGIC 1. After modifying contracts, refresh the dashboard
# MAGIC 2. Run validation checks to ensure data integrity
# MAGIC 3. Review contract burndown charts to verify changes
