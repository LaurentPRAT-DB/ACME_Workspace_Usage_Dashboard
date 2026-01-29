# Skill: Notebook Fix and Deployment Workflow

**Version:** 1.0.0
**Created:** 2026-01-29
**Purpose:** Standard workflow for fixing Databricks notebooks with proper versioning and deployment

---

## Overview

This skill documents the complete workflow for identifying, fixing, versioning, and deploying notebook changes in a Databricks Asset Bundle project.

---

## Prerequisites

- Git repository initialized and connected to remote
- Databricks Asset Bundle configured (databricks.yml)
- Databricks CLI authenticated with profile
- Access to Databricks workspace

---

## Workflow Steps

### 1. Identify the Issue

**Tools Used:**
- Error messages from notebook execution
- User reports
- Validation test results

**Example:**
```
Cell 3: SQL query contains $ parameter. Parameter values: 3: <empty>
Cell 9: TypeError: Invalid type <class 'decimal.Decimal'>
Test 11: Jobs Deployed - Cannot verify from notebook
```

**Actions:**
```bash
# Locate the affected file
glob **/*notebook*.py

# Read the file to understand the issue
read notebooks/account_monitor_notebook.py
```

---

### 2. Analyze the Root Cause

**Tools Used:**
- Grep for specific patterns
- Read documentation
- Review related code sections

**Example:**
```bash
# Search for problematic patterns
grep '\$[0-9]' notebooks/account_monitor_notebook.py
grep 'dbutils.jobs.list' notebooks/post_deployment_validation.py
grep 'pd.Timedelta.*days=' notebooks/account_monitor_notebook.py

# Read relevant sections
read notebooks/account_monitor_notebook.py --offset 430 --limit 50
```

**Common Issues:**
- SQL parameter markers (`$` in queries)
- Type conversion errors (Decimal to float)
- Invalid API calls (wrong method names)
- Undefined variables (scope issues)

---

### 3. Fix the Issue

**Edit the file with specific string replacements:**

```python
# Example 1: Fix SQL parameter markers
Edit:
  old_string: "CONCAT('$', FORMAT_NUMBER(...))"
  new_string: "CONCAT('USD ', FORMAT_NUMBER(...))"

# Example 2: Fix Decimal type conversion
Edit:
  old_string: "range=[0, contract_value * 1.1]"
  new_string: "range=[0, float(contract_value) * 1.1]"

# Example 3: Fix invalid API call
Edit:
  old_string: "dbutils.jobs.list()"
  new_string: "WorkspaceClient().jobs.list()"
```

**Best Practices:**
- Make minimal, targeted changes
- Fix one issue at a time for clarity
- Preserve existing logic and structure
- Add error handling where appropriate

---

### 4. Update Version Numbers

**Every fix must increment the version.**

**Version Format:**
- Major.Minor.Patch (e.g., 1.5.3)
- Build: YYYY-MM-DD-NNN (e.g., 2026-01-29-013)

**What to Increment:**
- **Patch**: Bug fixes, minor corrections (e.g., 1.5.2 → 1.5.3)
- **Minor**: New features, significant changes (e.g., 1.5.0 → 1.6.0)
- **Major**: Breaking changes, major refactors (e.g., 1.5.0 → 2.0.0)

**Files to Update:**

```python
# Update markdown header
Edit:
  old_string: "# MAGIC **Version:** 1.5.3 (Build: 2026-01-29-013)"
  new_string: "# MAGIC **Version:** 1.5.4 (Build: 2026-01-29-014)"

# Update Python constants
Edit:
  old_string: 'VERSION = "1.5.3"\nBUILD = "2026-01-29-013"'
  new_string: 'VERSION = "1.5.4"\nBUILD = "2026-01-29-014"'
```

**Verification:**
```bash
# Verify version updated in both places
grep "Version:" notebooks/account_monitor_notebook.py
grep "VERSION = " notebooks/account_monitor_notebook.py
```

---

### 5. Git Operations

**Standard Commit Flow:**

```bash
# Stage the changed file
git add notebooks/account_monitor_notebook.py

# Create descriptive commit message
git commit -m "$(cat <<'EOF'
Fix Decimal type conversion in Cell 9

- Convert contract_value to float in y-axis range calculation
- Convert commitment to float when extracting from DataFrame
- Convert Decimals to float in burndown_pct calculation
- Fixes: TypeError: unsupported operand type(s) for *: 'decimal.Decimal'
- Version bumped to 1.5.3 (Build: 2026-01-29-013)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Push to remote
git push
```

**Commit Message Format:**

```
[Short summary line - 50 chars max]

- [Bullet point describing change 1]
- [Bullet point describing change 2]
- [Bullet point describing change 3]
- Fixes: [Error message or issue description]
- Version bumped to [new version] (Build: [new build])

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Commit Message Best Practices:**
- Use imperative mood ("Fix" not "Fixed" or "Fixes")
- Be specific about what changed
- Include the error message being fixed
- Always mention version bump
- Keep first line under 50 characters

---

### 6. Deploy to Databricks ⚠️ CRITICAL STEP

**⚠️ WARNING: This step is MANDATORY and must NOT be skipped!**

Without deployment, changes exist only in GitHub and are NOT visible in the Databricks workspace.

**Deploy using Databricks Asset Bundle:**

```bash
# Deploy to development environment (default)
databricks bundle deploy -t dev

# Or just (dev is default)
databricks bundle deploy

# For production
databricks bundle deploy -t prod

# Verify deployment
databricks bundle validate
```

**What Happens During Deployment:**
1. Files synced to workspace: `/Workspace/Users/{user}/account_monitor/files/`
2. Notebooks uploaded to workspace (visible in UI)
3. Jobs updated with new definitions
4. Deployment state recorded
5. All resources validated

**Expected Output:**
```
Uploading bundle files to /Workspace/Users/laurent.prat@mailwatcher.net/account_monitor/files...
Deploying resources...
Updating deployment state...
Deployment complete!
```

**Verify Notebooks Are Deployed:**
```bash
# List deployed notebooks
databricks workspace list /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/

# You should see:
# - account_monitor_notebook
# - lakeview_dashboard_queries
# - ibm_style_dashboard_queries
# - post_deployment_validation
# - verify_contract_burndown
```

**Common Mistake:**
❌ Running `git push` and stopping - notebooks NOT updated in workspace
✅ Running `git push` AND `databricks bundle deploy` - notebooks updated everywhere

---

## Complete Example: Fixing Cell 9 Decimal Error

### Step 1: Issue Identified
```
Cell 9: TypeError: unsupported operand type(s) for *: 'decimal.Decimal'
Line 135: range=[0, contract_value * 1.1]
```

### Step 2: Root Cause
```bash
grep "contract_value \* 1.1" notebooks/account_monitor_notebook.py
# Found: contract_value is Decimal from Spark DataFrame
# Issue: pd.Timedelta and plotly require float/int, not Decimal
```

### Step 3: Fix Applied
```python
# Fix 1: Y-axis range
range=[0, float(contract_value) * 1.1]

# Fix 2: Commitment value
commitment = float(contract_data['commitment'].iloc[0])

# Fix 3: Percentage calculation
burndown_pct = (float(max_cumulative) / float(contract_value) * 100)

# Fix 4: Timedelta parameter
projected_burndown_date = last_date + pd.Timedelta(days=float(days_to_burndown))
```

### Step 4: Version Updated
```
From: 1.5.2 (Build: 2026-01-29-012)
To:   1.5.3 (Build: 2026-01-29-013)
```

### Step 5: Git Commit
```bash
git add notebooks/account_monitor_notebook.py
git commit -m "Fix additional Decimal type conversions in Cell 9..."
git push
```

### Step 6: Deploy
```bash
databricks bundle deploy
# ✅ Deployment complete!
```

### Step 7: Verify
```python
# User runs Cell 9 in notebook
# ✅ Chart renders without errors
# ✅ Version displayed: 1.5.3 (Build: 2026-01-29-013)
```

---

## Troubleshooting

### Issue: Git push rejected
```bash
# Pull latest changes first
git pull --rebase
git push
```

### Issue: Merge conflicts
```bash
# Resolve conflicts manually
git status
# Edit conflicted files
git add <resolved-files>
git rebase --continue
git push
```

### Issue: Deployment fails
```bash
# Validate bundle configuration
databricks bundle validate

# Check for syntax errors
python -m py_compile notebooks/account_monitor_notebook.py

# Check profile authentication
databricks auth profiles
```

### Issue: Version not updating in workspace
```bash
# Force sync
databricks bundle deploy --force-all

# Verify file timestamp
databricks workspace get /Users/{user}/account_monitor/files/notebooks/account_monitor_notebook.py
```

---

## Checklist

Use this checklist for every notebook fix:

- [ ] Issue identified and understood
- [ ] Root cause analyzed
- [ ] Fix applied and tested locally (if possible)
- [ ] Version number incremented (both places)
- [ ] Build number incremented
- [ ] Changes staged with `git add`
- [ ] Descriptive commit message written
- [ ] Commit includes version bump note
- [ ] Changes pushed to remote (`git push`)
- [ ] **⚠️ Bundle deployed to Databricks (`databricks bundle deploy -t dev`) - MANDATORY**
- [ ] **⚠️ Deployment confirmed successful (check output)**
- [ ] **⚠️ Notebooks verified in workspace (list notebooks or open in UI)**
- [ ] User notified of fix and new version
- [ ] Issue documented (if recurring)

**STOP: Do not mark this workflow complete without deploying to Databricks!**

---

## Related Files

- `databricks.yml` - Asset bundle configuration
- `notebooks/account_monitor_notebook.py` - Main analytics notebook
- `notebooks/post_deployment_validation.py` - Validation tests
- `.git/config` - Git remote configuration
- `~/.databrickscfg` - Databricks CLI profiles

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.5.4 | 2026-01-29 | Fixed SQL parameter markers in comments |
| 1.5.3 | 2026-01-29 | Fixed Decimal type conversions in Cell 9 |
| 1.5.2 | 2026-01-29 | Fixed SQL parameter syntax throughout |
| 1.5.1 | 2026-01-29 | Fixed Decimal to float conversion in burndown |
| 1.5.0 | 2026-01-29 | Changed burndown chart to horizontal commitment line |

---

## Best Practices Summary

1. **Always increment version** - Every fix gets a new version
2. **Descriptive commits** - Future you will thank present you
3. **Test before deploy** - Validate changes when possible
4. **One fix per commit** - Easier to track and revert
5. **Document breaking changes** - Update README/CHANGELOG
6. **Keep commits atomic** - Each commit should be complete
7. **Push frequently** - Don't lose work
8. **Validate deployment** - Check workspace after deploy
9. **Update documentation** - Keep docs in sync with code
10. **Track recurring issues** - Create skills or automation

---

## Automation Opportunities

**Future Enhancements:**
- Pre-commit hooks for version validation
- Automated version bumping script
- CI/CD pipeline for testing before deployment
- Automated deployment on merge to main
- Version changelog generation from commits
- Slack notifications on deployment

---

## Contact

For questions about this workflow:
- Check `START_HERE.md` for project overview
- Review `OPERATIONS_GUIDE.md` for daily operations
- See `GETTING_STARTED.md` for initial setup

---

**End of Skill Document**
