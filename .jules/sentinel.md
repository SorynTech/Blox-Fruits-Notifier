## 2026-05-23 - Hardened Web Dashboard Security

**Vulnerability:** XSS, Timing Attacks, and Information Leakage in Web Dashboard.
**Learning:** Usernames and suspension reasons fetched from the database were being injected directly into HTML templates without escaping, allowing for XSS. `check_auth` used standard string comparison for credentials, which is vulnerable to timing attacks. Exception handlers in web routes were returning raw exception strings, potentially leaking database schema or internal details.
**Prevention:** Always use `html.escape()` for any data rendered in HTML. Use `secrets.compare_digest()` for credential comparisons. Return generic error messages to web clients while logging the detailed error internally.
