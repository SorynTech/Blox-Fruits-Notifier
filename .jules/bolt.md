## 2026-05-11 - Optimizing Dashboard with Cache Column and Lateral Join
**Learning:** In applications with frequent "latest item per parent" lookups (like a user's last roll), the N+1 query problem can be eliminated by adding a cache column to the parent table. For backward compatibility, a `LEFT JOIN LATERAL` with `COALESCE` allows fetching the cached value or falling back to the related table in a single round-trip.
**Action:** Always check for O(N) database access patterns in loops (like list views) and prioritize batching via JOINS or adding cache columns for frequently accessed data.
