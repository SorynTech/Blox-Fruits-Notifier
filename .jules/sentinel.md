# Sentinel's Journal - Security Learnings

## 2025-05-14 - XSS and Timing Attacks in Aiohttp Dashboard
**Vulnerability:** Multiple Cross-Site Scripting (XSS) vulnerabilities in the stats and suspended user dashboards, plus a timing attack vulnerability in HTTP Basic Authentication.
**Learning:** The application was using Python's f-strings to build HTML templates without any sanitization of user-controlled data (usernames, fruit names, reasons). Additionally, using `==` for password comparison allowed for potential timing attacks to brute-force credentials. Shadowing the `html` standard library module with a local variable also made it difficult to use `html.escape()` correctly.
**Prevention:** Always use `html.escape()` for any dynamic data embedded in HTML. Use `secrets.compare_digest()` for credential comparisons. Implement security headers (CSP, X-Frame-Options) as a defense-in-depth measure. Avoid shadowing standard library names.
