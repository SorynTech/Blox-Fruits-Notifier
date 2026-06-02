## 2024-06-02 - Web Dashboard Security Patch
**Vulnerability:** Cross-Site Scripting (XSS), Timing Attacks, and Information Leakage.
**Learning:** Data sourced from external platforms (Discord usernames) or stored as free-text (suspension reasons) are viable XSS vectors when rendered in administrative dashboards. Furthermore, standard string comparison in basic auth is susceptible to timing attacks, and raw exception logging to HTTP responses leaks system internals.
**Prevention:**
1. Use `html.escape()` for all dynamic content in HTML templates.
2. Use `secrets.compare_digest()` for credential validation.
3. Return generic error messages to end-users while logging detailed errors internally.
4. Avoid shadowing standard library modules (like `html`) by using descriptive local variable names (e.g., `response_html`).
