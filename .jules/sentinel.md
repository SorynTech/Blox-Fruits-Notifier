## 2026-05-28 - [CRITICAL] XSS and Timing Attack Vulnerabilities in Web Dashboard
**Vulnerability:** The web dashboard was vulnerable to Cross-Site Scripting (XSS) via unsanitized usernames and fruit names, and the Basic Auth was susceptible to timing attacks. Additionally, internal exceptions were leaked in error responses.

**Learning:** Data sourced from the database (like usernames and reasons) was trusted implicitly during HTML rendering. Standard string comparison for passwords allowed for potential timing attacks. Using `html` as a local variable name in web handlers shadowed the `html` standard library module, causing `UnboundLocalError` when trying to fix XSS.

**Prevention:**
1. Always use `html.escape()` for any data rendered in HTML templates.
2. Use `secrets.compare_digest()` for all credential comparisons.
3. Return generic error messages (e.g., "Internal Server Error") instead of raw exception strings.
4. Avoid naming local variables `html` in functions that need the `html` module; use descriptive names like `response_html`.
