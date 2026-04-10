# Security Architecture

This document describes the security mechanisms implemented in the core of the application, focusing on CSRF protection and the Shield permission system.

## CSRF Protection

The application implements a custom CSRF (Cross-Site Request Forgery) protection layer based on the **Double Submit Cookie** pattern.

### Implementation Details
- **Location**: `core/security/csrf/`
- **CSRFMiddleware**: An ASGI middleware that intercepts non-safe requests (POST, PUT, DELETE) and validates that the `X-CSRF-Token` header (or form field) matches the value stored in the session cookie.
- **CSRFExtension**: Automatically integrates the middleware and ensures that the `csrf_token` is available in the Jinja2 context for all templates.

### Usage
To protect an endpoint and ensure a token is generated for the form:

```python
from core.security.csrf.csrf import CSRF

class MyTemplate(Template):
    @Get("/form")
    @CSRF() # Generates and ensures token availability
    async def get_form(self, request: Request):
        return self.templates.TemplateResponse(...)
```

In the HTML:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

---

## Shield: Permission System

Shield is a hierarchical, robust permission management system that controls access to various parts of the application.

### Key Components
- **Registry (`core/security/shield/registry.py`)**: A central store for all registered permissions in the system.
- **Scanner (`core/security/shield/scanner.py`)**: Automatically scans designated modules (folders) to discover and register permission metadata.
- **Provider (`core/security/shield/provider.py`)**: The engine that evaluates whether a particular user has the required permission to perform an action.

### Hierarchical Permissions
Shield allows for specialized permission strings (e.g., `finance.reports.view`) which can be grouped and managed as a hierarchy.

### Guards and Protection
Shield integrates with the FastAPI routing system to act as a "Guard". 
- When an endpoint is protected by a Shield guard, the system verifies the user's role and permission set BEFORE the request reaches the controller.
- It leverages the `fastapi-guard` extension to provide automated security checks.

## Implementation Guidelines

### Best Practices
1. **Always use CSRF for forms**: Even if using HTMX, ensure tokens are included in the headers or payload.
2. **Granular Permissions**: Define specific permissions rather than broad roles. Use the `shield.py` utilities to register these during app initialization.
3. **Automated Scanning**: Ensure new modules with permission requirements are added to the scanner's search path in `main.py`.
