#!/usr/bin/env python3
"""
Test all Lakeview Dashboard Queries

This script tests all 17 queries from lakeview_dashboard_queries.sql
to ensure they execute successfully and return data.
"""

import sys
import time
from datetime import datetime

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.sql import StatementState
except ImportError:
    print("Error: databricks-sdk not installed. Install with: pip install databricks-sdk")
    sys.exit(1)

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Test queries
queries = [
    {
        "id": 1,
        "name": "Contract Burndown Line Chart",
        "query": """
SELECT
  contract_id,
  CONCAT(contract_id, ' (USD ', FORMAT_NUMBER(commitment, 0), ')') as contract_label,
  usage_date as date,
  ROUND(cumulative_cost, 2) as actual_consumption,
  ROUND(projected_linear_burn, 2) as ideal_consumption,
  ROUND(commitment, 2) as contract_value,
  ROUND(budget_pct_consumed, 1) as pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 180)
ORDER BY contract_id, usage_date
LIMIT 10
"""
    },
    {
        "id": 2,
        "name": "Contract Summary Table",
        "query": """
SELECT
  contract_id as `Contract ID`,
  cloud_provider as `Cloud`,
  start_date as `Start Date`,
  end_date as `End Date`,
  CONCAT('USD ', FORMAT_NUMBER(commitment, 0)) as `Total Value`,
  CONCAT('USD ', FORMAT_NUMBER(total_consumed, 2)) as `Consumed`,
  CONCAT('USD ', FORMAT_NUMBER(budget_remaining, 2)) as `Remaining`,
  CONCAT(ROUND(consumed_pct, 1), '%') as `% Consumed`,
  pace_status as `Pace Status`,
  days_remaining as `Days Left`,
  projected_end_date as `Projected End`
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY consumed_pct DESC
"""
    },
    {
        "id": 3,
        "name": "Daily Consumption Counter",
        "query": """
SELECT
  CONCAT('USD ', FORMAT_NUMBER(SUM(daily_cost), 2)) as daily_cost,
  COUNT(DISTINCT contract_id) as active_contracts,
  usage_date as date
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date = CURRENT_DATE() - 1
GROUP BY usage_date
"""
    },
    {
        "id": 4,
        "name": "Pace Distribution Pie Chart",
        "query": """
SELECT
  pace_status,
  COUNT(*) as contract_count
FROM main.account_monitoring_dev.contract_burndown_summary
GROUP BY pace_status
ORDER BY
  CASE
    WHEN pace_status LIKE '%OVER%' THEN 1
    WHEN pace_status LIKE '%ABOVE%' THEN 2
    WHEN pace_status LIKE '%ON%' THEN 3
    ELSE 4
  END
"""
    },
    {
        "id": 5,
        "name": "Monthly Consumption Bar Chart",
        "query": """
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  contract_id,
  SUM(daily_cost) as monthly_cost,
  COUNT(*) as days_active
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), contract_id
ORDER BY month, contract_id
LIMIT 10
"""
    },
    {
        "id": 6,
        "name": "Top Workspaces Detailed",
        "query": """
SELECT
  workspace_id as `Workspace ID`,
  cloud_provider as `Cloud`,
  CONCAT('USD ', FORMAT_NUMBER(SUM(actual_cost), 2)) as `Total Cost`,
  ROUND(SUM(usage_quantity), 2) as `Total DBU`,
  COUNT(DISTINCT sku_name) as `Unique SKUs`,
  COUNT(DISTINCT usage_date) as `Active Days`
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY workspace_id, cloud_provider
ORDER BY SUM(actual_cost) DESC
LIMIT 10
"""
    },
    {
        "id": 7,
        "name": "Contract Detailed Analysis",
        "query": """
SELECT
  contract_id as `Contract`,
  CONCAT('USD ', FORMAT_NUMBER(commitment, 0)) as `Value`,
  CONCAT('USD ', FORMAT_NUMBER(total_consumed, 2)) as `Spent`,
  CONCAT(ROUND(consumed_pct, 1), '%') as `% Used`,
  pace_status as `Status`,
  days_remaining as `Days Left`,
  DATEDIFF(projected_end_date, end_date) as `Days Variance`,
  CASE
    WHEN projected_end_date < end_date THEN 'Will deplete early'
    WHEN projected_end_date > end_date THEN 'Under budget'
    ELSE 'On track'
  END as `Budget Health`,
  projected_end_date as `Est. Depletion Date`,
  end_date as `Contract End Date`
FROM main.account_monitoring_dev.contract_burndown_summary
ORDER BY days_remaining
"""
    },
    {
        "id": 8,
        "name": "Account Overview Counters",
        "query": """
SELECT
  COUNT(DISTINCT sku_name) as top_sku_count,
  COUNT(DISTINCT workspace_id) as top_workspace_count,
  MAX(usage_date) as latest_date
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
"""
    },
    {
        "id": 9,
        "name": "Data Freshness",
        "query": """
SELECT
  'Consumption' as source,
  MAX(usage_date) as latest_date,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
    ELSE 'False'
  END as verified
FROM system.billing.usage
UNION ALL
SELECT
  'Metrics' as source,
  MAX(usage_date) as latest_date,
  CASE
    WHEN DATEDIFF(CURRENT_DATE(), MAX(usage_date)) <= 2 THEN 'True'
    ELSE 'False'
  END as verified
FROM system.billing.usage
"""
    },
    {
        "id": 10,
        "name": "Total Spend by Cloud",
        "query": """
SELECT
  customer_name,
  cloud_provider as cloud,
  MIN(usage_date) as start_date,
  MAX(usage_date) as end_date,
  ROUND(SUM(usage_quantity), 3) as dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY customer_name, cloud_provider
"""
    },
    {
        "id": 11,
        "name": "Monthly Cost Trend",
        "query": """
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  cloud_provider,
  ROUND(SUM(usage_quantity), 2) as monthly_dbu,
  ROUND(SUM(actual_cost), 2) as monthly_cost,
  COUNT(DISTINCT workspace_id) as active_workspaces
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), cloud_provider
ORDER BY month
LIMIT 10
"""
    },
    {
        "id": 12,
        "name": "Top Consuming Workspaces",
        "query": """
SELECT
  workspace_id,
  cloud_provider,
  COUNT(DISTINCT sku_name) as sku_count,
  ROUND(SUM(usage_quantity), 2) as total_dbu,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY workspace_id, cloud_provider
ORDER BY total_cost DESC
LIMIT 10
"""
    },
    {
        "id": 13,
        "name": "Top Consuming SKUs",
        "query": """
SELECT
  sku_name,
  cloud_provider,
  usage_unit,
  ROUND(SUM(usage_quantity), 2) as total_usage,
  ROUND(SUM(actual_cost), 2) as total_cost,
  COUNT(DISTINCT workspace_id) as workspace_count
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY sku_name, cloud_provider, usage_unit
ORDER BY total_cost DESC
LIMIT 10
"""
    },
    {
        "id": 14,
        "name": "Cost by Product Category",
        "query": """
SELECT
  DATE_TRUNC('MONTH', usage_date) as month,
  product_category as category,
  cloud_provider,
  ROUND(SUM(actual_cost), 2) as total_cost
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY DATE_TRUNC('MONTH', usage_date), product_category, cloud_provider
ORDER BY month
LIMIT 10
"""
    },
    {
        "id": 15,
        "name": "Dashboard Data (Base Query)",
        "query": """
SELECT *
FROM main.account_monitoring_dev.dashboard_data
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
LIMIT 10
"""
    },
    {
        "id": 16,
        "name": "Account Information",
        "query": """
SELECT
  customer_name as `Customer`,
  salesforce_id as `Salesforce ID`,
  CONCAT_WS(' > ', business_unit_l0, business_unit_l1, business_unit_l2, business_unit_l3) as `Business Unit`,
  account_executive as `AE`,
  solutions_architect as `SA`,
  delivery_solutions_architect as `DSA`
FROM main.account_monitoring_dev.account_metadata
LIMIT 1
"""
    },
    {
        "id": 17,
        "name": "Combined Contract Burndown",
        "query": """
SELECT
  usage_date as date,
  SUM(commitment) as total_commitment,
  SUM(cumulative_cost) as total_consumption,
  ROUND(SUM(cumulative_cost) / SUM(commitment) * 100, 1) as overall_pct_consumed
FROM main.account_monitoring_dev.contract_burndown
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
GROUP BY usage_date
ORDER BY usage_date
LIMIT 10
"""
    }
]

def get_warehouse_id(w):
    """Get the first available SQL warehouse"""
    try:
        warehouses = list(w.warehouses.list())
        if warehouses:
            return warehouses[0].id
        return None
    except Exception as e:
        print(f"{RED}Error getting warehouse: {e}{RESET}")
        return None

def run_query(w, warehouse_id, query_text):
    """Execute a query via Databricks SQL warehouse"""
    try:
        # Execute statement
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=query_text,
            wait_timeout="60s"
        )

        # Check status
        if response.status.state == StatementState.SUCCEEDED:
            # Get row count
            if response.result and response.result.row_count is not None:
                row_count = response.result.row_count
            else:
                row_count = 0
            return True, row_count, None
        else:
            error_msg = "Query failed"
            if response.status.error:
                error_msg = f"{response.status.error.error_code}: {response.status.error.message}"
            return False, 0, error_msg

    except Exception as e:
        return False, 0, str(e)

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Testing Lakeview Dashboard Queries{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Get profile from command line or use default
    profile = sys.argv[1] if len(sys.argv) > 1 else None

    # Initialize Workspace Client
    if profile:
        print(f"{YELLOW}Initializing Databricks client with profile: {profile}...{RESET}")
    else:
        print(f"{YELLOW}Initializing Databricks client...{RESET}")

    try:
        w = WorkspaceClient(profile=profile) if profile else WorkspaceClient()
        print(f"{GREEN}✓ Connected to Databricks{RESET}")
    except Exception as e:
        print(f"{RED}✗ Failed to connect: {e}{RESET}")
        sys.exit(1)

    print(f"\n{YELLOW}Getting SQL Warehouse...{RESET}")
    warehouse_id = get_warehouse_id(w)

    if not warehouse_id:
        print(f"{RED}✗ Failed to get warehouse ID{RESET}")
        sys.exit(1)

    print(f"{GREEN}✓ Using warehouse: {warehouse_id}{RESET}\n")

    # Test results
    passed = 0
    failed = 0
    warnings = 0
    results = []

    # Run each query
    for query_info in queries:
        query_id = query_info['id']
        query_name = query_info['name']
        query_text = query_info['query']

        print(f"{BLUE}Query {query_id:2d}: {query_name}{RESET}")

        success, row_count, error = run_query(w, warehouse_id, query_text)

        if success:
            # Check if data returned
            if row_count > 0:
                status = "✓"
                status_color = GREEN
                passed += 1
                print(f"  {status_color}{status} PASSED{RESET} - Returned {row_count} row(s)")
                results.append({
                    'id': query_id,
                    'name': query_name,
                    'status': 'PASSED',
                    'rows': row_count
                })
            else:
                status = "⚠"
                status_color = YELLOW
                warnings += 1
                print(f"  {status_color}{status} PASSED{RESET} - Returned 0 rows (may indicate missing data)")
                results.append({
                    'id': query_id,
                    'name': query_name,
                    'status': 'WARNING',
                    'rows': 0
                })
        else:
            print(f"  {RED}✗ FAILED{RESET}")
            if error:
                print(f"  {RED}  Error: {error[:200]}{RESET}")
            failed += 1
            results.append({
                'id': query_id,
                'name': query_name,
                'status': 'FAILED',
                'error': error[:200] if error else 'Unknown error'
            })

        print()

    # Summary
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    total = len(queries)
    print(f"Total Queries: {total}")
    print(f"{GREEN}Passed: {passed}{RESET}")
    if warnings > 0:
        print(f"{YELLOW}Warnings: {warnings}{RESET} (queries passed but returned 0 rows)")
    print(f"{RED}Failed: {failed}{RESET}")

    success_rate = ((passed + warnings) / total) * 100 if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    # Failed queries detail
    if failed > 0:
        print(f"\n{RED}Failed Queries:{RESET}")
        for result in results:
            if result['status'] == 'FAILED':
                print(f"  {RED}✗ Query {result['id']}: {result['name']}{RESET}")
                if 'error' in result:
                    print(f"    {result['error']}")

    # Warning queries detail
    if warnings > 0:
        print(f"\n{YELLOW}Queries with Warnings:{RESET}")
        for result in results:
            if result['status'] == 'WARNING':
                print(f"  {YELLOW}⚠ Query {result['id']}: {result['name']} - 0 rows (missing data?){RESET}")

    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Exit code
    if failed > 0:
        sys.exit(1)
    elif warnings > 0:
        sys.exit(2)  # Success with warnings
    else:
        sys.exit(0)  # Complete success

if __name__ == '__main__':
    main()
