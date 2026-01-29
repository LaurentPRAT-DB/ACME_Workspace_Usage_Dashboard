# 🚀 Notebook Fix Quick Reference

**Quick access guide for fixing Databricks notebooks**

---

## Quick Fix (Automated)

Use the helper script to automate versioning and deployment:

```bash
# Fix a notebook with automatic version bump
./scripts/notebook_fix.sh notebooks/account_monitor_notebook.py "Fix SQL parameter issue"

# The script will:
# ✓ Auto-increment version (1.5.4 → 1.5.5)
# ✓ Generate new build number (2026-01-29-015)
# ✓ Stage and commit changes
# ✓ Push to remote
# ✓ Deploy to Databricks
```

---

## Manual Fix (Step-by-Step)

### 1. Fix the Code

```bash
# Edit the notebook
code notebooks/account_monitor_notebook.py

# Or use Edit tool for specific changes
```

### 2. Update Version

**Two locations to update:**

```python
# Location 1: Markdown header
# MAGIC **Version:** 1.5.4 (Build: 2026-01-29-014)
# Change to:
# MAGIC **Version:** 1.5.5 (Build: 2026-01-29-015)

# Location 2: Python constants
VERSION = "1.5.4"
BUILD = "2026-01-29-014"
# Change to:
VERSION = "1.5.5"
BUILD = "2026-01-29-015"
```

### 3. Commit and Deploy

```bash
# Stage
git add notebooks/account_monitor_notebook.py

# Commit
git commit -m "Fix [issue description]

- [Change 1]
- [Change 2]
- Version bumped to 1.5.5 (Build: 2026-01-29-015)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push
git push

# Deploy
databricks bundle deploy
```

---

## Common Fixes

### Fix 1: SQL Parameter Markers

**Issue:** `SQL query contains $ parameter`

```python
# Before
CONCAT('$', FORMAT_NUMBER(amount, 2))

# After
CONCAT('USD ', FORMAT_NUMBER(amount, 2))
```

### Fix 2: Decimal Type Conversion

**Issue:** `TypeError: unsupported operand type(s) for *: 'decimal.Decimal'`

```python
# Before
range=[0, contract_value * 1.1]
days_to_burndown = remaining_budget / daily_avg_spend

# After
range=[0, float(contract_value) * 1.1]
days_to_burndown = float(remaining_budget) / float(daily_avg_spend)
```

### Fix 3: Invalid API Calls

**Issue:** `dbutils.jobs.list() doesn't exist`

```python
# Before
jobs = dbutils.jobs.list()

# After
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
jobs = list(w.jobs.list())
```

### Fix 4: Field Name Errors

**Issue:** `UNRESOLVED_COLUMN` or `FIELD_NOT_FOUND`

```python
# Before
u.cloud_provider  # Wrong field name
lp.pricing.default_price_per_unit  # Wrong nested field

# After
u.cloud  # Correct field name
lp.pricing.default  # Correct nested field
```

---

## Version Numbering

**Format:** `Major.Minor.Patch (Build: YYYY-MM-DD-NNN)`

- **Patch++**: Bug fixes (1.5.4 → 1.5.5)
- **Minor++**: New features (1.5.4 → 1.6.0)
- **Major++**: Breaking changes (1.5.4 → 2.0.0)

**Build Number:**
- Format: `YYYY-MM-DD-NNN`
- Same day: increment NNN (001 → 002)
- New day: reset to 001

---

## Verification Checklist

After deploying, verify:

```bash
# Check workspace file exists
databricks workspace ls /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/

# Check git log
git log -1 --oneline

# Check remote sync
git status
```

In notebook:
- [ ] Run Cell 1 - verify version displays correctly
- [ ] Run affected cell - verify fix works
- [ ] Check for new errors

---

## Troubleshooting

### Script fails with "VERSION not found"

```bash
# Manually add version to notebook:
VERSION = "1.0.0"
BUILD = "2026-01-29-001"
```

### Git push rejected

```bash
git pull --rebase
git push
```

### Deployment fails

```bash
# Validate bundle
databricks bundle validate

# Check authentication
databricks auth profiles
```

### Version not updating in workspace

```bash
# Force deploy
databricks bundle deploy --force-all
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/notebook_fix.sh` | Automated fix script |
| `docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md` | Complete workflow documentation |
| `notebooks/account_monitor_notebook.py` | Main analytics notebook |
| `notebooks/post_deployment_validation.py` | Validation tests |

---

## Need More Help?

- **Full Documentation:** `docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md`
- **Getting Started:** `GETTING_STARTED.md`
- **Operations Guide:** `OPERATIONS_GUIDE.md`

---

**Last Updated:** 2026-01-29
