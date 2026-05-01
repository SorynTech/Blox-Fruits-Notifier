## 2025-05-01 - Optimized Stats Dashboard retrieval
**Learning:** The statistics page had a classic N+1 query bottleneck where it fetched every user and then performed a separate database query to find the latest roll for each one. Additionally, iterative string concatenation (`+=`) was being used for HTML generation.
**Action:** Use `LEFT JOIN LATERAL` to fetch the most recent related records in a single batch query. Maintain global counters for high-frequency metrics (like user count) and use `"".join()` for efficient O(N) string building.
