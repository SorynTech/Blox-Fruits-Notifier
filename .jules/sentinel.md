## 2026-05-20 - XSS Mitigation and Module Shadowing
**Vulnerability:** Stored Cross-Site Scripting (XSS) in the web dashboard handlers (`handle_stats` and `handle_suspended`).
**Learning:** User-controlled data (usernames, suspension reasons) was directly injected into HTML templates. Attempting to fix this by importing the `html` module failed because local variables named `html` shadowed the module, leading to `UnboundLocalError`.
**Prevention:** Always escape user-provided data using `html.escape()`. Use descriptive names for local variables (e.g., `response_html`) to avoid shadowing standard library modules.
