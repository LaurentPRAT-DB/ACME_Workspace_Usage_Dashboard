# Account Monitor - Administrator Guide

**For: System Administrators, FinOps Engineers, DevOps**

---

## Overview

This guide covers everything you need to install, configure, and maintain the Account Monitor system.

---

## Quick Links

| Task | Document |
|------|----------|
| First-time installation | [Installation Guide](INSTALLATION.md) |
| Understanding scheduled jobs | [Scheduled Jobs Guide](SCHEDULED_JOBS.md) |
| Daily/weekly/monthly tasks | [Operations Checklist](OPERATIONS_CHECKLIST.md) |
| Fixing issues | [Troubleshooting](TROUBLESHOOTING.md) |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Databricks Workspace                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ System Tables │    │ Unity Catalog │    │  Dashboard   │       │
│  │    (source)   │───▶│   (storage)   │───▶│   (output)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                    │               │
│         │                   │                    │               │
│  ┌──────▼──────────────────▼────────────────────▼──────┐        │
│  │                   Scheduled Jobs                      │        │
│  │  • Daily Refresh (2 AM) - Pull consumption data      │        │
│  │  • Weekly Training (Sun) - Retrain ML model          │        │
│  │  • Weekly Review (Mon) - Generate reports            │        │
│  │  • Monthly Summary (1st) - Archive & summarize       │        │
│  └───────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Gets Installed

### Tables (Unity Catalog)

| Table | Purpose | Updated By |
|-------|---------|-----------|
| `contracts` | Contract definitions | Manual / Setup job |
| `dashboard_data` | Aggregated billing data | Daily Refresh |
| `contract_burndown` | Cumulative consumption | Daily Refresh |
| `contract_forecast` | ML predictions | Weekly Training |
| `discount_tiers` | Discount rate config | Setup job |
| `discount_scenarios` | What-If scenarios | Weekly Training |
| `scenario_summary` | Scenario KPIs | Weekly Training |

### Jobs (Automated)

| Job | Schedule | Purpose |
|-----|----------|---------|
| Daily Refresh | 2 AM UTC daily | Pull new billing data |
| Weekly Training | Sunday 8 AM UTC | Retrain Prophet ML model |
| Weekly Review | Monday 8 AM UTC | Generate operational reports |
| Monthly Summary | 1st of month 6 AM UTC | Archive & executive summary |

### Dashboard

**Contract Consumption Monitor** with 5 pages:
1. Executive Summary
2. Contract Burndown
3. Weekly Operations
4. Monthly Summary
5. What-If Analysis

---

## Installation

### Prerequisites

- Databricks workspace with **Unity Catalog** enabled
- Access to **system.billing** tables
- **SQL Warehouse** (serverless recommended)
- **Databricks CLI** installed

### One-Command Install

```bash
# 1. Configure contracts
vi config/contracts.yml

# 2. Deploy
databricks bundle deploy --profile YOUR_PROFILE

# 3. Run first install
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

See [Installation Guide](INSTALLATION.md) for detailed steps.

---

## Configuration

### Contract Configuration

Edit `config/contracts.yml`:

```yaml
account_metadata:
  account_id: "auto"
  customer_name: "Your Company"

contracts:
  - contract_id: "CONTRACT-2026-001"
    cloud_provider: "auto"
    start_date: "2026-01-01"
    end_date: "2026-12-31"
    total_value: 500000.00
    currency: "USD"
    status: "ACTIVE"
```

### Discount Tier Configuration

Edit `config/discount_tiers.yml` to customize discount rates:

```yaml
discount_tiers:
  - tier_id: "TIER_100K_1Y"
    tier_name: "Standard - 1 Year"
    min_commitment: 100000
    max_commitment: 250000
    duration_years: 1
    discount_rate: 0.10
```

### Environment Targets

| Target | Schema | Use Case |
|--------|--------|----------|
| `dev` (default) | `account_monitoring_dev` | Testing |
| `prod` | `account_monitoring` | Production |

Deploy to production:
```bash
databricks bundle deploy --target prod --profile PROD_PROFILE
```

---

## Daily Operations

### Health Check (5 minutes)

1. **Check job status**
   ```bash
   databricks jobs list --profile YOUR_PROFILE | grep account_monitor
   ```

2. **Verify data freshness**
   ```sql
   SELECT MAX(usage_date) as latest_data,
          DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_stale
   FROM main.account_monitoring_dev.contract_burndown;
   ```

3. **Review dashboard** for any anomalies

### Data Freshness Targets

| Table | Acceptable Staleness |
|-------|---------------------|
| `contract_burndown` | ≤ 2 days |
| `contract_forecast` | ≤ 7 days |
| `scenario_summary` | ≤ 7 days |

---

## Weekly Operations

### Monday Morning Checklist

1. **Check Weekly Review job** completed successfully
2. **Review Weekly Operations** dashboard page
3. **Investigate** any cost spikes or anomalies
4. **Check contract pace** - any contracts over/under pace?

### Sunday Night Checklist

1. **Verify Weekly Training** job completed
2. **Check forecast** dates are updated
3. **Review What-If** scenarios refreshed

---

## Monthly Operations

### 1st of Month Checklist

1. **Verify Monthly Summary** job completed
2. **Review Monthly Summary** dashboard page
3. **Export** reports for finance if needed
4. **Check contracts** expiring in next 90 days

### Table Maintenance

```sql
-- Optimize tables monthly
OPTIMIZE main.account_monitoring_dev.contract_burndown;
OPTIMIZE main.account_monitoring_dev.dashboard_data;

-- Analyze for query optimization
ANALYZE TABLE main.account_monitoring_dev.contract_burndown COMPUTE STATISTICS;
```

---

## Managing Contracts

### Adding a New Contract

1. Edit `config/contracts.yml`
2. Redeploy: `databricks bundle deploy --profile YOUR_PROFILE`
3. Re-run setup: `databricks bundle run account_monitor_setup --profile YOUR_PROFILE`

### Modifying a Contract

Option 1: Edit config and redeploy (above)

Option 2: Direct SQL update:
```sql
UPDATE main.account_monitoring_dev.contracts
SET total_value = 600000.00
WHERE contract_id = 'CONTRACT-2026-001';
```

### Deactivating a Contract

```sql
UPDATE main.account_monitoring_dev.contracts
SET status = 'INACTIVE'
WHERE contract_id = 'OLD-CONTRACT';
```

---

## Troubleshooting Quick Reference

| Symptom | Cause | Solution |
|---------|-------|----------|
| Empty dashboard | No data loaded | Run `account_monitor_daily_refresh` |
| Old forecast dates | Training not run | Run `account_monitor_weekly_training` |
| Job failures | Warehouse stopped | Start SQL Warehouse |
| Permission errors | Missing grants | Grant SELECT on system.billing |
| Dashboard errors | Not published | Redeploy with `--force` |

See [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions.

---

## Useful Commands

```bash
# Deploy changes
databricks bundle deploy --profile YOUR_PROFILE

# Force deploy (overwrites dashboard changes)
databricks bundle deploy --force --profile YOUR_PROFILE

# Run specific job
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE

# Check job status
databricks runs list --limit 10 --profile YOUR_PROFILE

# Validate bundle
databricks bundle validate --profile YOUR_PROFILE

# Full reset
databricks bundle run account_monitor_cleanup --profile YOUR_PROFILE
databricks bundle run account_monitor_first_install --profile YOUR_PROFILE
```

---

## Alerting Setup

### SQL Alert: Data Staleness

Create a SQL alert that triggers if data is more than 3 days old:

```sql
SELECT CASE WHEN MAX(days_stale) > 3 THEN 'ALERT' ELSE 'OK' END as status
FROM (
  SELECT DATEDIFF(CURRENT_DATE(), MAX(usage_date)) as days_stale
  FROM main.account_monitoring_dev.contract_burndown
);
```

### SQL Alert: Contract Exhaustion

Alert when a contract will exhaust within 30 days:

```sql
SELECT contract_id, exhaustion_date_p50,
       DATEDIFF(exhaustion_date_p50, CURRENT_DATE()) as days_left
FROM main.account_monitoring_dev.contract_forecast
WHERE exhaustion_date_p50 IS NOT NULL
  AND DATEDIFF(exhaustion_date_p50, CURRENT_DATE()) BETWEEN 1 AND 30;
```

---

## Access Control

### Minimum Permissions Required

```sql
-- Grant system table access (account admin required)
GRANT SELECT ON TABLE system.billing.usage TO `user@company.com`;
GRANT SELECT ON TABLE system.billing.list_prices TO `user@company.com`;

-- Grant schema access
GRANT USE CATALOG ON CATALOG main TO `user@company.com`;
GRANT USE SCHEMA ON SCHEMA main.account_monitoring_dev TO `user@company.com`;
GRANT SELECT ON SCHEMA main.account_monitoring_dev TO `user@company.com`;
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [Installation Guide](INSTALLATION.md) | Detailed installation steps |
| [Scheduled Jobs Guide](SCHEDULED_JOBS.md) | Job descriptions with examples |
| [Operations Checklist](OPERATIONS_CHECKLIST.md) | Printable daily/weekly/monthly checklists |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and solutions |

---

*Last updated: February 2026*
