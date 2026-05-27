## 2026-05-27 - Eliminating N+1 Queries in Dashboard

**Learning:** The statistics dashboard was performing O(N) database queries by calling `get_user_rolls` for every user in a loop to display their last rolled fruit. This causes significant latency as the number of users grows. Denormalizing the schema to include a `last_fruit` cache column on the `users` table allows for O(1) retrieval during the main user fetch.

**Action:** Identify loops performing database lookups in web handlers or bot tasks. Use caching columns or SQL JOINs to fetch all required data in a single round-trip. For PostgreSQL backfills, use `DISTINCT ON` to efficiently grab the latest record per related entity.
