## 2025-06-07 - N+1 Bottleneck in Web Dashboard
**Learning:** The `handle_stats` endpoint was performing O(N) database queries by fetching all users and then querying each user's latest roll individually. Additionally, `len(get_all_users())` was used for simple counts, fetching all user records just to count them.
**Action:** Use PostgreSQL `DISTINCT ON` for efficient "latest per group" queries in a single JOIN. Use `COUNT(*)` for statistics instead of fetching full record sets.
