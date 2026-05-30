## 2026-05-30 - N+1 Query Pattern in Stats Dashboard
**Learning:** The `handle_stats` endpoint was performing O(N) database queries because it fetched all users and then queried the `rolls` table for each user individually to find their latest fruit. This pattern significantly impacts performance as the user base grows.
**Action:** Use PostgreSQL's `DISTINCT ON (user_id)` combined with a `LEFT JOIN` to fetch all necessary data (user info + latest roll) in a single O(1) query.

## 2026-05-30 - Memory-Intensive Bot Initialization
**Learning:** Initializing global statistics by fetching all user records into memory via `get_all_users()` is inefficient and doesn't scale.
**Action:** Use SQL aggregate functions like `COUNT(*)` and `SUM(total_rolls)` to offload calculation to the database engine.
