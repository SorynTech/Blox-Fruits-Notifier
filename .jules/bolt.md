## 2026-06-02 - N+1 Query in Stats Dashboard
**Learning:** The stats dashboard was performing a database query for each user to fetch their latest roll history, resulting in an O(N) query pattern. This significantly slows down page loads as the user base grows.
**Action:** Use PostgreSQL's `DISTINCT ON (user_id)` in a `LEFT JOIN` to fetch all users and their latest rolls in a single O(1) database operation. Always check loop bodies for database calls that can be optimized into a single join.
