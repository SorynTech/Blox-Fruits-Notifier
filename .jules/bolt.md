## 2026-06-04 - Optimize dashboard stats with O(1) query
**Learning:** The dashboard statistics page suffered from an N+1 query problem, fetching all users and then querying the rolls table for each user to find their last fruit. This scales poorly as the user base grows.
**Action:** Use PostgreSQL's `DISTINCT ON (user_id)` combined with a `LEFT JOIN` and `ORDER BY u.user_id, r.rolled_at DESC` to fetch both user data and their latest roll in a single query.
