## 2025-05-15 - N+1 Query Problem in Stats Dashboard
**Learning:** Fetching the latest related record for a list of items (e.g., last fruit for all users) often leads to N+1 query patterns. Using PostgreSQL's `LEFT JOIN LATERAL` allows retrieving this data in a single efficient query.
**Action:** Always check for loops containing database calls and consider using LATERAL joins or window functions to batch them.
