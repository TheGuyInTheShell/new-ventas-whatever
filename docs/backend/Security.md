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

Shield is a hierarchical, high-performance permission management system designed for FastAPI applications. It provides a declarative way to define, discover, and enforce security policies at the class, method, or even argument level.

### Key Components

- **Registry (`core/security/shield/registry.py`)**: A hierarchical singleton store that organizes permissions by context (modules or features).
- **Scanner (`core/security/shield/scanner.py`)**: An automated discovery tool that scans directories for classes and methods decorated with Shield metadata during application startup.
- **Provider (`core/security/shield/provider.py`)**: The resolution engine. It evaluates whether a user (via `Request`) satisfies a permission requirement using a customizable `ResolverProvider` or `BasicResolverProvider`.
- **Facade (`core/security/shield/shield.py`)**: The primary entry point for developers, offering decorators and imperative utilities. It now supports runtime resolver mapping by path or context.

### Declarative Usage (Decorators)

Shield encourages a declarative approach to security by using decorators on controllers.

#### 1. Context Registration
Use `@Shield.register` at the class level to establish a default context for all permissions within that class.

```python
@Shield.register(context="Finance")
class FinanceTemplate(Template):
    # All methods here default to the "Finance" context
    ...
```

#### 2. Endpoint Protection
Use `@Shield.need` to protect specific endpoints. Shield will automatically inject a FastAPI `Depends` guard that validates the permission before execution. You can also provide optional `meta` for additional validation context.

```python
@Shield.register(context="Portfolio")
class PortfolioController:
    @Get("/assets")
    @Shield.need(
        name="Assets", 
        action="view", 
        type="READ", 
        description="View user assets",
        meta=[("scope", "internal")]
    )
    async def get_assets(self, request: Request):
        return {"data": "..."}
```

#### 3. Basic Validation
For general protection layers (like API Key or JWT validation without specific granular permissions), use `@Shield.basic`. This decorator accepts a `BasicResolverProvider`.

```python
from core.security.shield import BasicResolverProvider

class MyApiKeyResolver(BasicResolverProvider):
    def resolve(self, request: Request) -> bool:
        return request.headers.get("X-API-KEY") == "secret"

@Shield.basic(resolver=MyApiKeyResolver())
async def secure_endpoint(request: Request):
    ...
```

#### 4. Argument-Level Protection (Advanced)
Shield allows marking specific function arguments as protected using `@Shield.arg`. This is useful for injecting permissions that are evaluated against specific data inputs.

```python
@Get("/user/{user_id}")
async def get_user(
    request: Request, 
    user_id: str,
    permission = Shield.arg("User", "view", "READ", "View user details", default=None)
):
    ...
```

### Imperative Usage and Manual Registration

When decorators are not sufficient, Shield provides imperative methods for manual control.

#### Manual Registration
Permissions can be registered manually during application initialization.

```python
Shield.create(
    name="Report", 
    action="export", 
    type="WRITE", 
    description="Export financial reports", 
    context="Finance"
)
```

#### Imperative Permission Checks
For logic-heavy permission checks within a function body, use `Shield.use`. This method returns a wrapper that expects a `ResolverProvider` and a callback.

```python
def process_sensitive_data(provider: ResolverProvider):
    # Check permission and execute callback if authorized
    return Shield.use("Data", "access", "READ", "Core")(
        provider, 
        lambda: "Sensitive Data Content"
    )
```

To avoid manual registration of every permission, use `Shield.scan` during the application's initialization. You can now map specific resolvers to paths or contexts during scanning.

```python
# In main.py or lifespan
Shield.scan(
    path="src/api", 
    callback=lambda registry_dict: print(f"Registered {len(registry_dict)} permissions"),
    context="Global",
    resolver=MyDefaultResolver() # Optional: Default resolver for this entire path
)
```

---

## FastAPI Guards and Middleware

The application integrates a custom `FastAPI_Guard` extension that applies global security policies via middleware.

### SecurityMiddleware
The `SecurityMiddleware` (`guard.middleware.SecurityMiddleware`) processes all incoming requests and can enforce global security rules (like valid JWT or API keys) before they reach the endpoint handlers.

### Extension Registration
To enable the guard globally, register it as an extension:

```python
# In main.py
from core.security.guards import FastAPI_Guard

app = FastAPI(...)
FastAPI_Guard(app).extends()
```

---

## Services Integration: PermissionsTree

For high-level management and representation of the permission hierarchy, the application provides the `PermissionsTree` service (`core/services/permissions/__init__.py`). 

This service can be used to:
- Generate unique deterministic signatures for permissions (`get_sign`).
- Retrieve all registered permissions in an ordered manner for UI or synchronization (`get_all`).
- Facilitate the creation of hierarchical nodes for database persistence.

Best practices suggest using `Shield` for runtime enforcement and `PermissionsTree` for administrative operations and persistence logic.


## Implementation Guidelines

### Best Practices
1. **Always use CSRF for forms**: Even if using HTMX, ensure tokens are included in the headers or payload.
2. **Granular Permissions**: Define specific permissions rather than broad roles. Use the `shield.py` utilities to register these during app initialization.
3. **Automated Scanning**: Ensure new modules with permission requirements are added to the scanner's search path in `main.py`.
