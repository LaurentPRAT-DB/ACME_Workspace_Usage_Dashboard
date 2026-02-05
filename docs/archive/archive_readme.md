# Archive Directory

This directory contains files that have been deprecated or superseded by newer implementations.

## Archived Files

### `ibm_style_dashboard_queries.sql`

**Archived Date:** 2026-01-29
**Reason:** Redundant with `lakeview_dashboard_queries.sql`

**Summary:**
- Contained 9 queries for a single-page dashboard layout
- 44% were exact duplicates of Lakeview queries
- 33% were simplified versions (Lakeview had more detail)
- Only 22% provided unique value

**Migration:**
- Unique Query 3 (Account Info) → Added as Lakeview Query 16
- Unique Query 7 (Combined Burndown) → Added as Lakeview Query 17
- Other queries already covered by Lakeview (Queries 1-15)

**Reference Documentation:**
- See `/docs/IBM_QUERIES_REDUNDANCY_ANALYSIS.md` for full analysis
- See `/notebooks/lakeview_dashboard_queries.sql` for all current queries

**If You Need This File:**
The file remains available here for reference. All functionality has been preserved in the Lakeview queries.
