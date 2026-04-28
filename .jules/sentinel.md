## 2025-05-15 - [XSS and Timing Attack Mitigation]
**Vulnerability:** Unsanitized user-controlled data (usernames, suspension reasons) was directly rendered into HTML templates, and HTTP Basic Auth credentials were compared using standard string equality.
**Learning:** Even internal-facing stats dashboards can be vectors for XSS if user-controlled content is not properly escaped. Standard string comparison is vulnerable to timing attacks.
**Prevention:** Always use `html.escape()` for any user-provided string reflected in HTML. Use `secrets.compare_digest()` for all credential comparisons.
