## 2026-06-05 - N+1 Query in Dashboard Stats
**Learning:** The dashboard's stats page was suffering from an N+1 query bottleneck, fetching all users and then querying the latest roll for each individual user in a loop. This caused the page load time to scale linearly with the number of users.
**Action:** Use PostgreSQL's `DISTINCT ON` clause combined with a `LEFT JOIN` to fetch all necessary data in a single query. Also, filter eligible users for background tasks at the database level instead of in-memory.
