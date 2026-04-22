## 2025-05-15 - [Python Module Shadowing and XSS]
**Vulnerability:** XSS in web dashboard due to unescaped user-provided strings.
**Learning:** Importing the `html` module while using a local variable named `html` for HTML strings leads to an `UnboundLocalError` or `AttributeError` because the local name shadows the module.
**Prevention:** Use descriptive local variable names like `response_html` and always sanitize user-controlled input with `html.escape()` before rendering in templates.
