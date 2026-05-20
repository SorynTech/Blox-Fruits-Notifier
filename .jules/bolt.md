## 2025-05-15 - Eliminating N+1 Queries on Dashboard
**Learning:** The `/stats` dashboard performs O(N) database queries because it fetches the last roll for each user individually. This scales poorly as the user base grows.
**Action:** Cache the `last_fruit` in the `users` table during `log_roll` and fetch it during `get_all_users`. This reduces dashboard queries from O(N+1) to O(1).
