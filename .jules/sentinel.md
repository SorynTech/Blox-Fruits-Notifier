## 2024-05-01 - XSS and Timing Attack Mitigation
**Vulnerability:** Usernames and suspension reasons were rendered in the web dashboard without sanitization, and credentials were compared using standard equality.
**Learning:** In internal-facing dashboards, security is often overlooked. Using `html.escape()` for all user-controlled data and `secrets.compare_digest()` for auth is essential even for simple bots.
**Prevention:** Always sanitize any data from the database before rendering in HTML and use timing-attack-safe comparison for any sensitive tokens or passwords.
