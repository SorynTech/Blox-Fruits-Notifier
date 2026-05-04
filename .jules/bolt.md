## 2025-05-15 - N+1 Query in Stats Dashboard
**Learning:** The stats dashboard was fetching all users and then iteratively calling `get_user_rolls` for each user to get their last fruit, causing an N+1 query problem. Additionally, `on_ready` and the dashboard were using `len(get_all_users())` to count active users, which is inefficient for large datasets.
**Action:** Use a `LEFT JOIN LATERAL` query to fetch users and their most recent roll in a single batch. Implement a dedicated `COUNT(*)` helper for active user counting and cache it in the global `stats` object.
