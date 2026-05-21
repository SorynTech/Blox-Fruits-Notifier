## 2025-05-15 - Optimization of Database Access and Dashboard Performance

**Learning:**
1. The dashboard was suffering from an N+1 query problem, where it would fetch all users and then execute an additional query for each user to get their last rolled fruit.
2. The notification checker was fetching all users from the database and filtering them in Python, which is inefficient as the user base grows.
3. Inconsistent use of `try...finally` for returning database connections to the pool posed a risk of connection leaks and pool exhaustion.

**Action:**
1. Introduce a `last_fruit` cache column in the `users` table to allow fetching all necessary dashboard data in a single query.
2. Implement targeted SQL queries for counting rolls, active users, and identifying users due for notifications.
3. Standardize connection management in database helpers using `try...finally` blocks to ensure connections are always returned to the `SimpleConnectionPool`.
