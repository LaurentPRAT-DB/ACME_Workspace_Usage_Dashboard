# Account Monitor - Operations Checklist

**For: System Administrators, FinOps Engineers**

Printable checklists for daily, weekly, and monthly operations.

---

## Daily Checklist (5 minutes)

Run every morning:

- [ ] **Check Daily Refresh job** ran successfully
  - Workflows > Jobs > "Account Monitor - Daily Refresh"
  - Should complete around 2:05 AM UTC

- [ ] **Verify data freshness**
  ```sql
  SELECT MAX(usage_date) FROM main.account_monitoring_dev.contract_burndown;
  ```
  - Should be yesterday or today

- [ ] **Quick dashboard check**
  - Open Executive Summary page
  - Verify numbers look reasonable
  - No error messages

- [ ] **Check SQL Warehouse status**
  - Should be running or set to auto-start

**If issues found:**
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Manually run: `databricks bundle run account_monitor_daily_refresh`

---

## Weekly Checklist (Monday Morning - 15 minutes)

### Before Team Meeting

- [ ] **Check Weekly Training job** (ran Sunday 8 AM)
  - Workflows > Jobs > "Account Monitor - Weekly Training"
  - Verify Prophet model trained (not linear_fallback)

- [ ] **Check Weekly Review job** (ran Monday 8 AM)
  - Workflows > Jobs > "Account Monitor - Weekly Review"

- [ ] **Review Weekly Operations dashboard page**
  - Cost Spikes: How many anomalies?
  - Contract Pace: Any OVER PACE or UNDER PACE?
  - Top Workspaces: Any unexpected entries?

- [ ] **Investigate anomalies**
  - For each daily spike: What caused it?
  - For weekend usage: Should it be running?

- [ ] **Check Contract Burndown page**
  - Forecast updated?
  - Exhaustion dates reasonable?

### Action Items

| Finding | Action |
|---------|--------|
| Contract OVER PACE | Alert stakeholders, consider usage reduction |
| Contract UNDER PACE | Find ways to use commitment |
| Cost spike >100% | Investigate specific workspace/job |
| Weekend usage | Verify it's intentional |

---

## Monthly Checklist (1st of Month - 30 minutes)

### First Business Day

- [ ] **Check Monthly Summary job** ran (1st at 6 AM)
  - Workflows > Jobs > "Account Monitor - Monthly Summary"

- [ ] **Review Monthly Summary dashboard page**
  - MoM Change: Significant increase/decrease?
  - Cost by Product: Any category growing fast?
  - Monthly Statistics: Trends over 6 months?

- [ ] **Export reports** (if needed)
  - Download CSV from dashboard
  - Send to finance/leadership

- [ ] **Check contracts expiring soon**
  ```sql
  SELECT contract_id, end_date,
         DATEDIFF(end_date, CURRENT_DATE()) as days_left
  FROM main.account_monitoring_dev.contracts
  WHERE DATEDIFF(end_date, CURRENT_DATE()) BETWEEN 1 AND 90;
  ```

- [ ] **Review What-If scenarios** for renewals
  - Open What-If Analysis page
  - Note sweet spot recommendations

### Table Maintenance

- [ ] **Optimize tables** (improves query performance)
  ```sql
  OPTIMIZE main.account_monitoring_dev.contract_burndown;
  OPTIMIZE main.account_monitoring_dev.dashboard_data;
  ```

- [ ] **Verify archive** worked
  ```sql
  SELECT COUNT(*) FROM main.account_monitoring_dev.dashboard_data_archive;
  ```

---

## Quarterly Checklist (Every 3 Months - 1 hour)

### System Health

- [ ] **Review all job history**
  - Any recurring failures?
  - Any jobs taking too long?

- [ ] **Audit user access**
  - Who has access?
  - Anyone who shouldn't?
  - Anyone missing access?

- [ ] **Check storage usage**
  ```sql
  DESCRIBE DETAIL main.account_monitoring_dev.dashboard_data;
  ```

- [ ] **Review discount tiers**
  - Still accurate?
  - Any new tiers needed?

### Contract Review

- [ ] **All contracts current?**
  ```sql
  SELECT * FROM main.account_monitoring_dev.contracts
  WHERE status = 'ACTIVE';
  ```

- [ ] **Any contracts need updating?**
  - New contracts signed
  - Amendments to existing
  - Renewals processed

### Documentation

- [ ] **Update contract YAML** if needed
- [ ] **Re-deploy** if configuration changed
- [ ] **Test dashboard** after any changes

---

## Annual Checklist

- [ ] **Archive review**
  - How much data archived?
  - Need to adjust retention?

- [ ] **Forecast accuracy**
  - Were predictions accurate?
  - Model improvements needed?

- [ ] **Contract analysis**
  - How well did we track?
  - Any surprises?

- [ ] **System upgrade check**
  - New Databricks features?
  - Bundle updates available?

---

## Emergency Procedures

### Job Failure

1. Check job output for error message
2. Verify SQL warehouse is running
3. Check system table access
4. Manually re-run job
5. If persists, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Data Missing

1. Check last successful Daily Refresh
2. Verify system.billing has data
3. Manually run refresh job
4. Validate with freshness query

### Dashboard Errors

1. Try refreshing the page
2. Check if warehouse is running
3. Verify underlying tables have data
4. Re-deploy with `--force` if needed

### Contact Information

| Issue Type | Contact |
|------------|---------|
| Job failures | DevOps/Admin team |
| Access issues | Account admin |
| Data questions | Data Engineering |
| Business questions | FinOps team |

---

## Quick Commands

```bash
# Check job status
databricks runs list --limit 5 --profile YOUR_PROFILE

# Run daily refresh
databricks bundle run account_monitor_daily_refresh --profile YOUR_PROFILE

# Run weekly training
databricks bundle run account_monitor_weekly_training --profile YOUR_PROFILE

# Force re-deploy dashboard
databricks bundle deploy --force --profile YOUR_PROFILE

# Check table freshness
databricks sql execute --profile YOUR_PROFILE \
  "SELECT MAX(usage_date) FROM main.account_monitoring_dev.contract_burndown"
```

---

*Last updated: February 2026*
