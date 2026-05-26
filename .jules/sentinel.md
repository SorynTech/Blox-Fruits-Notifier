## 2026-05-26 - XSS in Web Dashboard and Timing Attacks in Auth
**Vulnerability:** User-controlled data (usernames, fruit rolls, suspension reasons) were rendered directly in HTML without escaping, and Basic Auth used standard string equality for credential comparison.
**Learning:** Even internal-facing administrative dashboards must escape user-controlled data to prevent XSS, especially when that data originates from external platforms like Discord where users can set arbitrary usernames. Timing attacks on Basic Auth are a subtle but real risk.
**Prevention:** Always use `html.escape()` for all data rendered in HTML templates. Use `secrets.compare_digest()` for comparing sensitive credentials.
