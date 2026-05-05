## 2026-05-05 - Batch User/Roll Retrieval
**Learning:** Using `LEFT JOIN LATERAL` in PostgreSQL allows fetching the most recent related record for multiple parent records in a single query, effectively solving the N+1 query problem without complex application-side logic.
**Action:** Use `LEFT JOIN LATERAL` when needing to display a list of entities along with their latest related event (e.g., users and their last activity).

## 2026-05-05 - Efficient Global Stats Initialization
**Learning:** `SELECT COUNT(*)` at the database level is significantly more performant than fetching all records and using `len()` in Python, especially as the database grows.
**Action:** Always provide dedicated count helper functions for metrics needed at startup or in dashboards.
