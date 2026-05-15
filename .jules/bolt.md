## 2026-05-15 - [Eliminating N+1 Dashboard Queries]
**Learning:** In dashboard views requiring data from multiple tables (e.g., users and their most recent rolls), a standard approach of fetching all users and then querying rolls per-user leads to an N+1 performance bottleneck.
**Action:** Implement a cache column in the primary table (e.g., `last_fruit` in `users`) and update it during data entry (`log_roll`). Refactor retrieval to a single query fetching the primary table records, reducing database round-trips from O(N) to O(1).
