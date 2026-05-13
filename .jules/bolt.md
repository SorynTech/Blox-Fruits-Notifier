## 2025-05-15 - N+1 Query Bottleneck in Dashboard
**Learning:** The `/stats` dashboard was performing one database query per user to fetch their last roll, leading to $O(N)$ database round-trips. This significantly impacts performance as the user base grows.
**Action:** Use a cache column (`last_fruit`) on the `users` table or a `LEFT JOIN LATERAL` query to retrieve all dashboard data in a single $O(1)$ database request.

## 2025-05-15 - Quadratic String Concatenation in HTML Generation
**Learning:** Using `+=` to build large HTML tables in loops results in $O(N^2)$ performance due to string immutability in Python.
**Action:** Always use `"".join()` with list comprehensions for $O(N)$ performance when generating dynamic HTML content.
