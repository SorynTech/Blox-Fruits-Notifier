## 2025-05-15 - Caching via DB-side Backfill
**Learning:** When implementing a cache column for data that already exists in other tables (like "last roll"), use PostgreSQL's `DISTINCT ON` clause in an `UPDATE...FROM` query for an efficient one-time backfill during migration. This avoids O(N) application-level logic during deployment.
**Action:** Use `UPDATE users u SET cache_col = r.val FROM (SELECT DISTINCT ON (user_id) ... ORDER BY user_id, rolled_at DESC) r WHERE u.user_id = r.user_id` for idempotent migrations.
