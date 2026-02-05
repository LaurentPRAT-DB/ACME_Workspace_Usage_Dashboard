# ⚠️ DEPLOYMENT REQUIRED

## Critical Reminder

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🚨 AFTER EVERY GIT PUSH, YOU MUST DEPLOY TO DATABRICKS 🚨 │
│                                                             │
│      git push               ≠      Changes in workspace    │
│                                                             │
│      git push                                               │
│         +                   =      Changes in workspace    │
│      databricks bundle deploy                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## The Complete Command Sequence

```bash
# Step 1: Commit and push to GitHub
git add .
git commit -m "Your changes"
git push

# Step 2: Deploy to Databricks workspace (MANDATORY!)
databricks bundle deploy -t dev

# Step 3: Verify deployment
databricks workspace list /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/
```

## Why Both Steps Are Required

| Command | What It Does | Where Changes Go |
|---------|--------------|------------------|
| `git push` | Uploads code to GitHub | ✅ GitHub repository<br>❌ Databricks workspace |
| `databricks bundle deploy` | Syncs code to workspace | ✅ GitHub repository<br>✅ Databricks workspace |

## What Happens If You Skip Deployment

❌ **Notebooks in workspace show old version**
- Users can't see your fixes
- Version numbers don't update
- Changes appear "missing"

❌ **Confusion and wasted time**
- "I don't see the version update"
- "The fix isn't working"
- "Nothing changed"

❌ **Need to re-explain and re-deploy**
- Extra communication overhead
- Deployment done later anyway
- Frustrated users

## One-Line Solution

Add this alias to your `~/.bashrc` or `~/.zshrc`:

```bash
alias gp='git push && databricks bundle deploy -t dev && echo "✅ Pushed to GitHub AND deployed to workspace!"'
```

Then just run:
```bash
gp
```

## Post-Push Hook (Automatic)

Create `.git/hooks/post-push`:

```bash
#!/bin/bash
echo ""
echo "🚀 Deploying to Databricks workspace..."
echo ""
databricks bundle deploy -t dev
echo ""
echo "✅ Deployment complete! Changes are now live in workspace."
echo ""
```

Make executable:
```bash
chmod +x .git/hooks/post-push
```

Now deployment happens automatically after every push!

## Verification Commands

After deployment, verify notebooks are updated:

```bash
# List all notebooks
databricks workspace list /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/

# Open specific notebook in browser
databricks workspace open /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/lakeview_dashboard_queries

# Check file modification time
databricks workspace get-status /Workspace/Users/$(databricks current-user me --output json | jq -r .userName)/account_monitor/files/notebooks/lakeview_dashboard_queries
```

## Quick Reference Card

Print this and keep it visible:

```
┌──────────────────────────────────────────┐
│                                          │
│         EVERY CODE CHANGE NEEDS:         │
│                                          │
│  1. git push                             │
│  2. databricks bundle deploy -t dev      │
│                                          │
│         BOTH STEPS REQUIRED!             │
│                                          │
│  Without deployment:                     │
│  ❌ Changes NOT in workspace             │
│  ❌ Users see old version                │
│  ❌ Version numbers not updated          │
│                                          │
│  After deployment:                       │
│  ✅ Changes visible in workspace         │
│  ✅ Users see new version                │
│  ✅ Everything synchronized              │
│                                          │
└──────────────────────────────────────────┘
```

## Common Scenarios

### Scenario 1: Notebook Fix
```bash
# Fix issue in notebook
vim notebooks/lakeview_dashboard_queries.sql

# Commit and push
git add notebooks/lakeview_dashboard_queries.sql
git commit -m "Fix Query 4 field names"
git push

# 🚨 MUST DEPLOY!
databricks bundle deploy -t dev
```

### Scenario 2: Multiple File Changes
```bash
# Make various changes
git add .
git commit -m "Update configuration and queries"
git push

# 🚨 MUST DEPLOY!
databricks bundle deploy -t dev
```

### Scenario 3: Quick Fix
```bash
# One-liner to do everything
git add . && git commit -m "Quick fix" && git push && databricks bundle deploy -t dev
```

## Troubleshooting

### "I don't see my changes in the workspace"
**Solution:** You forgot to deploy. Run:
```bash
databricks bundle deploy -t dev
```

### "Deployment failed"
**Solution:** Check the error message and validate:
```bash
databricks bundle validate
```

### "How do I know if I deployed?"
**Solution:** Check deployment timestamp:
```bash
ls -la .databricks/bundle/dev/
# Look at modification time of deployment files
```

## Related Documentation

- `COMPLETE_WORKFLOW.md` - Full workflow documentation
- `docs/SKILL_NOTEBOOK_FIX_WORKFLOW.md` - Detailed notebook fix process
- `DAB_QUICK_COMMANDS.md` - Quick command reference

## Remember

**No exceptions. No shortcuts. Always deploy.**

```
git push + databricks bundle deploy = Complete deployment ✅
git push alone = Incomplete deployment ❌
```
