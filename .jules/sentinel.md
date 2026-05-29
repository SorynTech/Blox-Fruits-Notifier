## 2026-05-29 - XSS and Timing Attack Vulnerabilities in Web Dashboard

**Vulnerability:** The web dashboard (aiohttp) was vulnerable to Cross-Site Scripting (XSS) because user-controlled data (usernames, last fruits, suspension reasons) were rendered directly in HTML templates without escaping. Additionally, the HTTP Basic Auth was vulnerable to timing attacks due to standard string comparison.

**Learning:** When using `str.format()` or f-strings to generate HTML in Python, automatic escaping is not provided. Furthermore, local variables named `html` will shadow the `html` module, leading to `UnboundLocalError` if the module is needed within the same scope.

**Prevention:** Always use `html.escape()` for any data sourced from users or the database when rendering HTML. Use `secrets.compare_digest()` for comparing sensitive credentials. Avoid naming variables after imported modules to prevent shadowing.
