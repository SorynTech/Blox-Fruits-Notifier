## 2025-04-29 - Optimized Top-N-Per-Group Pattern
**Learning:** In PostgreSQL, using `LEFT JOIN LATERAL` is the most efficient way to solve the "Top-1-per-group" problem (e.g., getting the latest roll for every user) compared to multiple subqueries or Python-side filtering.
**Action:** Always prefer `LATERAL` joins or `DISTINCT ON` for batch retrieval of related records to eliminate N+1 query patterns.

## 2025-04-29 - Stable Connection Pooling
**Learning:** Missing `try...finally` blocks when using `SimpleConnectionPool` leads to connection exhaustion in high-concurrency environments (like a web dashboard).
**Action:** Wrap every database interaction in a `try...finally` block to ensure `putconn()` is always called, even on failure.
