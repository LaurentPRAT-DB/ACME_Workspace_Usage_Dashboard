# Complete Git to Workspace Workflow

## Overview

This document defines the complete workflow from code changes to Databricks workspace deployment.

## Standard Workflow Steps

### 1. Make Changes
Edit files locally in your development environment.

### 2. Test Changes (if applicable)
Run local tests or validation scripts.

### 3. Stage Changes
```bash
git add <files>
```

### 4. Commit Changes
```bash
git commit -m "Descriptive commit message

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 5. Push to GitHub
```bash
git push
```

### 6. **Deploy to Databricks Workspace** ⚠️ CRITICAL STEP
```bash
databricks bundle deploy -t dev
```

**This step is MANDATORY for notebook changes to be visible in the workspace!**

Without deployment:
- ❌ Changes remain only in GitHub
- ❌ Notebooks in workspace show old versions
- ❌ Users can't see updates

After deployment:
- ✅ Notebooks updated in workspace
- ✅ Changes immediately available
- ✅ Users see latest version

## Verification

After deployment, verify notebooks are updated:

```bash
# List deployed notebooks
databricks workspace list /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/

# Check specific notebook (opens in browser)
databricks workspace open /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/lakeview_dashboard_queries
```

## Deployment Locations

When you run `databricks bundle deploy -t dev`, files are deployed to:

```
/Workspace/Users/<your-email>/account_monitor/
├── files/
│   ├── notebooks/           ← Your notebooks here
│   │   ├── account_monitor_notebook
│   │   ├── lakeview_dashboard_queries
│   │   └── ibm_style_dashboard_queries
│   ├── sql/                 ← SQL scripts
│   ├── docs/                ← Documentation
│   └── *.py, *.yml, etc.    ← Other files
├── artifacts/               ← Build artifacts
└── state/                   ← Deployment state
```

## Quick Commands

### Full workflow (all in one)
```bash
git add .
git commit -m "Your message"
git push
databricks bundle deploy -t dev
```

### Force redeploy (if sync issues)
```bash
databricks bundle deploy -t dev --force-deploy
```

### Deploy to production
```bash
databricks bundle deploy -t prod
```

## Common Issues

### Issue 1: Notebook not updated in workspace
**Symptom:** Old version visible in Databricks UI
**Cause:** Forgot to run `databricks bundle deploy`
**Fix:** Run deployment command

### Issue 2: Deployment fails with validation errors
**Symptom:** Bundle deploy returns errors
**Cause:** Invalid databricks.yml configuration
**Fix:** Check databricks.yml syntax and resources

### Issue 3: Files not syncing
**Symptom:** Some files missing after deploy
**Cause:** Files excluded in databricks.yml sync section
**Fix:** Check `sync.include` and `sync.exclude` patterns

## Environment-Specific Deployment

### Development (default)
```bash
databricks bundle deploy -t dev
# or just
databricks bundle deploy
```

### Production
```bash
databricks bundle deploy -t prod
```

## Automation Options

### Option 1: Git Hook (Post-Push)
Create `.git/hooks/post-push`:
```bash
#!/bin/bash
echo "🚀 Deploying to Databricks workspace..."
databricks bundle deploy -t dev
echo "✅ Deployment complete!"
```

Make executable:
```bash
chmod +x .git/hooks/post-push
```

### Option 2: Shell Alias
Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias gitpush='git push && databricks bundle deploy -t dev'
```

### Option 3: Makefile
Create `Makefile`:
```makefile
deploy:
	git add .
	git commit -m "$(msg)"
	git push
	databricks bundle deploy -t dev

# Usage: make deploy msg="Your commit message"
```

## CI/CD Integration

For automated deployments, add to your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Deploy to Databricks
  run: |
    databricks bundle deploy -t dev
  env:
    DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

## Best Practices

1. ✅ **Always deploy after pushing** - Don't forget this step
2. ✅ **Verify deployment** - Check workspace after deploy
3. ✅ **Use dev environment first** - Test before prod
4. ✅ **Document changes** - Include version numbers
5. ✅ **Test notebooks** - Run queries after deployment

## Workflow Checklist

- [ ] Changes made locally
- [ ] Files staged (`git add`)
- [ ] Changes committed (`git commit`)
- [ ] Pushed to GitHub (`git push`)
- [ ] **Deployed to workspace (`databricks bundle deploy`)**
- [ ] Deployment verified (check workspace)
- [ ] Notebooks tested (run queries)

## Related Documentation

- `DAB_QUICK_COMMANDS.md` - Quick reference for bundle commands
- `DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- `databricks.yml` - Bundle configuration
- `.databricks/` - Local deployment state

## Summary

**Remember:** `git push` updates GitHub, but `databricks bundle deploy` updates your workspace!

Both steps are required for complete deployment.
