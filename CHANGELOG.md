# Changelog

All notable changes to the Databricks Account Monitor project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.18.0] - 2026-02-24

### Added
- **Auto-Commit Optimizer**: ML-based optimal contract commitment recommendations
  - New `auto_commit_optimizer.py` notebook for analyzing historical consumption
  - Prophet ML forecasting to predict future consumption over contract period
  - Evaluates commitment candidates at discount tier boundaries
  - Provides optimal, conservative, and aggressive recommendations with ROI scores
- **`total_value: "auto"` support**: Set contract commitment to "auto" in config to auto-calculate optimal value
  - Targets 95% utilization by default
  - Analyzes last 365 days of historical consumption
  - Rounds to nearest $1,000 for cleaner numbers
- New tables: `auto_commit_recommendations`, `auto_commit_scenarios`, `auto_commit_forecast_detail`
- New views: `auto_commit_latest`, `auto_commit_summary`

### Changed
- Updated `setup_contracts.py` to support `total_value: "auto"` configuration
- Added auto-commit schema creation to first install job

---

## [1.17.0] - 2026-02-12

### Changed
- Skip redundant extension scenarios when shorter extension reaches 100% utilization
- Improved What-If simulation efficiency by filtering impossible scenarios

---

## [1.16.0] - 2026-02-12

### Added
- Lightweight discount tier update job with MERGE-based incremental updates
- New `update_discount_tiers.py` notebook for tier management

### Changed
- Discount tier updates now use MERGE instead of DELETE/INSERT for better performance

---

## [1.15.0] - 2026-02-11

### Changed
- Reorganized documentation by persona (Executive, Administrator, Developer)
- Improved documentation navigation with role-based paths

---

## [1.14.0] - 2026-02-11

### Added
- Created persona-based documentation structure with new guides
- Added `docs/INDEX.md` as central documentation hub

---

## [1.13.0] - 2026-02-12

### Added
- Weekly Operations dashboard page with anomaly detection
- Monthly Summary dashboard page with MoM trends
- 14 new dashboard widgets for operational insights

---

## [1.12.0] - 2026-02-11

### Changed
- Simplified What-If page with enhanced Strategy & Savings widget
- Live contract data display in What-If analysis

---

## [1.11.0] - 2026-02-08

### Added
- Comprehensive Administrator Operations Guide
- Health monitoring procedures
- Data quality checks
- Emergency procedures documentation

---

## [1.10.0] - 2026-02-07

### Added
- **What-If Discount Simulation**: Tier-based discount scenario analysis
  - Duration-based discount tiers (longer contracts = higher discounts)
  - Pre-computed scenarios at 0%, 5%, 10%, 15%, 20%+ discount levels
  - Sweet spot detection (max savings with >=85% utilization)
  - Break-even analysis and exhaustion extension calculations
- New tables: `discount_tiers`, `discount_scenarios`, `scenario_burndown`, `scenario_forecast`, `scenario_summary`

---

## [1.9.0] - 2026-02-06

### Changed
- Simplified dashboard to 2 pages (Executive Summary, Contract Burndown)
- Optimized bundle sync configuration for faster deployments

### Removed
- Prophet Forecasts page (consolidated into Contract Burndown)
- Usage Analytics page (metrics available in Executive Summary)

---

## [1.8.0] - 2026-02-05

### Added
- Quick Start first-install guide with step-by-step workflow
- One-command install process via `account_monitor_first_install` job

---

## [1.7.0] - 2026-02-05

### Added
- **Prophet ML Forecasting**: Time-series predictions for contract exhaustion
  - Automatic Prophet installation on serverless compute
  - Weekly model retraining schedule
  - Exhaustion date predictions (P10, P50, P90 confidence levels)
- New `consumption_forecaster.py` notebook
- New `contract_forecast` table

---

## [1.6.1] - 2026-02-04

### Changed
- Removed `salesforce_id` column from contracts table
- Added `notes` column for contract descriptions

---

## [1.5.0] - 2026-02-01

### Added
- Initial stable release
- Contract consumption monitoring with burndown analysis
- Lakeview dashboard with Executive Summary
- Databricks Asset Bundle (DAB) deployment
- YAML-based contract configuration
- Daily refresh and weekly training jobs

---

## Version Numbering

- **Major (X.0.0)**: Breaking changes, schema migrations required
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, documentation updates

---

## Links

- [README](README.md) - Project overview and quick start
- [Documentation Index](docs/INDEX.md) - Full documentation
- [Schema Reference](docs/developer/SCHEMA_REFERENCE.md) - Table schemas
