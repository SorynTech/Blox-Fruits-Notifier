## 2024-05-31 - Efficient "Latest Record per Group" in PostgreSQL
**Learning:** Fetching the latest record for each member of a group (e.g., latest roll for each user) often leads to N+1 query patterns in application code. PostgreSQL's `DISTINCT ON` clause is an extremely efficient way to solve this in a single query.
**Action:** Use `SELECT DISTINCT ON (group_column) ... ORDER BY group_column, sort_column DESC` to collapse results to the most recent entry per group. Combine with `LEFT JOIN` to include all group members even if they have no records.
