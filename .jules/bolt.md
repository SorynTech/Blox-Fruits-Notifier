# Bolt Journal - Performance Learnings

## 2025-05-14 - Initial Scan
**Learning:** Found N+1 query pattern in `handle_stats` where it fetches all users and then queries the `rolls` table for each user to get their last fruit. Also, `notification_checker` fetches all users from the database and filters them in Python, which is inefficient.
**Action:** Implement `LEFT JOIN LATERAL` for batch-fetching users with their last roll and add database-level filtering for notifications.
