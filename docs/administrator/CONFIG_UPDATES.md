# Account Monitor - Configuration Updates Guide

**For: System Administrators, FinOps Engineers**

How to update contracts and discount tiers in the Account Monitor system.

---

## Overview

The Account Monitor uses YAML configuration files as the source of truth:

| Configuration | File | Purpose |
|---------------|------|---------|
| Contracts | `config/contracts.yml` | Define contract commitments |
| Discount Tiers | `config/discount_tiers.yml` | Define discount rates by commitment/duration |

---

## Adding or Modifying Contracts

### Step-by-Step Process

#### Step 1: Edit the Contract Configuration

Edit `config/contracts.yml` to add or modify contracts:

```yaml
contracts:
  # Existing contract
  - contract_id: "CONTRACT-001"
    cloud_provider: "AWS"
    start_date: "2026-01-01"
    end_date: "2026-12-31"
    total_value: 500000.00
    currency: "USD"
    commitment_type: "SPEND"
    status: "ACTIVE"
    notes: "Annual enterprise contract"

  # NEW: Add a new contract
  - contract_id: "CONTRACT-002"
    cloud_provider: "AZURE"
    start_date: "2026-06-01"
    end_date: "2027-05-31"
    total_value: 250000.00
    currency: "USD"
    commitment_type: "SPEND"
    status: "ACTIVE"
    notes: "Azure expansion contract"
```

**Important**: Keep ALL existing contracts in the file. The setup job replaces all contracts with what's in the YAML.

#### Step 2: Deploy the Updated Configuration

```bash
# Deploy to sync the config file to workspace
databricks bundle deploy --target prod --profile YOUR_PROFILE
```

#### Step 3: Run the Setup Job

```bash
# Load contracts from the updated config
databricks bundle run account_monitor_setup --target prod --profile YOUR_PROFILE
```

This job:
- Creates schema if needed
- Loads all contracts from config
- Does NOT run ML training or What-If analysis

#### Step 4: Refresh Data and Forecasts

```bash
# Refresh billing data for new contracts
databricks bundle run account_monitor_daily_refresh --target prod --profile YOUR_PROFILE

# Retrain ML model and regenerate What-If scenarios
databricks bundle run account_monitor_weekly_training --target prod --profile YOUR_PROFILE
```

### Complete Command Sequence

```bash
# Full update sequence for contracts
databricks bundle deploy --target prod --profile YOUR_PROFILE
databricks bundle run account_monitor_setup --target prod --profile YOUR_PROFILE
databricks bundle run account_monitor_daily_refresh --target prod --profile YOUR_PROFILE
databricks bundle run account_monitor_weekly_training --target prod --profile YOUR_PROFILE
```

**Estimated Time**: ~15-20 minutes total

---

## Contract Configuration Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | string | Unique identifier (e.g., "CONTRACT-001") |
| `total_value` | number | Commitment amount in dollars |
| `status` | string | "ACTIVE", "INACTIVE", or "EXPIRED" |

### Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `cloud_provider` | "auto" | "AWS", "AZURE", "GCP", or "auto" (detect) |
| `start_date` | "auto" | YYYY-MM-DD or "auto" (1 year ago) |
| `end_date` | "auto" | YYYY-MM-DD or "auto" (1 year from now) |
| `currency` | "USD" | Currency code |
| `commitment_type` | "SPEND" | "SPEND" or "DBU" |
| `notes` | null | Optional description |

### Example Configurations

**Single Cloud Contract:**
```yaml
- contract_id: "AWS-2026"
  cloud_provider: "AWS"
  start_date: "2026-01-01"
  end_date: "2026-12-31"
  total_value: 500000.00
  status: "ACTIVE"
```

**Multi-Year Contract:**
```yaml
- contract_id: "ENTERPRISE-3YR"
  cloud_provider: "auto"
  start_date: "2026-01-01"
  end_date: "2028-12-31"
  total_value: 1500000.00
  status: "ACTIVE"
  notes: "3-year enterprise agreement"
```

**DBU Commitment:**
```yaml
- contract_id: "DBU-COMMIT-2026"
  cloud_provider: "AWS"
  start_date: "2026-01-01"
  end_date: "2026-12-31"
  total_value: 1000000  # DBU units, not dollars
  commitment_type: "DBU"
  status: "ACTIVE"
```

---

## Modifying Existing Contracts

To modify an existing contract:

1. Find the contract in `config/contracts.yml`
2. Update the fields you need to change
3. Run the deployment and setup commands

```yaml
# Before
- contract_id: "CONTRACT-001"
  total_value: 500000.00
  status: "ACTIVE"

# After - increased commitment
- contract_id: "CONTRACT-001"
  total_value: 750000.00  # Updated value
  status: "ACTIVE"
  notes: "Amendment: +$250K added Q3"
```

---

## Deactivating a Contract

To deactivate a contract, set `status: "INACTIVE"`:

```yaml
- contract_id: "OLD-CONTRACT"
  total_value: 100000.00
  status: "INACTIVE"  # Changed from ACTIVE
  notes: "Contract expired, keeping for historical data"
```

Inactive contracts:
- Remain in the database for historical reporting
- Are excluded from burndown calculations
- Are excluded from What-If analysis

---

## Using Multiple Config Files

For complex scenarios, use multiple contract files:

```bash
# Deploy with multiple config files
databricks bundle run account_monitor_setup \
  --target prod \
  --profile YOUR_PROFILE \
  --notebook-params config_files="config/contracts.yml,config/contracts_emea.yml"
```

This merges contracts from all specified files.

---

## Troubleshooting

### Contract Not Appearing in Dashboard

1. Verify contract is in the YAML with `status: "ACTIVE"`
2. Check that setup job completed successfully
3. Run daily refresh to pull billing data
4. Verify contract dates include current date

### Contract Shows Zero Consumption

1. Check `cloud_provider` matches your actual usage
2. Verify `start_date` is in the past
3. Check billing data exists in `system.billing.usage`

### What-If Scenarios Not Generated

1. Run weekly training job after adding contracts
2. Verify discount tiers exist for the contract's commitment level

---

---

## Updating Discount Tiers

Discount tiers define the discount rates available for different commitment levels and contract durations. Use the lightweight update job for tier changes.

### Step-by-Step Process

#### Step 1: Edit the Discount Tiers Configuration

Edit `config/discount_tiers.yml` to add or modify tiers:

```yaml
discount_tiers:
  # Existing tier
  - tier_id: "TIER_100K_1Y"
    tier_name: "Standard - 1 Year"
    min_commitment: 100000
    max_commitment: 249999
    duration_years: 1
    discount_rate: 0.10
    notes: "Standard commit, 1 year term"

  # NEW: Add a custom tier
  - tier_id: "TIER_CUSTOM_2Y"
    tier_name: "Custom - 2 Year"
    min_commitment: 75000
    max_commitment: 149999
    duration_years: 2
    discount_rate: 0.12
    notes: "Custom mid-tier for specific customers"
```

#### Step 2: Deploy the Updated Configuration

```bash
databricks bundle deploy --target prod --profile YOUR_PROFILE
```

#### Step 3: Run the Lightweight Update Job

```bash
databricks bundle run account_monitor_update_discount_tiers --target prod --profile YOUR_PROFILE
```

This job:
- **MERGES** tiers (inserts new, updates changed, keeps existing)
- Does NOT delete existing tiers
- Automatically regenerates What-If scenarios

**Estimated Time**: ~5 minutes

### Complete Command Sequence

```bash
# Update discount tiers (lightweight)
databricks bundle deploy --target prod --profile YOUR_PROFILE
databricks bundle run account_monitor_update_discount_tiers --target prod --profile YOUR_PROFILE
```

### Alternative: Use Pre-Built Tier Configurations

Three alternative tier configurations are available in `config/files/`:

| File | Strategy | Discount Range |
|------|----------|----------------|
| `discount_tiers_alternative1_market_aligned.yml` | Conservative | 10% - 50% |
| `discount_tiers_alternative2_aggressive.yml` | Competitive | 12% - 55% |
| `discount_tiers_alternative3_stackable.yml` | Complex | 8% - 68%+ |

To use an alternative configuration:

```bash
databricks bundle run account_monitor_update_discount_tiers \
  --target prod \
  --profile YOUR_PROFILE \
  --notebook-params discount_tiers_file="config/files/discount_tiers_alternative2_aggressive.yml"
```

---

## Discount Tier Configuration Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `tier_id` | string | Unique identifier (e.g., "TIER_100K_1Y") |
| `tier_name` | string | Human-readable name |
| `min_commitment` | number | Minimum contract value |
| `duration_years` | number | Contract duration (1-5) |
| `discount_rate` | decimal | Discount as decimal (0.15 = 15%) |

### Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `max_commitment` | null | Maximum contract value (null = unlimited) |
| `cloud_provider` | null | Restrict to specific cloud |
| `effective_date` | null | When tier becomes active |
| `expiration_date` | null | When tier expires |
| `notes` | null | Description |

### Example Tier Configuration

```yaml
- tier_id: "TIER_250K_3Y"
  tier_name: "Growth - 3 Year"
  min_commitment: 250000
  max_commitment: 499999
  duration_years: 3
  discount_rate: 0.25
  notes: "Growth commit, 3 year term"
```

---

## Comparison: Contract Update vs Tier Update

| Aspect | Contract Update | Discount Tier Update |
|--------|-----------------|----------------------|
| Job | `account_monitor_setup` | `account_monitor_update_discount_tiers` |
| Method | DELETE + INSERT | MERGE (incremental) |
| Impact | Replaces all contracts | Updates only changed tiers |
| Requires | Keep ALL contracts in YAML | Can add individual tiers |
| Regenerates | Nothing (run weekly_training) | What-If scenarios automatically |
| Time | ~15-20 min (with training) | ~5 min |

---

## Related Documents

| Document | Description |
|----------|-------------|
| [ADMIN_GUIDE.md](ADMIN_GUIDE.md) | Administrator overview |
| [INSTALLATION.md](INSTALLATION.md) | Initial setup |

---

*Last updated: February 2026*
