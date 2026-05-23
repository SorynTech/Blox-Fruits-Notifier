## 2025-05-14 - [Eliminate N+1 queries in stats dashboard]
**Learning:** The stats dashboard was performing an O(N) database lookup for the "last fruit" of each user in a loop, significantly slowing down the page render as the user base grows.
**Action:** Implement data denormalization by adding a `last_fruit` cache column to the `users` table, updated during the roll logging process, allowing for O(1) retrieval during dashboard rendering.
