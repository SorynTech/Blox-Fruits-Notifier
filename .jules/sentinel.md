## 2024-10-27 - Stored XSS in Dashboard and Timing Attack in Auth
**Vulnerability:** The web dashboard (`/stats`, `/suspended`) was vulnerable to Stored XSS because Discord usernames, fruit names, and suspension reasons were rendered directly into HTML templates without escaping. Additionally, `check_auth` used standard string comparison, making it susceptible to timing attacks.

**Learning:** Data sourced from a database or external API (Discord) should always be treated as untrusted, especially when rendered in internal dashboards. Even if the data "looks" safe (like a username), it can be manipulated by malicious users. Also, constant-time comparison is essential for credential verification to prevent side-channel leakage.

**Prevention:** Always use `html.escape()` for any dynamic content in HTML templates. Use `secrets.compare_digest()` for auth checks. Avoid naming local variables after common modules (e.g., don't use `html` as a variable name if you import the `html` module) to prevent shadowing and runtime errors during template rendering.
