## 2025-05-14 - Initial Performance Audit
**Learning:** The dashboard was suffering from an N+1 query problem, fetching the entire roll history for every user just to display the most recent fruit. Additionally, global statistics were being initialized by fetching all user records instead of using efficient COUNT queries.
**Action:** Implement a cache column for the last fruit in the users table and use COUNT(*) for global statistics initialization.
