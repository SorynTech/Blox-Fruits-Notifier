## 2026-05-05 - Variable Shadowing of Sanitization Modules
**Vulnerability:** XSS Sanitization Bypass/Crash
**Learning:** In Python, assigning a value to a variable name that matches an imported module (e.g., `html = "..."`) within a function makes that name local to the entire function scope. Any attempt to use the module (e.g., `html.escape()`) before the local assignment will result in an `UnboundLocalError`. This can lead to a Denial of Service or developers skipping sanitization to "fix" the crash.
**Prevention:** Avoid using variable names that shadow standard library modules, especially those used for security (like `html`, `secrets`, `json`). Use descriptive names like `response_html` or `json_data` instead.
