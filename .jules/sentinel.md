## 2025-05-14 - Hardening the Stats Dashboard
**Vulnerability:** Cross-Site Scripting (XSS), Timing Attacks, and Information Leakage in the web dashboard.
**Learning:** Using the same name for a module (e.g., `import html`) and a local variable (e.g., `html = "..."`) causes shadowing, leading to runtime errors when trying to use the module. Additionally, raw database values (like usernames or suspension reasons) must always be escaped before being rendered in HTML templates to prevent script injection.
**Prevention:** Use descriptive names for local variables (like `response_html`) to avoid module shadowing. Always apply `html.escape()` to user-provided data. Use `secrets.compare_digest()` for auth checks. Return generic error messages to clients while logging full traces internally.
