"""
Databricks Account Monitor - Unity Catalog Setup Script
Automates the creation of Unity Catalog tables and initial data population
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import *
import sys
from datetime import datetime, timedelta

# Configuration
DEFAULT_CATALOG = "main"  # Change this to your catalog name
SCHEMA_NAME = "account_monitoring"

def set_catalog(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Set the current catalog"""
    print(f"Setting catalog to: {catalog}")
    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f'USE CATALOG {catalog}'
        })
        print(f"✓ Using catalog: {catalog}")
        return True
    except Exception as e:
        print(f"⚠ Error setting catalog: {e}")
        return False


def create_schema(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Create the account_monitoring schema in Unity Catalog"""
    print(f"\nCreating schema: {catalog}.{SCHEMA_NAME}")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f"""
                CREATE SCHEMA IF NOT EXISTS {catalog}.{SCHEMA_NAME}
                COMMENT 'Account monitoring and cost tracking using system tables'
            """
        })
        print(f"✓ Schema created: {catalog}.{SCHEMA_NAME}")
    except Exception as e:
        print(f"⚠ Error creating schema: {e}")
        return False

    return True


def create_contracts_table(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Create the contracts tracking table"""
    print(f"\nCreating table: {catalog}.{SCHEMA_NAME}.contracts")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f"""
                CREATE TABLE IF NOT EXISTS {catalog}.{SCHEMA_NAME}.contracts (
                  contract_id STRING NOT NULL COMMENT 'Unique contract identifier',
                  account_id STRING NOT NULL COMMENT 'Databricks account ID',
                  cloud_provider STRING NOT NULL COMMENT 'Cloud provider: aws, azure, gcp',
                  start_date DATE NOT NULL COMMENT 'Contract start date',
                  end_date DATE NOT NULL COMMENT 'Contract end date',
                  total_value DECIMAL(18,2) NOT NULL COMMENT 'Total contract value',
                  currency STRING DEFAULT 'USD' COMMENT 'Currency code (USD, EUR, etc.)',
                  commitment_type STRING COMMENT 'DBU or SPEND commitment',
                  status STRING DEFAULT 'ACTIVE' COMMENT 'ACTIVE, EXPIRED, or PENDING',
                  notes STRING COMMENT 'Additional notes',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Record creation timestamp',
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Record update timestamp',
                  CONSTRAINT pk_contracts PRIMARY KEY (contract_id)
                )
                USING DELTA
                COMMENT 'Contract tracking for consumption monitoring'
                TBLPROPERTIES (
                  'delta.feature.allowColumnDefaults' = 'supported',
                  'delta.enableChangeDataFeed' = 'true',
                  'delta.autoOptimize.optimizeWrite' = 'true',
                  'delta.autoOptimize.autoCompact' = 'true'
                )
            """
        })
        print(f"✓ Contracts table created successfully")
    except Exception as e:
        print(f"⚠ Error creating contracts table: {e}")
        return False

    return True


def create_account_metadata_table(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Create the account metadata table"""
    print(f"\nCreating table: {catalog}.{SCHEMA_NAME}.account_metadata")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f"""
                CREATE TABLE IF NOT EXISTS {catalog}.{SCHEMA_NAME}.account_metadata (
                  account_id STRING NOT NULL COMMENT 'Databricks account ID',
                  customer_name STRING NOT NULL COMMENT 'Customer display name',
                  salesforce_id STRING COMMENT 'Salesforce account ID',
                  business_unit_l0 STRING COMMENT 'Top-level business unit',
                  business_unit_l1 STRING COMMENT 'Second-level business unit',
                  business_unit_l2 STRING COMMENT 'Third-level business unit',
                  business_unit_l3 STRING COMMENT 'Fourth-level business unit',
                  account_executive STRING COMMENT 'Account Executive name',
                  solutions_architect STRING COMMENT 'Solutions Architect name',
                  delivery_solutions_architect STRING COMMENT 'Delivery Solutions Architect name',
                  region STRING COMMENT 'Geographic region',
                  industry STRING COMMENT 'Customer industry',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Record creation timestamp',
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Record update timestamp',
                  CONSTRAINT pk_account_metadata PRIMARY KEY (account_id)
                )
                USING DELTA
                COMMENT 'Account metadata and organizational information'
                TBLPROPERTIES (
                  'delta.feature.allowColumnDefaults' = 'supported',
                  'delta.enableChangeDataFeed' = 'true',
                  'delta.autoOptimize.optimizeWrite' = 'true',
                  'delta.autoOptimize.autoCompact' = 'true'
                )
            """
        })
        print(f"✓ Account metadata table created successfully")
    except Exception as e:
        print(f"⚠ Error creating account metadata table: {e}")
        return False

    return True


def create_dashboard_data_table(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Create the dashboard data aggregation table"""
    print(f"\nCreating table: {catalog}.{SCHEMA_NAME}.dashboard_data")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f"""
                CREATE TABLE IF NOT EXISTS {catalog}.{SCHEMA_NAME}.dashboard_data (
                  usage_date DATE NOT NULL,
                  account_id STRING NOT NULL,
                  customer_name STRING,
                  salesforce_id STRING,
                  business_unit_l0 STRING,
                  business_unit_l1 STRING,
                  business_unit_l2 STRING,
                  business_unit_l3 STRING,
                  account_executive STRING,
                  solutions_architect STRING,
                  workspace_id STRING NOT NULL,
                  cloud_provider STRING NOT NULL,
                  sku_name STRING NOT NULL,
                  usage_unit STRING,
                  usage_quantity DECIMAL(18,6),
                  price_per_unit DECIMAL(20,10),
                  list_cost DECIMAL(18,2),
                  actual_cost DECIMAL(18,2),
                  product_category STRING,
                  job_id STRING,
                  job_name STRING,
                  warehouse_id STRING,
                  cluster_id STRING,
                  run_as STRING,
                  custom_tags MAP<STRING, STRING>,
                  updated_at TIMESTAMP
                )
                USING DELTA
                PARTITIONED BY (usage_date)
                COMMENT 'Pre-aggregated dashboard data for Lakeview'
                TBLPROPERTIES (
                  'delta.enableChangeDataFeed' = 'true',
                  'delta.autoOptimize.optimizeWrite' = 'true',
                  'delta.autoOptimize.autoCompact' = 'true'
                )
            """
        })
        print(f"✓ Dashboard data table created successfully")
    except Exception as e:
        print(f"⚠ Error creating dashboard data table: {e}")
        return False

    return True


def get_default_warehouse(w: WorkspaceClient):
    """Get the first available SQL warehouse"""
    warehouses = list(w.warehouses.list())
    if not warehouses:
        raise Exception("No SQL warehouses found. Please create one first.")
    return warehouses[0].id


def insert_sample_data(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Insert sample data for testing"""
    print("\n" + "="*70)
    print("Inserting sample data...")
    print("="*70)

    # Get account_id from system tables
    try:
        result = w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': 'SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1'
        })
        # Note: Actual account_id extraction would need proper response parsing
        print("\n⚠ Please note: You need to update the sample data with your actual account_id")
        print("   Query system.billing.usage to find your account_id")
    except Exception as e:
        print(f"\n⚠ Could not auto-detect account_id: {e}")

    # Sample contract data
    print("\nInserting sample contracts...")
    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f"""
                MERGE INTO {catalog}.{SCHEMA_NAME}.contracts AS target
                USING (
                  SELECT '1694992' as contract_id, 'your-account-id' as account_id,
                         'aws' as cloud_provider, DATE'2024-11-10' as start_date,
                         DATE'2026-01-29' as end_date, 300000.00 as total_value,
                         'USD' as currency, 'SPEND' as commitment_type, 'ACTIVE' as status,
                         'First AWS contract' as notes,
                         CURRENT_TIMESTAMP() as created_at, CURRENT_TIMESTAMP() as updated_at
                  UNION ALL
                  SELECT '2209701', 'your-account-id', 'aws', DATE'2026-01-30',
                         DATE'2029-01-29', 1000000.00, 'USD', 'SPEND', 'ACTIVE',
                         'Second AWS contract', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
                ) AS source
                ON target.contract_id = source.contract_id
                WHEN NOT MATCHED THEN INSERT *
            """
        })
        print("✓ Sample contracts inserted (or already exist)")
    except Exception as e:
        print(f"⚠ Error inserting contracts: {e}")

    # Sample account metadata
    print("\nInserting sample account metadata...")
    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': f"""
                MERGE INTO {catalog}.{SCHEMA_NAME}.account_metadata AS target
                USING (
                  SELECT 'your-account-id' as account_id,
                         'Sample Customer Inc' as customer_name,
                         '0014N00001HEcQAG' as salesforce_id,
                         'AMER' as business_unit_l0,
                         'West' as business_unit_l1,
                         'California' as business_unit_l2,
                         'Enterprise' as business_unit_l3,
                         'John Doe' as account_executive,
                         'Jane Smith' as solutions_architect,
                         'Bob Johnson' as delivery_solutions_architect,
                         'US-West' as region,
                         'Technology' as industry,
                         CURRENT_TIMESTAMP() as created_at,
                         CURRENT_TIMESTAMP() as updated_at
                ) AS source
                ON target.account_id = source.account_id
                WHEN NOT MATCHED THEN INSERT *
            """
        })
        print("✓ Sample account metadata inserted (or already exists)")
    except Exception as e:
        print(f"⚠ Error inserting metadata: {e}")

    print("\n" + "!"*70)
    print("IMPORTANT: Update 'your-account-id' with your actual account ID")
    print("Run this query to find it: SELECT DISTINCT account_id FROM system.billing.usage")
    print("!"*70)


def verify_system_tables_access(w: WorkspaceClient):
    """Verify access to system tables"""
    print("\n" + "="*70)
    print("Verifying access to system tables...")
    print("="*70)

    try:
        result = w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                SELECT
                  COUNT(*) as record_count,
                  MAX(usage_date) as latest_date,
                  COUNT(DISTINCT workspace_id) as workspace_count
                FROM system.billing.usage
                WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
                  AND record_type = 'ORIGINAL'
            """
        })
        print("✓ System tables access verified")
        print("  Tables available:")
        print("    - system.billing.usage")
        print("    - system.billing.list_prices")
        return True
    except Exception as e:
        print(f"✗ Cannot access system tables: {e}")
        print("\nPlease ensure:")
        print("  1. System tables are enabled for your account")
        print("  2. You have the necessary permissions")
        print("  3. Contact Databricks support if needed")
        return False


def create_sample_queries(w: WorkspaceClient, catalog: str = DEFAULT_CATALOG):
    """Create sample queries for testing"""
    print("\n" + "="*70)
    print("Sample Queries You Can Run")
    print("="*70)

    queries = {
        "Check Data Freshness": f"""
            SELECT MAX(usage_date) as latest_date,
                   DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind
            FROM system.billing.usage
        """,
        "Yesterday's Total Cost": f"""
            SELECT
              u.cloud,
              ROUND(SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))), 2) as cost
            FROM system.billing.usage u
            LEFT JOIN system.billing.list_prices lp
              ON u.sku_name = lp.sku_name
              AND u.cloud = lp.cloud
              AND u.usage_unit = lp.usage_unit
              AND u.usage_end_time >= lp.price_start_time
              AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
            WHERE u.usage_date = CURRENT_DATE() - 1
              AND u.record_type = 'ORIGINAL'
            GROUP BY u.cloud
        """,
        "View Contracts": f"""
            SELECT * FROM {catalog}.{SCHEMA_NAME}.contracts
        """,
        "View Account Metadata": f"""
            SELECT * FROM {catalog}.{SCHEMA_NAME}.account_metadata
        """
    }

    for name, query in queries.items():
        print(f"\n{name}:")
        print(query.strip())


def main():
    """Main setup function"""
    print("=" * 70)
    print("Databricks Account Monitor - Unity Catalog Setup")
    print("=" * 70)
    print()

    # Check for catalog name argument
    catalog = DEFAULT_CATALOG
    if len(sys.argv) > 1:
        catalog = sys.argv[1]
        print(f"Using catalog: {catalog}")
    else:
        print(f"Using default catalog: {catalog}")
        print(f"To use a different catalog, run: python {sys.argv[0]} <catalog_name>")
    print()

    # Initialize workspace client
    try:
        w = WorkspaceClient()
        print(f"✓ Connected to workspace: {w.config.host}")
    except Exception as e:
        print(f"✗ Failed to connect to Databricks workspace: {e}")
        print("\nPlease ensure you have:")
        print("  1. Databricks CLI installed")
        print("  2. Authentication configured (databricks configure)")
        sys.exit(1)

    # Set catalog
    if not set_catalog(w, catalog):
        print("\n⚠ Could not set catalog, but continuing...")

    # Verify system tables access
    if not verify_system_tables_access(w):
        print("\n⚠ System tables access check failed.")
        print("Setup can continue, but dashboard functionality may be limited.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Create schema
    if not create_schema(w, catalog):
        print("\n✗ Setup failed at schema creation")
        sys.exit(1)

    # Create tables
    success = True
    success = success and create_contracts_table(w, catalog)
    success = success and create_account_metadata_table(w, catalog)
    success = success and create_dashboard_data_table(w, catalog)

    if not success:
        print("\n⚠ Some tables failed to create")
        print("Please check the errors above and try again")
        sys.exit(1)

    # Insert sample data
    print()
    response = input("Insert sample data for testing? (y/n): ")
    if response.lower() == 'y':
        insert_sample_data(w, catalog)

    # Show sample queries
    create_sample_queries(w, catalog)

    print()
    print("=" * 70)
    print("Setup completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print(f"  1. Update sample data in {catalog}.{SCHEMA_NAME}.contracts")
    print(f"  2. Update sample data in {catalog}.{SCHEMA_NAME}.account_metadata")
    print("  3. Run the queries from account_monitor_queries_CORRECTED.sql")
    print("  4. Upload account_monitor_notebook.py to your workspace")
    print("  5. Create a Lakeview dashboard")
    print()
    print(f"Schema location: {catalog}.{SCHEMA_NAME}")
    print()
    print("For detailed instructions, see GETTING_STARTED.md")
    print()


if __name__ == "__main__":
    main()
