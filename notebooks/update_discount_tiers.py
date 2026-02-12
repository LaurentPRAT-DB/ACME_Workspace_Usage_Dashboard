# Databricks notebook source
# MAGIC %md
# MAGIC # Update Discount Tiers (Lightweight)
# MAGIC
# MAGIC This notebook updates discount tiers using MERGE (incremental update) instead of DELETE+INSERT.
# MAGIC
# MAGIC **Usage:**
# MAGIC - Edit `config/discount_tiers.yml` to add/modify tiers
# MAGIC - Run this notebook to apply changes
# MAGIC - Optionally run What-If refresh to regenerate scenarios
# MAGIC
# MAGIC **Parameters:**
# MAGIC - `catalog`: Unity Catalog name
# MAGIC - `schema`: Schema name
# MAGIC - `discount_tiers_file`: Path to discount tiers YAML config

# COMMAND ----------

# Parameters
dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("schema", "account_monitoring_dev", "Schema")
dbutils.widgets.text("discount_tiers_file", "config/discount_tiers.yml", "Discount Tiers Config")

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip()
DISCOUNT_TIERS_FILE = dbutils.widgets.get("discount_tiers_file").strip()

print(f"Catalog: {CATALOG}")
print(f"Schema: {SCHEMA}")
print(f"Discount Tiers File: {DISCOUNT_TIERS_FILE}")

# COMMAND ----------

import yaml
import os
from datetime import datetime

def load_yaml_config(file_path):
    """Load YAML configuration file from workspace or repo"""
    try:
        # Try workspace path first
        workspace_path = f"/Workspace{file_path}" if not file_path.startswith("/Workspace") else file_path
        if os.path.exists(workspace_path):
            with open(workspace_path, 'r') as f:
                return yaml.safe_load(f)
    except Exception as e:
        print(f"  Workspace path not found: {e}")

    try:
        # Try relative path (for bundle deployments)
        bundle_base = "/Workspace/Users/" + spark.sql("SELECT current_user()").collect()[0][0]
        bundle_path = f"{bundle_base}/account_monitor/files/{file_path}"
        if os.path.exists(bundle_path):
            with open(bundle_path, 'r') as f:
                return yaml.safe_load(f)
    except Exception as e:
        print(f"  Bundle path not found: {e}")

    # Return empty config if not found
    print(f"  WARNING: Config file not found: {file_path}")
    return None

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Discount Tiers Configuration

# COMMAND ----------

# Load discount tiers from YAML
discount_config = load_yaml_config(DISCOUNT_TIERS_FILE)

if not discount_config:
    # Use default tiers if file not found
    print("Using default discount tiers configuration")
    discount_config = {
        "discount_tiers": [
            {"tier_id": "TIER_100K_1Y", "tier_name": "Standard - 1 Year", "min_commitment": 100000, "max_commitment": 249999, "duration_years": 1, "discount_rate": 0.10},
            {"tier_id": "TIER_100K_2Y", "tier_name": "Standard - 2 Year", "min_commitment": 100000, "max_commitment": 249999, "duration_years": 2, "discount_rate": 0.15},
            {"tier_id": "TIER_100K_3Y", "tier_name": "Standard - 3 Year", "min_commitment": 100000, "max_commitment": 249999, "duration_years": 3, "discount_rate": 0.18},
        ]
    }

discount_tiers = discount_config.get('discount_tiers', [])
print(f"Found {len(discount_tiers)} discount tier(s) in configuration")

# COMMAND ----------

# MAGIC %md
# MAGIC ## MERGE Discount Tiers (Incremental Update)

# COMMAND ----------

# Track statistics
stats = {
    "inserted": 0,
    "updated": 0,
    "unchanged": 0,
    "errors": 0
}

print(f"\nMerging {len(discount_tiers)} discount tier(s) into {CATALOG}.{SCHEMA}.discount_tiers...")

for tier in discount_tiers:
    tier_id = tier.get('tier_id', '')
    tier_name = tier.get('tier_name', '')
    min_commit = tier.get('min_commitment', 0)
    max_commit = tier.get('max_commitment')
    duration = tier.get('duration_years', 1)
    discount = tier.get('discount_rate', 0)
    cloud = tier.get('cloud_provider')
    effective = tier.get('effective_date')
    expiration = tier.get('expiration_date')
    notes = tier.get('notes', '')

    # Handle None values for SQL
    max_commit_sql = f"{max_commit}" if max_commit else "NULL"
    cloud_sql = f"'{cloud}'" if cloud else "NULL"
    effective_sql = f"'{effective}'" if effective else "NULL"
    expiration_sql = f"'{expiration}'" if expiration else "NULL"
    notes_sql = notes.replace("'", "''") if notes else ""

    try:
        merge_sql = f"""
        MERGE INTO {CATALOG}.{SCHEMA}.discount_tiers AS target
        USING (
            SELECT
                '{tier_id}' AS tier_id,
                '{tier_name}' AS tier_name,
                {min_commit} AS min_commitment,
                {max_commit_sql} AS max_commitment,
                {duration} AS duration_years,
                {discount} AS discount_rate,
                {cloud_sql} AS cloud_provider,
                {effective_sql} AS effective_date,
                {expiration_sql} AS expiration_date,
                '{notes_sql}' AS notes,
                CURRENT_TIMESTAMP() AS created_at
        ) AS source
        ON target.tier_id = source.tier_id
        WHEN MATCHED AND (
            target.tier_name != source.tier_name OR
            target.min_commitment != source.min_commitment OR
            COALESCE(target.max_commitment, -1) != COALESCE(source.max_commitment, -1) OR
            target.duration_years != source.duration_years OR
            target.discount_rate != source.discount_rate
        ) THEN UPDATE SET
            tier_name = source.tier_name,
            min_commitment = source.min_commitment,
            max_commitment = source.max_commitment,
            duration_years = source.duration_years,
            discount_rate = source.discount_rate,
            cloud_provider = source.cloud_provider,
            effective_date = source.effective_date,
            expiration_date = source.expiration_date,
            notes = source.notes,
            created_at = source.created_at
        WHEN NOT MATCHED THEN INSERT (
            tier_id, tier_name, min_commitment, max_commitment, duration_years,
            discount_rate, cloud_provider, effective_date, expiration_date, notes, created_at
        ) VALUES (
            source.tier_id, source.tier_name, source.min_commitment, source.max_commitment,
            source.duration_years, source.discount_rate, source.cloud_provider,
            source.effective_date, source.expiration_date, source.notes, source.created_at
        )
        """

        result = spark.sql(merge_sql)

        # Get merge metrics
        metrics = result.first()
        if metrics:
            rows_affected = metrics[0] if metrics[0] else 0
            if rows_affected > 0:
                stats["updated"] += 1
                print(f"  ✓ Updated: {tier_id}")
            else:
                stats["unchanged"] += 1
        else:
            stats["inserted"] += 1
            print(f"  ✓ Inserted: {tier_id}")

    except Exception as e:
        stats["errors"] += 1
        print(f"  ✗ Error with {tier_id}: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

# Print summary
print("\n" + "="*50)
print("DISCOUNT TIER UPDATE SUMMARY")
print("="*50)
print(f"  Total tiers in config: {len(discount_tiers)}")
print(f"  Inserted: {stats['inserted']}")
print(f"  Updated: {stats['updated']}")
print(f"  Unchanged: {stats['unchanged']}")
print(f"  Errors: {stats['errors']}")

# Verify final count
tier_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{SCHEMA}.discount_tiers").collect()[0]['cnt']
print(f"\nTotal tiers in database: {tier_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Display Current Tiers

# COMMAND ----------

# Show current discount tiers
display(spark.sql(f"""
    SELECT
        tier_id,
        tier_name,
        min_commitment,
        max_commitment,
        duration_years,
        ROUND(discount_rate * 100, 1) as discount_pct,
        notes
    FROM {CATALOG}.{SCHEMA}.discount_tiers
    ORDER BY min_commitment, duration_years
"""))

# COMMAND ----------

# Return success
result = {
    "status": "SUCCESS",
    "tiers_in_config": len(discount_tiers),
    "tiers_in_database": tier_count,
    "inserted": stats["inserted"],
    "updated": stats["updated"],
    "errors": stats["errors"]
}
print(f"\nResult: {result}")
dbutils.notebook.exit(str(result))
