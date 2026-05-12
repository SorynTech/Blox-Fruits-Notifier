## 2025-05-13 - XSS in Server-Side Rendered Dashboard
**Vulnerability:** User-controlled data (usernames, roll history, suspension reasons) were directly injected into HTML f-strings in aiohttp handlers, allowing for Cross-Site Scripting (XSS).
**Learning:** Even internal or semi-protected dashboards (behind Basic Auth) are vulnerable if they display data sourced from external interfaces (like Discord commands). Python's f-strings do not provide automatic HTML escaping.
**Prevention:** Always wrap user-controlled or database-sourced data in `html.escape(str(data))` when building HTML strings. Using `str()` ensures that non-string types (like None or timestamps) don't cause a TypeError during escaping.
