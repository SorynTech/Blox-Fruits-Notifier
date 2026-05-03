## 2025-05-15 - Dashboard Security Hardening
**Vulnerability:** Timing attacks in authentication, Cross-Site Scripting (XSS) in user-provided data rendering, and Information Leakage via raw exception responses.
**Learning:** Python's scoping rules cause local variable assignments to shadow global imports of the same name (e.g., `import html` shadowed by `html = ...`), leading to `UnboundLocalError` if the global module is accessed before the local assignment.
**Prevention:** Use descriptive local variable names (like `response_html` or `users_html`) to avoid shadowing standard library modules, or use `from module import function` to minimize the risk of namespace collisions. Always verify that security-critical user data is sanitized at the point of rendering.
