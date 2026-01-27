-- Insert Sample Data
-- Adds sample account metadata and contracts for testing

-- Get the actual account_id from system tables
CREATE OR REPLACE TEMP VIEW actual_account AS
SELECT DISTINCT account_id
FROM system.billing.usage
LIMIT 1;

-- Insert sample account metadata
MERGE INTO main.account_monitoring_dev.account_metadata AS target
USING (
  SELECT
    aa.account_id,
    'Your Organization Name' as customer_name,
    'SF-XXXXX' as salesforce_id,
    'REGION' as business_unit_l0,
    'SUB-REGION' as business_unit_l1,
    'COUNTRY' as business_unit_l2,
    'DIVISION' as business_unit_l3,
    'Account Executive Name' as account_executive,
    'Solutions Architect Name' as solutions_architect,
    'Delivery SA Name' as delivery_solutions_architect,
    'US-WEST' as region,
    'Technology' as industry,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as updated_at
  FROM actual_account aa
) AS source
ON target.account_id = source.account_id
WHEN MATCHED THEN UPDATE SET
  customer_name = source.customer_name,
  salesforce_id = source.salesforce_id,
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
WHEN NOT MATCHED THEN INSERT (
  account_id, customer_name, salesforce_id, business_unit_l0, business_unit_l1,
  business_unit_l2, business_unit_l3, account_executive, solutions_architect,
  delivery_solutions_architect, region, industry, created_at, updated_at
) VALUES (
  source.account_id, source.customer_name, source.salesforce_id, source.business_unit_l0,
  source.business_unit_l1, source.business_unit_l2, source.business_unit_l3,
  source.account_executive, source.solutions_architect, source.delivery_solutions_architect,
  source.region, source.industry, source.created_at, source.updated_at
);

-- Get cloud provider from actual usage
CREATE OR REPLACE TEMP VIEW actual_cloud AS
SELECT DISTINCT cloud as cloud_provider
FROM system.billing.usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 365)
LIMIT 1;

-- Insert realistic 1-year $2000 contract
-- Set to start 1 year ago so we can see historical burn
MERGE INTO main.account_monitoring_dev.contracts AS target
USING (
  SELECT
    'CONTRACT-2026-001' as contract_id,
    aa.account_id,
    ac.cloud_provider,
    DATE_SUB(CURRENT_DATE(), 365) as start_date,
    CURRENT_DATE() as end_date,
    2000.00 as total_value,
    'USD' as currency,
    'SPEND' as commitment_type,
    'ACTIVE' as status,
    '1-year $2000 contract for burn down demo' as notes,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as updated_at
  FROM actual_account aa
  CROSS JOIN actual_cloud ac
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
WHEN NOT MATCHED THEN INSERT (
  contract_id, account_id, cloud_provider, start_date, end_date,
  total_value, currency, commitment_type, status, notes, created_at, updated_at
) VALUES (
  source.contract_id, source.account_id, source.cloud_provider, source.start_date,
  source.end_date, source.total_value, source.currency, source.commitment_type,
  source.status, source.notes, source.created_at, source.updated_at
);

-- Also insert a large enterprise contract for comparison
MERGE INTO main.account_monitoring_dev.contracts AS target
USING (
  SELECT
    'CONTRACT-ENTERPRISE-001' as contract_id,
    aa.account_id,
    ac.cloud_provider,
    DATE'2024-01-01' as start_date,
    DATE'2026-12-31' as end_date,
    500000.00 as total_value,
    'USD' as currency,
    'SPEND' as commitment_type,
    'ACTIVE' as status,
    'Multi-year enterprise contract' as notes,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as updated_at
  FROM actual_account aa
  CROSS JOIN actual_cloud ac
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
WHEN NOT MATCHED THEN INSERT (
  contract_id, account_id, cloud_provider, start_date, end_date,
  total_value, currency, commitment_type, status, notes, created_at, updated_at
) VALUES (
  source.contract_id, source.account_id, source.cloud_provider, source.start_date,
  source.end_date, source.total_value, source.currency, source.commitment_type,
  source.status, source.notes, source.created_at, source.updated_at
);

-- Display inserted data
SELECT
  'Sample data inserted' as status,
  (SELECT COUNT(*) FROM main.account_monitoring_dev.account_metadata) as account_count,
  (SELECT COUNT(*) FROM main.account_monitoring_dev.contracts) as contract_count;
