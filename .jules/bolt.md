## 2026-04-24 - [N+1 Query in Stats Dashboard]
**Learning:** The `/stats` dashboard exhibited an N+1 query pattern, fetching all users and then querying the latest fruit roll for each user individually. This leads to linear performance degradation as the user base grows.
**Action:** Use PostgreSQL's `LEFT JOIN LATERAL` to fetch the most recent related records (e.g., latest rolls) for a set of parent records (e.g., users) in a single batch query, reducing the complexity from O(N) to O(1) database calls.
>>>>>>> REPLACE
