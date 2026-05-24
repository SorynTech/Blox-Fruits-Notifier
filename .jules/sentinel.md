# Sentinel's Security Journal 🛡️

Critical security learnings and patterns discovered in this codebase.

## 2025-05-14 - Initial Security Scan
**Vulnerability:** XSS in stats dashboard, Timing attacks in auth, Information leakage in error responses.
**Learning:** Legacy web handlers were rendering user-controlled data directly into HTML templates without escaping. Basic Auth used standard string comparison.
**Prevention:** Always escape user-controlled variables (usernames, reasons, etc.) using `html.escape`. Use `secrets.compare_digest` for all credential comparisons. Return generic error messages on sensitive endpoints.
