# Scripts Directory

Helper scripts for Databricks notebook development and deployment.

---

## Available Scripts

### 📝 notebook_fix.sh

**Purpose:** Automates the complete notebook fix workflow including versioning, git operations, and deployment.

**Usage:**
```bash
./scripts/notebook_fix.sh <notebook_file> "<commit_message>"
```

**Example:**
```bash
./scripts/notebook_fix.sh notebooks/account_monitor_notebook.py "Fix SQL parameter issue in Cell 3"
```

**What it does:**
1. ✅ Extracts current version and build number
2. ✅ Automatically increments patch version
3. ✅ Generates new build number (increments or resets)
4. ✅ Updates VERSION and BUILD constants
5. ✅ Updates markdown header version
6. ✅ Stages file with `git add`
7. ✅ Creates properly formatted commit message
8. ✅ Commits changes
9. ✅ Pushes to remote
10. ✅ Deploys to Databricks workspace

**Output:**
```
=== Notebook Fix Helper ===

Current version: 1.5.4 (Build: 2026-01-29-014)
New version:     1.5.5 (Build: 2026-01-29-015)

Update version and commit? (y/n) y

Step 1: Updating version numbers...
✓ Version updated

Step 2: Git operations...
✓ File staged
✓ Changes committed

Step 3: Pushing to remote...
✓ Pushed to remote

Step 4: Deploying to Databricks...
✓ Deployed to workspace

=== Success! ===

Summary:
  File: notebooks/account_monitor_notebook.py
  Version: 1.5.4 → 1.5.5
  Build: 2026-01-29-014 → 2026-01-29-015
  Commit: a1b2c3d - Fix SQL parameter issue in Cell 3
```

**Requirements:**
- Git repository initialized
- Databricks CLI configured with active profile
- Notebook must have VERSION and BUILD constants
- Script must be executable: `chmod +x scripts/notebook_fix.sh`

**Version Format:**
- **Version:** Major.Minor.Patch (e.g., 1.5.4)
- **Build:** YYYY-MM-DD-NNN (e.g., 2026-01-29-014)

**Versioning Rules:**
- Script always increments patch version
- Build number increments if same day, resets to 001 on new day
- For minor/major version bumps, edit manually before running script

---

## Adding New Scripts

When adding new scripts:

1. Create the script file
2. Add shebang line: `#!/bin/bash`
3. Make it executable: `chmod +x scripts/your_script.sh`
4. Document it in this README
5. Add usage examples

---

## Related Documentation

- **Quick Reference:** `../NOTEBOOK_FIX_QUICKREF.md`
- **Full Workflow:** `../docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md`
- **Operations Guide:** `../OPERATIONS_GUIDE.md`

---

**Last Updated:** 2026-01-29
