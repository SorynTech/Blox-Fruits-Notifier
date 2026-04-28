## 2025-05-15 - N+1 Query Bottleneck in Stats Page
**Learning:** The `/stats` page currently fetches all users and then performs a separate database query for each user to retrieve their last fruit roll. This results in O(N) queries, which slows down the dashboard as the user base grows.
**Action:** Use a `LEFT JOIN LATERAL` query to batch fetch users and their most recent rolls in a single O(1) database operation.
