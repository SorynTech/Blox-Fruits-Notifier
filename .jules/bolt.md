## 2025-05-15 - Database Performance and N+1 Elimination

**Learning:** Database performance is the primary bottleneck in this Discord bot. The stats dashboard suffered from a severe N+1 query problem by fetching all rolls for every user individually. Background tasks also performed full table scans and filtered in Python, which does not scale.

**Action:**
1. Use `LEFT JOIN LATERAL` in PostgreSQL to fetch the latest related record for multiple parents in a single query.
2. Offload aggregation (e.g., rarity counts) to SQL with `GROUP BY` instead of fetching and processing in Python.
3. Replace Python-side filtering with `WHERE` clauses for background tasks.
4. Ensure `try...finally` blocks for database connections to prevent pool exhaustion.
5. Use `"".join()` for HTML generation to ensure O(N) string building performance.
