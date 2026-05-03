## 2025-05-15 - Dashboard N+1 Query Optimization
**Learning:** The statistics dashboard was suffering from an N+1 query problem, fetching the most recent fruit for every user with an upcoming roll in separate database queries. Using a `LEFT JOIN LATERAL` query allows batch-retrieving this data in a single round-trip.
**Action:** Always look for opportunities to use SQL-level joins or batching instead of iterative Python-side processing for related records.
