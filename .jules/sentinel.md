## 2025-05-14 - Python Module Shadowing in Web Handlers
**Vulnerability:** Not a direct vulnerability, but caused the application to crash (DoS) after implementing XSS protection using the `html` module.
**Learning:** Multiple web handlers (`handle_health`, `handle_stats`, `handle_suspended`) used `html` as a local variable name for the final response string. Importing the `html` module at the top level and then attempting to use `html.escape()` inside these functions caused an `UnboundLocalError` because Python shadowed the module name with the local variable.
**Prevention:** Always use descriptive names for HTML response strings (e.g., `response_html`) and avoid using standard library module names as local variables.
