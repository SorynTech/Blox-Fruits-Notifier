## 2026-05-29 - [Optimization of N+1 Query in Dashboard]
**Learning:** Dashboard data retrieval was suffering from an N+1 query problem because it fetched the latest fruit roll for each user individually from the `rolls` table while iterating through the user list.
**Action:** Implemented a cache column `last_fruit` in the `users` table, updated during each roll, and backfilled for existing data. This allows fetching user stats and their latest roll in a single query from the `users` table, reducing database load from O(N) to O(1) per dashboard load.
