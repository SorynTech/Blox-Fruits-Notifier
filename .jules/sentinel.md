## 2026-05-13 - [Module Shadowing causing UnboundLocalError]
**Vulnerability:** Not a direct vulnerability, but a bug that disabled security controls.
**Learning:** Using a local variable named 'html' (standard for response bodies in this project) shadows the 'html' library module, leading to UnboundLocalError when trying to use html.escape().
**Prevention:** Use descriptive names like 'response_html' or 'page_html' for local string variables to avoid shadowing security-critical library modules.
