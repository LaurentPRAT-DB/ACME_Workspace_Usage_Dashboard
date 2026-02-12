# Schema Reference

This document contains schema references for both Databricks system tables and Account Monitor custom tables.

---

## Account Monitor Tables (Unity Catalog)

### contracts

Stores contract definitions loaded from YAML configuration.

| Column | Type | Description |
|--------|------|-------------|
| `contract_id` | STRING | Primary key - unique contract identifier |
| `account_id` | STRING | Databricks account ID |
| `cloud_provider` | STRING | Cloud provider (AWS, AZURE, GCP) |
| `start_date` | DATE | Contract start date |
| `end_date` | DATE | Contract end date |
| `total_value` | DECIMAL(20,2) | Contract commitment value |
| `currency` | STRING | Currency code (USD, EUR, etc.) |
| `commitment_type` | STRING | SPEND or DBU |
| `status` | STRING | ACTIVE, INACTIVE, EXPIRED |
| `notes` | STRING | Optional description |
| `created_at` | TIMESTAMP | Record creation time |

### contract_burndown

Daily cumulative consumption tracking per contract.

| Column | Type | Description |
|--------|------|-------------|
| `contract_id` | STRING | Foreign key to contracts |
| `usage_date` | DATE | Date of consumption |
| `daily_cost` | DECIMAL(20,2) | Cost for this day |
| `cumulative_cost` | DECIMAL(20,2) | Running total from contract start |
| `commitment` | DECIMAL(20,2) | Contract total_value |
| `remaining_budget` | DECIMAL(20,2) | commitment - cumulative_cost |
| `burn_rate_7d` | DECIMAL(20,6) | 7-day rolling average daily cost |
| `pct_consumed` | DECIMAL(10,4) | Percentage of commitment consumed |

### contract_forecast

Prophet ML model predictions for consumption.

| Column | Type | Description |
|--------|------|-------------|
| `contract_id` | STRING | Foreign key to contracts |
| `forecast_date` | DATE | Date of prediction |
| `predicted_cumulative` | DECIMAL(20,2) | Predicted cumulative cost |
| `predicted_cumulative_lower` | DECIMAL(20,2) | Lower confidence bound |
| `predicted_cumulative_upper` | DECIMAL(20,2) | Upper confidence bound |
| `exhaustion_date_p10` | DATE | 10th percentile exhaustion date |
| `exhaustion_date_p50` | DATE | Median exhaustion date |
| `exhaustion_date_p90` | DATE | 90th percentile exhaustion date |
| `forecast_model` | STRING | Model type (prophet, linear_fallback) |
| `training_date` | TIMESTAMP | When model was trained |
| `created_at` | TIMESTAMP | Record creation time |

### discount_tiers

Configurable discount rates by commitment level and duration.

| Column | Type | Description |
|--------|------|-------------|
| `tier_id` | STRING | Primary key - unique tier identifier |
| `tier_name` | STRING | Human-readable name |
| `min_commitment` | DECIMAL(20,2) | Minimum contract value for this tier |
| `max_commitment` | DECIMAL(20,2) | Maximum contract value (NULL = unlimited) |
| `duration_years` | INT | Contract duration (1, 2, or 3 years) |
| `discount_rate` | DECIMAL(5,4) | Discount as decimal (0.15 = 15%) |
| `cloud_provider` | STRING | Optional cloud restriction |
| `effective_date` | DATE | When tier becomes active |
| `expiration_date` | DATE | When tier expires |
| `notes` | STRING | Optional description |
| `created_at` | TIMESTAMP | Record creation time |

### discount_scenarios

Generated What-If discount scenarios per contract.

| Column | Type | Description |
|--------|------|-------------|
| `scenario_id` | STRING | Primary key - unique scenario identifier |
| `contract_id` | STRING | Foreign key to contracts |
| `scenario_name` | STRING | Display name (e.g., "10% Discount") |
| `discount_pct` | DECIMAL(5,4) | Applied discount rate |
| `is_baseline` | BOOLEAN | True for 0% baseline scenario |
| `is_extension` | BOOLEAN | True for "If X-year commit" scenarios |
| `extension_years` | INT | Extended duration for extension scenarios |
| `tier_id` | STRING | Reference to discount_tiers |
| `status` | STRING | ACTIVE or ARCHIVED |
| `created_at` | TIMESTAMP | Record creation time |

### scenario_summary

Denormalized KPIs for dashboard queries.

| Column | Type | Description |
|--------|------|-------------|
| `scenario_id` | STRING | Primary key - foreign key to discount_scenarios |
| `contract_id` | STRING | Foreign key to contracts |
| `cumulative_savings` | DECIMAL(20,2) | Total savings with discount applied |
| `scenario_exhaustion_date` | DATE | Predicted exhaustion with discount |
| `days_extended` | INT | Extra days vs baseline |
| `utilization_pct` | DECIMAL(10,4) | Projected utilization percentage |
| `is_sweet_spot` | BOOLEAN | True if recommended scenario |
| `last_calculated` | TIMESTAMP | When KPIs were computed |

### dashboard_data

Aggregated billing data for dashboard queries.

| Column | Type | Description |
|--------|------|-------------|
| `usage_date` | DATE | Date of usage |
| `account_id` | STRING | Databricks account ID |
| `workspace_id` | STRING | Workspace identifier |
| `sku_name` | STRING | SKU designation |
| `cloud` | STRING | Cloud provider |
| `usage_quantity` | DECIMAL(20,6) | DBUs consumed |
| `actual_cost` | DECIMAL(20,2) | Calculated cost |
| `product_category` | STRING | Categorized product type |

---

## Databricks System Tables (Read-Only)

This section documents the actual schema from Databricks system tables as of 2026.

## system.billing.usage

Location: `system.billing.usage`

### Main Columns

| Column | Type | Description |
|--------|------|-------------|
| `record_id` | STRING | Unique ID for this usage record |
| `account_id` | STRING | Account identifier for the report |
| `workspace_id` | STRING | Workspace association identifier |
| `sku_name` | STRING | SKU designation (e.g., STANDARD_ALL_PURPOSE_COMPUTE) |
| `cloud` | STRING | Cloud provider: aws, azure, or gcp |
| `usage_start_time` | TIMESTAMP | The start time relevant to this usage record (UTC) |
| `usage_end_time` | TIMESTAMP | The end time relevant to this usage record (UTC) |
| `usage_date` | DATE | Date field for efficient date-based aggregation |
| `custom_tags` | MAP<STRING, STRING> | User-defined tags associated with usage |
| `usage_unit` | STRING | Measurement unit (typically DBU) |
| `usage_quantity` | DECIMAL | Number of units consumed for this record |
| `usage_metadata` | STRUCT | Resource and job identifiers |
| `identity_metadata` | STRUCT | User/principal information |
| `record_type` | STRING | ORIGINAL, RETRACTION, or RESTATEMENT |
| `ingestion_date` | DATE | Date record entered the table |
| `billing_origin_product` | STRING | Product originating the usage |
| `product_features` | STRUCT | Feature-specific details |
| `usage_type` | STRING | Category: COMPUTE_TIME, STORAGE_SPACE, etc. |

### usage_metadata Struct

```sql
usage_metadata: STRUCT<
  cluster_id: STRING,
  job_id: STRING,
  warehouse_id: STRING,
  instance_pool_id: STRING,
  node_type: STRING,
  job_run_id: STRING,
  notebook_id: STRING,
  dlt_pipeline_id: STRING,
  endpoint_name: STRING,
  endpoint_id: STRING,
  dlt_update_id: STRING,
  dlt_maintenance_id: STRING,
  metastore_id: STRING,
  run_name: STRING,
  job_name: STRING,
  notebook_path: STRING,
  central_clean_room_id: STRING,
  source_region: STRING,
  destination_region: STRING,
  app_id: STRING,
  app_name: STRING,
  budget_policy_id: STRING,
  storage_api_type: STRING,
  ai_runtime_workload_id: STRING,
  uc_table_catalog: STRING,
  uc_table_schema: STRING,
  uc_table_name: STRING,
  database_instance_id: STRING,
  sharing_materialization_id: STRING,
  usage_policy_id: STRING,
  agent_bricks_id: STRING,
  base_environment_id: STRING
>
```

### identity_metadata Struct

```sql
identity_metadata: STRUCT<
  run_as: STRING,        -- User/service principal executing the workload
  owned_by: STRING,      -- SQL warehouse owner
  created_by: STRING     -- App/Agent Bricks creator email
>
```

## system.billing.list_prices

Location: `system.billing.list_prices`

### Main Columns

| Column | Type | Description |
|--------|------|-------------|
| `price_start_time` | TIMESTAMP | The time this price became effective (UTC) |
| `price_end_time` | TIMESTAMP | The time this price stopped being effective (UTC) - NULL for current price |
| `account_id` | STRING | ID of the account this report was generated for |
| `sku_name` | STRING | Name of the SKU |
| `cloud` | STRING | Cloud provider: aws, azure, or gcp |
| `currency_code` | STRING | The currency this price is expressed in (e.g., USD) |
| `usage_unit` | STRING | The unit of measurement that is monetized |
| `pricing` | STRUCT | Contains pricing information with nested keys |

### pricing Struct

```sql
pricing: STRUCT<
  default: STRING,                            -- Standard list price
  promotional: STRUCT<default: STRING>,       -- Promotional pricing
  effective_list: STRUCT<default: STRING>     -- Resolved price for calculations
>
```

Example:
```json
{
  "default": "0.10",
  "promotional": {"default": "0.07"},
  "effective_list": {"default": "0.07"}
}
```

## Important Notes

### Cost Calculation

**There is NO total_price column in system.billing.usage!**

You must calculate cost by joining with list_prices:

```sql
SELECT
  u.usage_quantity,
  CAST(lp.pricing.effective_list.default AS DECIMAL(20, 10)) as price_per_unit,
  u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20, 10)) as calculated_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
```

### Join Pattern for Pricing

Always use this pattern when joining usage with list_prices:

```sql
ON usage.sku_name = list_prices.sku_name
AND usage.cloud = list_prices.cloud
AND usage.usage_unit = list_prices.usage_unit
AND usage.usage_end_time >= list_prices.price_start_time
AND (list_prices.price_end_time IS NULL OR usage.usage_end_time < list_prices.price_end_time)
```

### Filtering by Date

Always filter on `usage_date` (not usage_start_time or usage_end_time) for performance:

```sql
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
```

### Excluding Corrections

To exclude retraction and restatement records:

```sql
WHERE record_type = 'ORIGINAL'
```

Or to include corrections but handle them properly:

```sql
-- Corrections will have negative usage_quantity for RETRACTION records
GROUP BY <dimensions>
HAVING SUM(usage_quantity) > 0
```

## Unity Catalog Setup

### Custom Tables Catalog Structure

Use Unity Catalog for all custom tables:

```
<your_catalog>.account_monitoring.contracts
<your_catalog>.account_monitoring.account_metadata
<your_catalog>.account_monitoring.dashboard_data
```

**Default catalog name**: Use `main` or your organization's standard catalog.

### Creating Unity Catalog Tables

```sql
-- Set default catalog
USE CATALOG main;

-- Create schema
CREATE SCHEMA IF NOT EXISTS account_monitoring
COMMENT 'Account monitoring and cost tracking';

-- Create table
CREATE TABLE IF NOT EXISTS main.account_monitoring.contracts (
  contract_id STRING NOT NULL,
  account_id STRING NOT NULL,
  -- ... other fields
  CONSTRAINT pk_contracts PRIMARY KEY (contract_id)
) USING DELTA;
```

## Common Query Patterns

### Daily Cost Summary

```sql
SELECT
  u.usage_date,
  u.cloud,
  SUM(u.usage_quantity) as total_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.usage_date, u.cloud
ORDER BY u.usage_date DESC;
```

### Workspace Cost Analysis

```sql
SELECT
  u.workspace_id,
  COUNT(DISTINCT u.usage_date) as active_days,
  SUM(u.usage_quantity) as total_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.record_type = 'ORIGINAL'
GROUP BY u.workspace_id
ORDER BY total_cost DESC;
```

### Job Cost Analysis

```sql
SELECT
  u.usage_metadata.job_id,
  u.usage_metadata.job_name,
  COUNT(DISTINCT u.usage_metadata.job_run_id) as run_count,
  SUM(u.usage_quantity) as total_dbu,
  SUM(u.usage_quantity * CAST(lp.pricing.effective_list.default AS DECIMAL(20,10))) as total_cost
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
  ON u.sku_name = lp.sku_name
  AND u.cloud = lp.cloud
  AND u.usage_unit = lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND u.record_type = 'ORIGINAL'
  AND u.usage_metadata.job_id IS NOT NULL
GROUP BY u.usage_metadata.job_id, u.usage_metadata.job_name
ORDER BY total_cost DESC;
```

## References

- [Billable usage system table reference - Databricks on AWS](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Pricing system table reference - Databricks on AWS](https://docs.databricks.com/aws/en/admin/system-tables/pricing)
- [Monitor costs using system tables](https://docs.databricks.com/aws/en/admin/usage/system-tables)
