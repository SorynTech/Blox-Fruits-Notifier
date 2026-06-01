## 2026-06-01 - Web Dashboard Security Hardening
**Vulnerability:** Multiple security gaps in the aiohttp web dashboard, including timing attack risks in Basic Auth, XSS vulnerabilities due to manual HTML string concatenation, and information leakage through raw exception responses.
**Learning:** Manual HTML generation in Python requires rigorous use of `html.escape()` for all user-controlled data. Local variable names like `html` can shadow the `html` module, necessitating careful naming (e.g., `response_html`).
**Prevention:** Always wrap web handlers in try-except blocks that return generic error messages. Use `secrets.compare_digest()` for all credential comparisons. Rename local variables that conflict with security modules.
