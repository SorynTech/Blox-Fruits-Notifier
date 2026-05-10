## 2026-05-10 - XSS in Server-Side Rendered HTML
**Vulnerability:** User-controlled data (usernames, fruit names, suspension reasons) were directly embedded into HTML templates using Python f-strings without sanitization.
**Learning:** The application relies on manual string concatenation for its web dashboard, making it highly susceptible to XSS if new endpoints or data fields are added.
**Prevention:** Always use `html.escape()` when injecting variables into HTML strings, or migrate to a templating engine like Jinja2 that provides automatic escaping.
