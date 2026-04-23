## 2026-04-23 - [Variable Shadowing Blocking Security Mitigation]
**Vulnerability:** XSS and potential logic errors due to `html` standard library shadowing.
**Learning:** The codebase consistently used a local variable named `html` to store generated HTML strings in `aiohttp` handlers. This shadowed the `html` standard library module, preventing the use of `html.escape()` for sanitization within those functions without refactoring.
**Prevention:** Follow a naming convention for HTML string variables (e.g., `page_html` or `response_html`) and always import the `html` module at the top level to ensure sanitization tools are readily available.
