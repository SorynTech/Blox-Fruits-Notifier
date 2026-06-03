## 2024-06-03 - Cross-Site Scripting (XSS) in Admin Dashboard
**Vulnerability:** User-controlled data from Discord (usernames and fruit names) was rendered directly into the aiohttp web dashboard HTML without escaping, allowing for Reflected and Stored XSS.
**Learning:** Internal dashboards are high-value targets for XSS when they display data sourced from external APIs (like Discord). Even if the user is authenticated, the data they see might be malicious.
**Prevention:** Always use `html.escape()` for any dynamic content rendered in HTML templates. Use constant-time comparison (`secrets.compare_digest`) for Basic Auth to prevent timing attacks.

## 2024-06-03 - Variable Shadowing causing UnboundLocalError
**Vulnerability:** Importing the `html` module for security escaping conflicted with existing local variables named `html` used to store response strings.
**Learning:** When introducing standard security libraries, ensure their names do not shadow existing local variables, as this leads to `UnboundLocalError` when the code tries to access the local variable before assignment.
**Prevention:** Use descriptive names for HTML response strings (e.g., `response_html`) to avoid namespace collisions with the `html` library.
