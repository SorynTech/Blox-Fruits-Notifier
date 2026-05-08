## 2026-05-08 - Eliminate N+1 queries in Stats Dashboard
**Learning:** The previous implementation of the stats dashboard performed an N+1 query pattern, executing a separate database call to `get_user_rolls` for every user in a loop to retrieve their most recent fruit. This scales poorly as the user base grows.
**Action:** Use a `LEFT JOIN LATERAL` query to batch-retrieve users along with their single most recent related record (e.g., fruit roll) in one efficient database round-trip.

## 2026-05-08 - Connection Pool Management
**Learning:** Failing to use `finally` blocks when acquiring connections from a pool (like `psycopg2.pool.SimpleConnectionPool`) leads to connection leaks if an exception occurs during the database operation.
**Action:** Always wrap database logic in `try...finally` to ensure `putconn` (or equivalent) is called to return the connection to the pool, preventing application crashes due to connection exhaustion.
