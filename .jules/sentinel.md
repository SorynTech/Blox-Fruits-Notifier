## 2026-04-24 - [XSS Vulnerabilities in Web Dashboard]
**Vulnerability:** User-controlled data (usernames, fruit names, suspension reasons) were being rendered directly into HTML without sanitization, leading to potential Cross-Site Scripting (XSS) attacks.
**Learning:** Even internal or protected dashboards must sanitize all user-supplied data before rendering to prevent malicious scripts from being executed in the context of an authenticated session.
**Prevention:** Always use `html.escape()` or a similar sanitization function when embedding user data into HTML templates.
