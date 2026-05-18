## 2025-05-14 - HTML Module Shadowing and XSS
**Vulnerability:** Cross-Site Scripting (XSS) in server-side rendered dashboard routes.
**Learning:** Data sourced from external APIs (like Discord usernames) or the database (suspension reasons) was injected into HTML templates without escaping. Additionally, when fixing this using the `html` standard library, using a local variable named `html` to store the template output shadows the module, leading to `UnboundLocalError`.
**Prevention:** Always use `html.escape()` for user-controlled data in templates. Use descriptive variable names like `response_html` to avoid shadowing the `html` module.

## 2025-05-14 - Timing Attacks in Basic Auth
**Vulnerability:** Use of `==` for password comparison in authentication logic.
**Learning:** Standard string comparison is not constant-time, potentially allowing an attacker to brute-force credentials by measuring response times.
**Prevention:** Use `secrets.compare_digest()` for all credential comparisons.
