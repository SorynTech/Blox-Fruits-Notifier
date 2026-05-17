## 2025-05-15 - Initial Security Hardening
**Vulnerability:** Multiple security gaps identified: timing attacks in Basic Auth, potential XSS in web dashboard, missing security headers, and information leakage in error responses.
**Learning:** Legacy web implementations often overlook defense-in-depth measures like CSP and timing-safe comparisons.
**Prevention:** Always use `secrets.compare_digest` for credentials, `html.escape` for user data in templates, and middleware for security headers.
