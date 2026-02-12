# Account Monitor - Documentation Index

## Choose Your Path

Documentation is organized by role. Pick your persona to find relevant guides:

---

## Executive / Finance / FinOps

*Business-focused documentation for stakeholders, finance teams, and contract negotiators.*

| Document | Description |
|----------|-------------|
| [Executive Summary](executive/EXECUTIVE_SUMMARY.md) | What the system does and why it matters |
| [Dashboard Overview](executive/DASHBOARD_OVERVIEW.md) | Visual guide to using the dashboard |
| [Contract Optimization Strategy](executive/CONTRACT_OPTIMIZATION_STRATEGY.md) | How to optimize contract negotiations |

**Quick Links:**
- [User Guide](user-guide/USER_GUIDE.md) - End-user documentation

---

## Administrator / DevOps / FinOps Engineer

*Installation, operations, and maintenance documentation.*

| Document | Description |
|----------|-------------|
| [Admin Guide](administrator/ADMIN_GUIDE.md) | System overview and quick reference |
| [Installation Guide](administrator/INSTALLATION.md) | Step-by-step installation |
| [Scheduled Jobs Guide](administrator/SCHEDULED_JOBS.md) | Job descriptions and monitoring |
| [Operations Checklist](administrator/OPERATIONS_CHECKLIST.md) | Daily/weekly/monthly checklists |
| [Troubleshooting](administrator/TROUBLESHOOTING.md) | Common issues and solutions |

**Additional Resources:**
- [Deployment Guide](administrator/DEPLOYMENT_GUIDE.md) - DAB deployment details
- [Configuration Guide](administrator/CONFIGURATION_GUIDE.md) - Configuration options
- [Post-Deployment Validation](administrator/POST_DEPLOYMENT_VALIDATION.md) - Validation steps
- [Team Deployment Guide](administrator/TEAM_DEPLOYMENT_GUIDE.md) - Multi-team deployments
- [Dashboard Quick Start](administrator/DASHBOARD_QUICK_START.md) - Dashboard setup

---

## Developer / Data Engineer / Contributor

*Technical documentation for understanding and extending the system.*

| Document | Description |
|----------|-------------|
| [Technical Reference](developer/TECHNICAL_REFERENCE.md) | Architecture, schema, SQL patterns, debugging |
| [Schema Reference](developer/SCHEMA_REFERENCE.md) | Detailed table and column documentation |
| [Quick Reference](developer/QUICK_REFERENCE.md) | Common SQL queries |

**DAB (Databricks Asset Bundles):**
- [DAB README](developer/DAB_README.md) - Bundle structure overview
- [DAB Quick Commands](developer/DAB_QUICK_COMMANDS.md) - CLI command reference
- [Databricks Asset Bundle](developer/DATABRICKS_ASSET_BUNDLE.md) - Detailed DAB documentation

**Additional Technical Docs:**
- [Contract Burndown Guide](developer/CONTRACT_BURNDOWN_GUIDE.md) - Burndown calculation logic
- [Lakeview Dashboard Guide](developer/AIBI_LAKEVIEW_DASHBOARD_GUIDE.md) - Dashboard JSON structure

---

## Quick Start Paths

### First Time Setup (15 minutes)
1. [Start Here](START_HERE.md) - Quick start guide
2. [Installation Guide](administrator/INSTALLATION.md) - Deploy the system
3. [Dashboard Overview](executive/DASHBOARD_OVERVIEW.md) - Learn the dashboard

### Understanding the System
1. [Executive Summary](executive/EXECUTIVE_SUMMARY.md) - Business overview
2. [Admin Guide](administrator/ADMIN_GUIDE.md) - System architecture
3. [Technical Reference](developer/TECHNICAL_REFERENCE.md) - Deep technical details

### Contract Renewal Preparation
1. [Contract Optimization Strategy](executive/CONTRACT_OPTIMIZATION_STRATEGY.md) - Negotiation guide
2. [Dashboard Overview](executive/DASHBOARD_OVERVIEW.md) - Using What-If Analysis
3. [User Guide](user-guide/USER_GUIDE.md) - Detailed feature guide

### Troubleshooting Issues
1. [Troubleshooting](administrator/TROUBLESHOOTING.md) - Common issues
2. [Operations Checklist](administrator/OPERATIONS_CHECKLIST.md) - Diagnostic steps
3. [Technical Reference](developer/TECHNICAL_REFERENCE.md) - SQL patterns & debugging

---

## All Documentation

### Core Guides (Root)
| File | Description | Audience |
|------|-------------|----------|
| [START_HERE.md](START_HERE.md) | Quick start guide | New users |

### Executive
| File | Description |
|------|-------------|
| [EXECUTIVE_SUMMARY.md](executive/EXECUTIVE_SUMMARY.md) | Business value overview |
| [DASHBOARD_OVERVIEW.md](executive/DASHBOARD_OVERVIEW.md) | Visual dashboard guide |
| [CONTRACT_OPTIMIZATION_STRATEGY.md](executive/CONTRACT_OPTIMIZATION_STRATEGY.md) | Negotiation strategy |

### Administrator
| File | Description |
|------|-------------|
| [ADMIN_GUIDE.md](administrator/ADMIN_GUIDE.md) | Admin quick reference |
| [INSTALLATION.md](administrator/INSTALLATION.md) | Installation steps |
| [SCHEDULED_JOBS.md](administrator/SCHEDULED_JOBS.md) | Job monitoring |
| [CONFIG_UPDATES.md](administrator/CONFIG_UPDATES.md) | Contract & tier updates |
| [OPERATIONS_CHECKLIST.md](administrator/OPERATIONS_CHECKLIST.md) | Printable checklists |
| [TROUBLESHOOTING.md](administrator/TROUBLESHOOTING.md) | Issue resolution |
| [DEPLOYMENT_GUIDE.md](administrator/DEPLOYMENT_GUIDE.md) | DAB deployment |
| [CONFIGURATION_GUIDE.md](administrator/CONFIGURATION_GUIDE.md) | Config options |
| [CONFIG_QUICK_REFERENCE.md](administrator/CONFIG_QUICK_REFERENCE.md) | Config quick ref |
| [POST_DEPLOYMENT_VALIDATION.md](administrator/POST_DEPLOYMENT_VALIDATION.md) | Validation |
| [TEAM_DEPLOYMENT_GUIDE.md](administrator/TEAM_DEPLOYMENT_GUIDE.md) | Team deployments |
| [DASHBOARD_QUICK_START.md](administrator/DASHBOARD_QUICK_START.md) | Dashboard setup |

### Developer
| File | Description |
|------|-------------|
| [TECHNICAL_REFERENCE.md](developer/TECHNICAL_REFERENCE.md) | Architecture & patterns |
| [SCHEMA_REFERENCE.md](developer/SCHEMA_REFERENCE.md) | Table schemas |
| [QUICK_REFERENCE.md](developer/QUICK_REFERENCE.md) | SQL queries |
| [DAB_README.md](developer/DAB_README.md) | Bundle overview |
| [DAB_QUICK_COMMANDS.md](developer/DAB_QUICK_COMMANDS.md) | CLI commands |
| [DATABRICKS_ASSET_BUNDLE.md](developer/DATABRICKS_ASSET_BUNDLE.md) | DAB details |
| [CONTRACT_BURNDOWN_GUIDE.md](developer/CONTRACT_BURNDOWN_GUIDE.md) | Burndown logic |
| [AIBI_LAKEVIEW_DASHBOARD_GUIDE.md](developer/AIBI_LAKEVIEW_DASHBOARD_GUIDE.md) | Dashboard JSON |

### Exploration (Design Documents)
| File | Description |
|------|-------------|
| [IMPLEMENTATION_PLAN.md](exploration/IMPLEMENTATION_PLAN.md) | Original implementation plan |
| [data_model_approach.md](exploration/data_model_approach.md) | Data model design |
| [simulation_engine_approach.md](exploration/simulation_engine_approach.md) | What-If engine design |

### Archive (Historical)
Development logs, bug fixes, and superseded documentation.
See [archive/archive_readme.md](archive/archive_readme.md) for index.

---

## Version Information

- **Current Version:** 1.16.0
- **Last Updated:** February 2026
- **Databricks Runtime:** 13.0+

---

## Need Help?

| Question | Where to Look |
|----------|---------------|
| How do I install? | [Installation Guide](administrator/INSTALLATION.md) |
| What does this metric mean? | [Dashboard Overview](executive/DASHBOARD_OVERVIEW.md) |
| Why isn't the job running? | [Troubleshooting](administrator/TROUBLESHOOTING.md) |
| How do I add a contract? | [Admin Guide](administrator/ADMIN_GUIDE.md#managing-contracts) |
| What discount should I choose? | [Contract Optimization](executive/CONTRACT_OPTIMIZATION_STRATEGY.md) |

---

*Documentation organized by persona for easier navigation.*
