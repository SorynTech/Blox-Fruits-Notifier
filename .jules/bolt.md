## 2026-05-02 - N+1 Query in Stats Dashboard
**Learning:** PostgreSQL's `LEFT JOIN LATERAL` is an extremely powerful tool for solving N+1 query problems where you need the "latest" related record for each row in a result set.
**Action:** Always check loop-based data fetching in route handlers for opportunities to use LATERAL joins or window functions to consolidate database round-trips.
