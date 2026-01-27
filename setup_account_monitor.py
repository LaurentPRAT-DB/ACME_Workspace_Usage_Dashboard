"""
Databricks Account Monitor - Setup Script
Automates the creation of custom tables and initial data population
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import *
import sys
from datetime import datetime, timedelta

def create_database(w: WorkspaceClient, catalog: str = "hive_metastore"):
    """Create the account_monitoring database"""
    print("Creating database: account_monitoring")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                CREATE DATABASE IF NOT EXISTS account_monitoring
                COMMENT 'Database for account monitoring and cost tracking'
                LOCATION '/account_monitoring'
            """
        })
        print("✓ Database created successfully")
    except Exception as e:
        print(f"⚠ Error creating database: {e}")
        return False

    return True


def create_contracts_table(w: WorkspaceClient):
    """Create the contracts tracking table"""
    print("Creating table: account_monitoring.contracts")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                CREATE TABLE IF NOT EXISTS account_monitoring.contracts (
                  contract_id STRING COMMENT 'Unique contract identifier',
                  account_id STRING COMMENT 'Databricks account ID',
                  cloud_provider STRING COMMENT 'Cloud provider: aws, azure, gcp',
                  start_date DATE COMMENT 'Contract start date',
                  end_date DATE COMMENT 'Contract end date',
                  total_value DECIMAL(18,2) COMMENT 'Total contract value',
                  currency STRING COMMENT 'Currency code (USD, EUR, etc.)',
                  commitment_type STRING COMMENT 'DBU or SPEND commitment',
                  status STRING COMMENT 'ACTIVE, EXPIRED, or PENDING',
                  notes STRING COMMENT 'Additional notes',
                  created_at TIMESTAMP COMMENT 'Record creation timestamp',
                  updated_at TIMESTAMP COMMENT 'Record update timestamp'
                )
                USING DELTA
                COMMENT 'Contract tracking for consumption monitoring'
                TBLPROPERTIES (
                  'delta.enableChangeDataFeed' = 'true',
                  'delta.autoOptimize.optimizeWrite' = 'true'
                )
            """
        })
        print("✓ Contracts table created successfully")
    except Exception as e:
        print(f"⚠ Error creating contracts table: {e}")
        return False

    return True


def create_account_metadata_table(w: WorkspaceClient):
    """Create the account metadata table"""
    print("Creating table: account_monitoring.account_metadata")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                CREATE TABLE IF NOT EXISTS account_monitoring.account_metadata (
                  account_id STRING COMMENT 'Databricks account ID',
                  customer_name STRING COMMENT 'Customer display name',
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
                  created_at TIMESTAMP COMMENT 'Record creation timestamp',
                  updated_at TIMESTAMP COMMENT 'Record update timestamp'
                )
                USING DELTA
                COMMENT 'Account metadata and organizational information'
                TBLPROPERTIES (
                  'delta.enableChangeDataFeed' = 'true',
                  'delta.autoOptimize.optimizeWrite' = 'true'
                )
            """
        })
        print("✓ Account metadata table created successfully")
    except Exception as e:
        print(f"⚠ Error creating account metadata table: {e}")
        return False

    return True


def create_dashboard_data_table(w: WorkspaceClient):
    """Create the dashboard data aggregation table"""
    print("Creating table: account_monitoring.dashboard_data")

    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                CREATE TABLE IF NOT EXISTS account_monitoring.dashboard_data (
                  usage_date DATE,
                  account_id STRING,
                  customer_name STRING,
                  salesforce_id STRING,
                  business_unit_l0 STRING,
                  business_unit_l1 STRING,
                  business_unit_l2 STRING,
                  business_unit_l3 STRING,
                  account_executive STRING,
                  solutions_architect STRING,
                  workspace_id STRING,
                  cloud_provider STRING,
                  sku_name STRING,
                  usage_unit STRING,
                  usage_quantity DECIMAL(18,6),
                  actual_cost DECIMAL(18,2),
                  list_price_per_unit DECIMAL(18,6),
                  discounted_price_per_unit DECIMAL(18,6),
                  list_cost DECIMAL(18,2),
                  discounted_cost DECIMAL(18,2),
                  product_category STRING,
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
        print("✓ Dashboard data table created successfully")
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


def insert_sample_data(w: WorkspaceClient):
    """Insert sample data for testing"""
    print("\nInserting sample data...")

    # Sample contract data
    print("Inserting sample contracts...")
    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                INSERT INTO account_monitoring.contracts VALUES
                  ('1694992', 'account-001', 'aws', '2024-11-10', '2026-01-29',
                   300000.00, 'USD', 'SPEND', 'ACTIVE', 'First AWS contract',
                   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
                  ('2209701', 'account-001', 'aws', '2026-01-30', '2029-01-29',
                   1000000.00, 'USD', 'SPEND', 'ACTIVE', 'Second AWS contract',
                   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
            """
        })
        print("✓ Sample contracts inserted")
    except Exception as e:
        print(f"⚠ Note: Sample contracts may already exist: {e}")

    # Sample account metadata
    print("Inserting sample account metadata...")
    try:
        w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                INSERT INTO account_monitoring.account_metadata VALUES
                  ('account-001', 'Sample Customer Inc', '0014N00001HEcQAG',
                   'AMER', 'West', 'California', 'Enterprise',
                   'John Doe', 'Jane Smith', 'Bob Johnson',
                   'US-West', 'Technology',
                   CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
            """
        })
        print("✓ Sample account metadata inserted")
    except Exception as e:
        print(f"⚠ Note: Sample metadata may already exist: {e}")


def verify_system_tables_access(w: WorkspaceClient):
    """Verify access to system tables"""
    print("\nVerifying access to system tables...")

    try:
        result = w.api_client.do('POST', '/api/2.0/sql/statements', {
            'warehouse_id': get_default_warehouse(w),
            'statement': """
                SELECT COUNT(*) as count
                FROM system.billing.usage
                WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
            """
        })
        print("✓ System tables access verified")
        return True
    except Exception as e:
        print(f"✗ Cannot access system tables: {e}")
        print("\nPlease ensure:")
        print("  1. System tables are enabled for your account")
        print("  2. You have the necessary permissions")
        print("  3. Contact Databricks support if needed")
        return False


def create_refresh_job(w: WorkspaceClient):
    """Create a job to refresh dashboard data daily"""
    print("\nCreating daily refresh job...")

    job_name = "Account Monitor - Daily Refresh"

    try:
        from databricks.sdk.service.jobs import Task, NotebookTask, JobCluster, ComputeSpec

        # Check if job already exists
        existing_jobs = [j for j in w.jobs.list() if j.settings.name == job_name]
        if existing_jobs:
            print(f"⚠ Job '{job_name}' already exists. Skipping creation.")
            return True

        # Create job
        job = w.jobs.create(
            name=job_name,
            tasks=[
                Task(
                    task_key="refresh_dashboard_data",
                    description="Refresh dashboard data from system tables",
                    notebook_task=NotebookTask(
                        notebook_path="/Workspace/Shared/account_monitor_notebook",
                        source="WORKSPACE"
                    ),
                    timeout_seconds=3600
                )
            ],
            schedule={
                "quartz_cron_expression": "0 0 2 * * ?",  # Daily at 2 AM
                "timezone_id": "UTC",
                "pause_status": "UNPAUSED"
            },
            email_notifications={
                "on_failure": ["your-email@company.com"],
                "no_alert_for_skipped_runs": True
            },
            max_concurrent_runs=1
        )

        print(f"✓ Job created successfully with ID: {job.job_id}")
        print(f"  Schedule: Daily at 2:00 AM UTC")
        return True

    except Exception as e:
        print(f"⚠ Could not create job automatically: {e}")
        print("\nManual creation steps:")
        print("  1. Go to Workflows in your Databricks workspace")
        print("  2. Create a new job")
        print("  3. Add the account_monitor_notebook")
        print("  4. Schedule it to run daily")
        return False


def main():
    """Main setup function"""
    print("=" * 70)
    print("Databricks Account Monitor - Setup")
    print("=" * 70)
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

    print()

    # Verify system tables access
    if not verify_system_tables_access(w):
        print("\n⚠ System tables access check failed.")
        print("Setup can continue, but dashboard functionality may be limited.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    print()

    # Create database
    if not create_database(w):
        print("\n✗ Setup failed at database creation")
        sys.exit(1)

    print()

    # Create tables
    success = True
    success = success and create_contracts_table(w)
    success = success and create_account_metadata_table(w)
    success = success and create_dashboard_data_table(w)

    if not success:
        print("\n⚠ Some tables failed to create")
        print("Please check the errors above and try again")
        sys.exit(1)

    # Insert sample data
    response = input("\nInsert sample data for testing? (y/n): ")
    if response.lower() == 'y':
        insert_sample_data(w)

    # Create refresh job
    print()
    response = input("Create daily refresh job? (y/n): ")
    if response.lower() == 'y':
        create_refresh_job(w)

    print()
    print("=" * 70)
    print("Setup completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Upload account_monitor_notebook.py to your workspace")
    print("  2. Update account metadata with your actual data")
    print("  3. Add your contract information")
    print("  4. Run the notebook to generate dashboard data")
    print("  5. Create a Lakeview dashboard using dashboard_data table")
    print()
    print("For detailed instructions, see README.md")
    print()


if __name__ == "__main__":
    main()
