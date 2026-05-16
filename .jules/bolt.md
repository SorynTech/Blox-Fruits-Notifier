## 2026-05-16 - Database Initialization Order
**Learning:** Idempotent backfills that depend on other tables (e.g., populating `users.last_fruit` from the `rolls` table) must be executed after those dependency tables are created in `init_database` to prevent `undefined_table` errors on fresh installs.
**Action:** Always verify the schema dependency graph before adding backfill logic to `init_database`.

## 2026-05-16 - Global Search for SELECT Sites
**Learning:** When adding a new cached column to a table, all SELECT sites (helper functions like `get_all_users`, `get_suspended_users`, etc.) must be updated to include the new field, otherwise the UI may display stale or "None" values.
**Action:** Use `grep` to find all SELECT statements involving the modified table to ensure consistency across the application.
