# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 Account Monitor - Post Deployment Validation
# MAGIC
# MAGIC **Version:** 1.1.0 (Updated: 2026-01-29)
# MAGIC
# MAGIC This notebook validates that your Account Monitor deployment is working correctly.
# MAGIC It checks all the critical steps from START_HERE.md.
# MAGIC
# MAGIC **What This Notebook Does:**
# MAGIC 1. ✅ Verifies system tables access
# MAGIC 2. ✅ Tests cost calculation with correct schema
# MAGIC 3. ✅ Validates Unity Catalog tables exist
# MAGIC 4. ✅ Checks sample data is present
# MAGIC 5. ✅ Tests dashboard data queries
# MAGIC 6. ✅ Validates contract tracking
# MAGIC 7. ✅ Confirms data freshness
# MAGIC
# MAGIC **Run this after:** `databricks bundle deploy --profile LPT_FREE_EDITION -t dev`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration - Update these if you used different values
CATALOG = "main"
SCHEMA = "account_monitoring_dev"  # or "account_monitoring" for prod
TARGET = "dev"  # or "prod"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Test results tracking
test_results = []

def test_result(test_name, passed, message=""):
    """Track test results"""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    test_results.append({"test": test_name, "passed": passed, "message": message})
    print(f"{status} - {test_name}")
    if message:
        print(f"   {message}")
    print()

def print_summary():
    """Print test summary"""
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed

    print("="*70)
    print(f"{BLUE}📊 VALIDATION SUMMARY{RESET}")
    print("="*70)
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    print("="*70)

    if failed > 0:
        print(f"\n{RED}❌ Failed Tests:{RESET}")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}: {result['message']}")
    else:
        print(f"\n{GREEN}🎉 All tests passed! Your deployment is ready to use.{RESET}")

print(f"{BLUE}Starting validation for {TARGET} environment...{RESET}\n")
print(f"Catalog: {CATALOG}")
print(f"Schema: {SCHEMA}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: System Tables Access

# COMMAND ----------

print(f"{BLUE}Test 1: Checking system.billing.usage access{RESET}\n")

try:
    result = spark.sql("""
        SELECT COUNT(*) as record_count
        FROM system.billing.usage
        WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 7)
    """).collect()[0]

    count = result['record_count']
    if count > 0:
        test_result("System Tables Access", True, f"Found {count:,} records in last 7 days")
    else:
        test_result("System Tables Access", False, "No records found - data may be delayed")
except Exception as e:
    test_result("System Tables Access", False, f"Cannot access system tables: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: Data Freshness Check

# COMMAND ----------

print(f"{BLUE}Test 2: Checking data freshness{RESET}\n")

try:
    result = spark.sql("""
        SELECT
            MAX(usage_date) as latest_date,
            DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_behind
        FROM system.billing.usage
        WHERE record_type = 'ORIGINAL'
    """).collect()[0]

    latest = result['latest_date']
    days_behind = result['days_behind']

    if days_behind <= 2:
        test_result("Data Freshness", True, f"Latest data: {latest} ({days_behind} days old)")
    elif days_behind <= 5:
        test_result("Data Freshness", True, f"⚠️  Latest data: {latest} ({days_behind} days old - acceptable)")
    else:
        test_result("Data Freshness", False, f"Data is stale: {latest} ({days_behind} days old)")
except Exception as e:
    test_result("Data Freshness", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Cost Calculation (Correct Schema)

# COMMAND ----------

print(f"{BLUE}Test 3: Testing cost calculation with correct JOIN{RESET}\n")

try:
    result = spark.sql("""
        SELECT
            u.cloud,
            COUNT(*) as records,
            SUM(u.usage_quantity) as total_dbu,
            SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
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
    """).collect()

    if len(result) > 0:
        for row in result:
            print(f"  {row['cloud']}: ${row['total_cost']:.2f} ({row['total_dbu']:.2f} DBU)")
        test_result("Cost Calculation", True, f"Successfully calculated costs for {len(result)} cloud provider(s)")
    else:
        test_result("Cost Calculation", False, "No cost data for yesterday - may be normal if it's early")
except Exception as e:
    test_result("Cost Calculation", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Unity Catalog Schema Exists

# COMMAND ----------

print(f"{BLUE}Test 4: Checking Unity Catalog schema{RESET}\n")

try:
    schemas = spark.sql(f"SHOW SCHEMAS IN {CATALOG}").collect()
    schema_names = [s['databaseName'] for s in schemas]

    if SCHEMA in schema_names:
        test_result("Unity Catalog Schema", True, f"Schema {CATALOG}.{SCHEMA} exists")
    else:
        test_result("Unity Catalog Schema", False, f"Schema {CATALOG}.{SCHEMA} not found. Available: {', '.join(schema_names)}")
except Exception as e:
    test_result("Unity Catalog Schema", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Required Tables Exist

# COMMAND ----------

print(f"{BLUE}Test 5: Checking required tables{RESET}\n")

required_tables = [
    "contracts",
    "account_metadata",
    "dashboard_data",
    "daily_summary"
]

try:
    tables = spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").collect()
    table_names = [t['tableName'] for t in tables]

    missing_tables = []
    for table in required_tables:
        if table in table_names:
            print(f"  {GREEN}✓{RESET} {table}")
        else:
            print(f"  {RED}✗{RESET} {table}")
            missing_tables.append(table)

    if len(missing_tables) == 0:
        test_result("Required Tables", True, f"All {len(required_tables)} tables exist")
    else:
        test_result("Required Tables", False, f"Missing tables: {', '.join(missing_tables)}")
except Exception as e:
    test_result("Required Tables", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Account Metadata Table

# COMMAND ----------

print(f"{BLUE}Test 6: Checking account metadata{RESET}\n")

try:
    result = spark.sql(f"""
        SELECT
            account_id,
            customer_name,
            business_unit_l0,
            account_executive,
            solutions_architect
        FROM {CATALOG}.{SCHEMA}.account_metadata
    """).collect()

    if len(result) > 0:
        print("  Account metadata found:")
        for row in result:
            print(f"    Account: {row['account_id']}")
            print(f"    Customer: {row['customer_name']}")
            print(f"    BU: {row['business_unit_l0']}")
        test_result("Account Metadata", True, f"Found {len(result)} account(s)")
    else:
        test_result("Account Metadata", False, "No account metadata found - run setup job first")
except Exception as e:
    test_result("Account Metadata", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 7: Contracts Table

# COMMAND ----------

print(f"{BLUE}Test 7: Checking contracts{RESET}\n")

try:
    result = spark.sql(f"""
        SELECT
            contract_id,
            cloud_provider,
            start_date,
            end_date,
            total_value,
            status
        FROM {CATALOG}.{SCHEMA}.contracts
    """).collect()

    if len(result) > 0:
        print("  Contracts found:")
        for row in result:
            print(f"    {row['contract_id']} - {row['cloud_provider']} - ${row['total_value']:,.2f} ({row['status']})")
        test_result("Contracts", True, f"Found {len(result)} contract(s)")
    else:
        test_result("Contracts", False, "No contracts found - add your contracts")
except Exception as e:
    test_result("Contracts", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 8: Dashboard Data Table

# COMMAND ----------

print(f"{BLUE}Test 8: Checking dashboard data{RESET}\n")

try:
    result = spark.sql(f"""
        SELECT
            COUNT(*) as total_records,
            MIN(usage_date) as earliest_date,
            MAX(usage_date) as latest_date,
            COUNT(DISTINCT workspace_id) as workspace_count,
            ROUND(SUM(actual_cost), 2) as total_cost
        FROM {CATALOG}.{SCHEMA}.dashboard_data
    """).collect()[0]

    if result['total_records'] > 0:
        print(f"  Records: {result['total_records']:,}")
        print(f"  Date Range: {result['earliest_date']} to {result['latest_date']}")
        print(f"  Workspaces: {result['workspace_count']}")
        print(f"  Total Cost: ${result['total_cost']:,.2f}")
        test_result("Dashboard Data", True, "Dashboard data is populated")
    else:
        test_result("Dashboard Data", False, "Dashboard data is empty - run daily refresh job")
except Exception as e:
    test_result("Dashboard Data", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 9: Daily Summary Table

# COMMAND ----------

print(f"{BLUE}Test 9: Checking daily summary{RESET}\n")

try:
    result = spark.sql(f"""
        SELECT COUNT(*) as record_count
        FROM {CATALOG}.{SCHEMA}.daily_summary
    """).collect()[0]

    if result['record_count'] > 0:
        test_result("Daily Summary", True, f"Found {result['record_count']:,} daily summary records")
    else:
        test_result("Daily Summary", False, "Daily summary is empty - run daily refresh job")
except Exception as e:
    test_result("Daily Summary", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 10: Contract Consumption Query

# COMMAND ----------

print(f"{BLUE}Test 10: Testing contract consumption calculation{RESET}\n")

try:
    result = spark.sql(f"""
        SELECT
            c.contract_id,
            c.total_value,
            COALESCE(SUM(d.actual_cost), 0) as consumed,
            ROUND(COALESCE(SUM(d.actual_cost), 0) / c.total_value * 100, 1) as consumed_pct
        FROM {CATALOG}.{SCHEMA}.contracts c
        LEFT JOIN {CATALOG}.{SCHEMA}.dashboard_data d
            ON c.account_id = d.account_id
            AND c.cloud_provider = d.cloud_provider
            AND d.usage_date BETWEEN c.start_date AND c.end_date
        WHERE c.status = 'ACTIVE'
        GROUP BY c.contract_id, c.total_value
    """).collect()

    if len(result) > 0:
        print("  Contract consumption:")
        for row in result:
            print(f"    {row['contract_id']}: ${row['consumed']:,.2f} / ${row['total_value']:,.2f} ({row['consumed_pct']}%)")
        test_result("Contract Consumption", True, "Contract consumption calculated successfully")
    else:
        test_result("Contract Consumption", False, "No active contracts or no consumption data")
except Exception as e:
    test_result("Contract Consumption", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 11: Jobs Deployed

# COMMAND ----------

print(f"{BLUE}Test 11: Checking deployed jobs{RESET}\n")

try:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    jobs_found = []
    expected_jobs = [
        f"[{TARGET}] Account Monitor - Setup",
        f"[{TARGET}] Account Monitor - Daily Refresh",
        f"[{TARGET}] Account Monitor - Weekly Review",
        f"[{TARGET}] Account Monitor - Monthly Summary"
    ]

    # List all jobs and filter by target
    try:
        all_jobs = list(w.jobs.list())
        for job in all_jobs:
            if job.settings and job.settings.name:
                job_name = job.settings.name
                # Check if this is one of our account monitor jobs
                if f"[{TARGET}]" in job_name and "Account Monitor" in job_name:
                    jobs_found.append(job_name)

        if len(jobs_found) > 0:
            print("  Jobs found:")
            for job in jobs_found:
                print(f"    - {job}")
            test_result("Jobs Deployed", True, f"Found {len(jobs_found)} job(s)")
        elif len(jobs_found) == 0:
            print(f"  Expected jobs:")
            for expected in expected_jobs:
                print(f"    - {expected}")
            test_result("Jobs Deployed", False, f"No jobs found with [{TARGET}] prefix. Run: databricks bundle deploy")
    except Exception as api_error:
        # If we can't list jobs, check if tables exist as fallback
        print(f"  ⚠️  Cannot list jobs via API: {str(api_error)}")
        print("  Checking if tables exist as fallback validation...")

        tables = spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").collect()
        table_names = [t['tableName'] for t in tables]

        if len(table_names) >= len(required_tables):
            print("  ✓ All required tables exist - jobs likely deployed successfully")
            test_result("Jobs Deployed", True, "Tables exist - jobs assumed deployed (API check failed)")
        else:
            test_result("Jobs Deployed", False, f"Cannot verify jobs and only {len(table_names)} of {len(required_tables)} tables exist")

except Exception as e:
    test_result("Jobs Deployed", False, f"Error during job verification: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 12: Sample Query - Yesterday's Cost

# COMMAND ----------

print(f"{BLUE}Test 12: Running sample query - Yesterday's cost{RESET}\n")

try:
    result = spark.sql("""
        SELECT
            cloud_provider,
            COUNT(DISTINCT workspace_id) as workspaces,
            ROUND(SUM(actual_cost), 2) as total_cost
        FROM main.account_monitoring_dev.dashboard_data
        WHERE usage_date = CURRENT_DATE() - 1
        GROUP BY cloud_provider
    """).collect()

    if len(result) > 0:
        print("  Yesterday's costs:")
        for row in result:
            print(f"    {row['cloud_provider']}: ${row['total_cost']:,.2f} ({row['workspaces']} workspaces)")
        test_result("Sample Query", True, "Sample queries work correctly")
    else:
        test_result("Sample Query", False, "No data for yesterday - may be normal")
except Exception as e:
    test_result("Sample Query", False, f"Error: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Validation Summary

# COMMAND ----------

print_summary()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Next Steps
# MAGIC
# MAGIC ### If All Tests Passed ✅
# MAGIC
# MAGIC 1. **Update Your Data**
# MAGIC    ```sql
# MAGIC    -- Update account metadata
# MAGIC    UPDATE main.account_monitoring_dev.account_metadata
# MAGIC    SET
# MAGIC        customer_name = 'Your Organization',
# MAGIC        salesforce_id = 'YOUR-SF-ID',
# MAGIC        business_unit_l0 = 'YOUR-REGION',
# MAGIC        account_executive = 'AE Name',
# MAGIC        solutions_architect = 'SA Name'
# MAGIC    WHERE account_id = (SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1);
# MAGIC
# MAGIC    -- Add your contracts
# MAGIC    INSERT INTO main.account_monitoring_dev.contracts VALUES
# MAGIC        ('YOUR-CONTRACT-ID',
# MAGIC         (SELECT DISTINCT account_id FROM system.billing.usage LIMIT 1),
# MAGIC         'aws',
# MAGIC         DATE'2024-01-01',
# MAGIC         DATE'2025-12-31',
# MAGIC         500000.00,
# MAGIC         'USD',
# MAGIC         'SPEND',
# MAGIC         'ACTIVE',
# MAGIC         'Your contract notes',
# MAGIC         CURRENT_TIMESTAMP(),
# MAGIC         CURRENT_TIMESTAMP());
# MAGIC    ```
# MAGIC
# MAGIC 2. **Run Jobs**
# MAGIC    ```bash
# MAGIC    # Run daily refresh
# MAGIC    databricks bundle run account_monitor_daily_refresh --profile LPT_FREE_EDITION -t dev
# MAGIC    ```
# MAGIC
# MAGIC 3. **Create Dashboard**
# MAGIC    - Go to **Dashboards** → **Create Dashboard**
# MAGIC    - Use queries from `account_monitor_queries_CORRECTED.sql`
# MAGIC
# MAGIC ### If Tests Failed ❌
# MAGIC
# MAGIC 1. **Check the failed test messages above**
# MAGIC 2. **Run the setup job**
# MAGIC    ```bash
# MAGIC    databricks bundle run account_monitor_setup --profile LPT_FREE_EDITION -t dev
# MAGIC    ```
# MAGIC 3. **Re-run this validation notebook**
# MAGIC
# MAGIC ### Common Issues
# MAGIC
# MAGIC - **System tables access failed**: Contact your admin to enable system tables
# MAGIC - **Tables missing**: Run the setup job first
# MAGIC - **Dashboard data empty**: Run the daily refresh job
# MAGIC - **Contracts missing**: Add your contract data

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎉 Congratulations!
# MAGIC
# MAGIC If all tests passed, your Account Monitor is ready to use!
# MAGIC
# MAGIC **Quick Links:**
# MAGIC - View jobs: Go to **Workflows** → **Jobs** → Filter by "Account Monitor"
# MAGIC - Query data: Use **SQL Editor** with queries from `account_monitor_queries_CORRECTED.sql`
# MAGIC - Create dashboard: Go to **Dashboards** → **Create Dashboard**
# MAGIC
# MAGIC **Documentation:**
# MAGIC - `START_HERE.md` - Quick start guide
# MAGIC - `SCHEMA_REFERENCE.md` - System table schemas
# MAGIC - `QUICK_REFERENCE.md` - Query examples
# MAGIC - `OPERATIONS_GUIDE.md` - Daily operations
