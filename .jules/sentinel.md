# Sentinel Journal 🛡️

## 2025-05-14 - Web Dashboard Security Hardening
**Vulnerability:** Multiple security issues in the aiohttp web dashboard:
1. **Cross-Site Scripting (XSS):** User-controlled data (usernames, fruit names, suspension reasons) was injected directly into HTML templates without escaping.
2. **Timing Attack:** HTTP Basic Auth used standard `==` string comparison for credentials.
3. **Information Leakage:** Raw exceptions were returned in HTTP responses.
4. **Variable Shadowing:** Local variable `html` shadowed the `html` standard library module, complicating proper escaping.

**Learning:** Server-side rendered templates that use string formatting (like `.format()`) are highly susceptible to XSS if every dynamic value isn't explicitly sanitized. Additionally, standard string comparisons for secrets can leak information about the secret's value through execution time differences.

**Prevention:**
- Always use `html.escape()` for any data being rendered in HTML.
- Use `secrets.compare_digest()` for credential comparisons.
- Wrap web handlers in try-except blocks that return generic error messages to the user while logging details internally.
- Avoid naming variables after standard library modules.
