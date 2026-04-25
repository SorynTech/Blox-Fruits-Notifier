## 2025-04-25 - Eliminating N+1 Queries with LEFT JOIN LATERAL

**Learning:** In a dashboard showing a list of users and their most recent associated record (e.g., fruit rolls), fetching users then iteratively querying rolls for each user creates an N+1 performance bottleneck. Using `LEFT JOIN LATERAL` allows fetching the top 1 related record for each row in the primary table in a single optimized query.

**Action:** Always look for N+1 query patterns in dashboard handlers. Prefer SQL-level joins and lateral subqueries over application-level loops with database calls. Ensure SQL aliases match application expectation and verify database column names against existing dictionary key lookups.
