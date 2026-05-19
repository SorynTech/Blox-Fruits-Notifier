# Sentinel Security Journal 🛡️

## 2025-05-19 - Timing Attack & XSS Vulnerabilities
**Vulnerability:** HTTP Basic Auth was using standard string comparison for credentials, and user-controlled data was rendered in HTML templates without escaping.
**Learning:** Standard equality operators in Python (`==`) return as soon as a mismatch is found, allowing attackers to guess credentials character by character by measuring response times. Direct injection of user strings into HTML allows for Cross-Site Scripting (XSS).
**Prevention:** Use `secrets.compare_digest` for all credential comparisons. Always escape user-provided or database-sourced strings using `html.escape` before rendering in HTML templates.
