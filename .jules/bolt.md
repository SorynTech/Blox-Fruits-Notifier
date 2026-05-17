## 2025-05-14 - Eliminating N+1 Queries in Stats Dashboard
**Learning:** Server-side rendered dashboards that iterate over a list of users and perform separate database queries for each user's latest activity (e.g., their most recent roll) create a significant O(N) performance bottleneck.
**Action:** Cache the most recent activity result (like `last_fruit`) directly in the `users` table. Update this cache synchronously during the write operation to ensure O(1) retrieval during dashboard rendering.

## 2025-05-14 - Optimized Table Counting
**Learning:** Using `len(get_all_users())` to count active users is extremely inefficient as it fetches all columns for every user record from the database into application memory just to calculate a count.
**Action:** Always use `SELECT COUNT(*)` queries for statistical counters to leverage the database engine's efficiency and minimize network/memory overhead.
