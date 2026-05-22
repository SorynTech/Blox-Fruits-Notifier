## 2026-05-22 - [XSS and Timing Attacks in Dashboard]
**Vulnerability:** Cross-Site Scripting (XSS) via unsanitized database fields (usernames, fruit names) and Timing Attacks in HTTP Basic Auth.
**Learning:** User-controlled data retrieved from the database was injected directly into server-side rendered HTML templates using `.format()`, allowing for arbitrary script execution. The authentication logic used `==` for password comparison, which is susceptible to timing-based side-channel attacks. A secondary issue was shadowing the `html` standard library module with a local variable, which initially hindered the use of `html.escape()`.
**Prevention:**
1. Always wrap user-controlled or database-sourced strings in `html.escape()` before rendering them in HTML.
2. Use `secrets.compare_digest()` for all credential comparisons to ensure constant-time operations.
3. Avoid shadowing standard library module names (e.g., `html`, `json`, `os`) to maintain access to their functionality and improve code clarity.
4. Implement generic error messages for sensitive endpoints to prevent information leakage through stack traces or raw exception messages.
