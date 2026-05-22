## 2025-05-22 - Dashboard N+1 Query Bottleneck
**Learning:** Rendering a dashboard with a list of users where each entry requires a lookup from a related table (like `rolls`) creates an O(N) database bottleneck. Even with indexes, this significantly slows down as the user base grows.
**Action:** Implement a cache column (`last_fruit`) on the primary table (`users`) and update it during the write operation (`log_roll`). This reduces dashboard retrieval to O(1) for the related data.
