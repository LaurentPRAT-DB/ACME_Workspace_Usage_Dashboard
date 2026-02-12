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
- [Scheduled Jobs (Detailed)](scheduled_jobs_guide.md) - In-depth job explanations with examples
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - DAB deployment details
- [Configuration Guide](CONFIGURATION_GUIDE.md) - Configuration options

---

## Developer / Data Engineer / Contributor

*Technical documentation for understanding and extending the system.*

| Document | Description |
|----------|-------------|
| [Technical Reference](developer/TECHNICAL_REFERENCE.md) | Architecture, schema, SQL patterns, debugging |
| [Schema Reference](SCHEMA_REFERENCE.md) | Detailed table and column documentation |
| [Quick Reference](QUICK_REFERENCE.md) | Common SQL queries |

**DAB (Databricks Asset Bundles):**
- [DAB README](DAB_README.md) - Bundle structure overview
- [DAB Quick Commands](DAB_QUICK_COMMANDS.md) - CLI command reference
- [Databricks Asset Bundle](DATABRICKS_ASSET_BUNDLE.md) - Detailed DAB documentation

**Additional Technical Docs:**
- [Contract Burndown Guide](CONTRACT_BURNDOWN_GUIDE.md) - Burndown calculation logic
- [Lakeview Dashboard Guide](AIBI_LAKEVIEW_DASHBOARD_GUIDE.md) - Dashboard JSON structure

---

## Quick Start Paths

### First Time Setup (15 minutes)
1. [Getting Started](GETTING_STARTED.md) - Quick start guide
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

### Core Guides
| File | Description | Audience |
|------|-------------|----------|
| [README.md](README.md) | Project README | All |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick start | All |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview | All |
| [START_HERE.md](START_HERE.md) | Entry point | New users |

### Operations
| File | Description | Audience |
|------|-------------|----------|
| [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) | Operations manual | Admin |
| [scheduled_jobs_guide.md](scheduled_jobs_guide.md) | Job details | Admin |
| [POST_DEPLOYMENT_VALIDATION.md](POST_DEPLOYMENT_VALIDATION.md) | Validation steps | Admin |

### Configuration
| File | Description | Audience |
|------|-------------|----------|
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | Configuration options | Admin/Dev |
| [CONFIG_QUICK_REFERENCE.md](CONFIG_QUICK_REFERENCE.md) | Config quick ref | Admin/Dev |
| [TEAM_DEPLOYMENT_GUIDE.md](TEAM_DEPLOYMENT_GUIDE.md) | Team deployments | Admin |

### Dashboard
| File | Description | Audience |
|------|-------------|----------|
| [DASHBOARD_QUICK_START.md](DASHBOARD_QUICK_START.md) | Dashboard setup | Admin |
| [AIBI_LAKEVIEW_DASHBOARD_GUIDE.md](AIBI_LAKEVIEW_DASHBOARD_GUIDE.md) | Dashboard internals | Developer |

### Reference
| File | Description | Audience |
|------|-------------|----------|
| [SCHEMA_REFERENCE.md](SCHEMA_REFERENCE.md) | Table schemas | Developer |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | SQL queries | All |
| [CONTRACT_BURNDOWN_GUIDE.md](CONTRACT_BURNDOWN_GUIDE.md) | Burndown logic | Developer |

### Exploration (Design Documents)
| File | Description |
|------|-------------|
| [exploration/IMPLEMENTATION_PLAN.md](exploration/IMPLEMENTATION_PLAN.md) | Original implementation plan |
| [exploration/data_model_approach.md](exploration/data_model_approach.md) | Data model design |
| [exploration/simulation_engine_approach.md](exploration/simulation_engine_approach.md) | What-If engine design |

### Archive (Historical)
Development logs, bug fixes, and historical documentation are in `archive/`.
See [archive/archive_readme.md](archive/archive_readme.md) for index.

---

## Version Information

- **Current Version:** 1.13.0
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
