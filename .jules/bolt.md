## 2026-06-01 - N+1 Query in Dashboard Stats
**Learning:** The dashboard's `handle_stats` function previously fetched all users and then performed a separate database query for each user to retrieve their latest roll. This O(N) approach significantly slowed down the dashboard as the user base grew.
**Action:** Consolidate user and latest roll data into a single O(1) query using PostgreSQL's `DISTINCT ON (user_id)` combined with a `LEFT JOIN`. This ensures that even with thousands of users, the dashboard remains responsive with only two primary queries (users data and rarity distribution).
