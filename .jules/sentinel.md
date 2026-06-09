## 2026-06-09 - HTML Module Shadowing in Web Handlers
**Vulnerability:** XSS due to missing input sanitization in web dashboard handlers.
**Learning:** In `main.py`, several web handlers used a local variable named `html` to store rendered templates. When the `html` standard library module was imported to implement `html.escape()`, it caused shadowing issues leading to `UnboundLocalError`.
**Prevention:** Always use descriptive names like `response_html` for local HTML strings to avoid shadowing the `html` module. Ensure all user-provided data from the database (usernames, reasons) is escaped before being formatted into HTML templates.
