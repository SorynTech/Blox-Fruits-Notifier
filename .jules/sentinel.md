## 2025-05-15 - UnboundLocalError when shadowing module name
**Vulnerability:** Not a vulnerability itself, but a side effect of a security fix.
**Learning:** Importing the `html` module and then using `html` as a local variable name within a function causes an `UnboundLocalError` in Python if the local variable is assigned anywhere in the function. This is because Python treats the name as a local variable for the entire scope, shadowing the module.
**Prevention:** Avoid using standard library module names (like `html`, `json`, `os`) as local variable names. Use more descriptive names like `response_html` or `users_html`.
