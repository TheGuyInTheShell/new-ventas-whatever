# Endpoint Registration and Controllers

The application uses a class-based approach for defining API and Template endpoints. This system leverages custom decorators and an automated router to discover and register routes in FastAPI.

## Controllers and Templates

Endpoints are grouped into classes that inherit from either `Controller` or `Template`.

- **Controller (`core/lib/register/controller.py`)**: Used for API endpoints that return data (JSON, etc.).
- **Template (`core/lib/register/template.py`)**: Used for web endpoints that render HTML templates.

### Basic Structure

```python
from core.lib.register import Controller
from core.lib.decorators import Get, Post

class UsersController(Controller):
    @Get("/")
    async def list_users(self):
        return [{"id": 1, "name": "John"}]

    @Post("/")
    async def create_user(self, name: str):
        return {"id": 2, "name": name}
```

---

## Custom HTTP Decorators

Instead of using standard FastAPI path operations, the project provides custom decorators for each HTTP method. These decorators are shortcuts that store route metadata for the auto-router.

### Available Decorators
- `@Get(path, **kwargs)`
- `@Post(path, **kwargs)`
- `@Put(path, **kwargs)`
- `@Delete(path, **kwargs)`
- `@Patch(path, **kwargs)`
- `@Head(path, **kwargs)`
- `@Options(path, **kwargs)`

These decorators support all standard FastAPI parameters such as `response_model`, `status_code`, `dependencies`, and `tags`.

---

## Dependency Injection Mechanism (`__dependencies__`)

One of the most powerful features of the custom decorators is the support for the `__dependencies__` mechanism. This allows third-party decorators (like **Shield**) to inject FastAPI `Depends()` objects into the route registration without manually adding them to the handler signature.

### How it Works
1. A decorator like `@Shield.need(...)` attaches a list of dependencies to the function's `__dependencies__` attribute.
2. The `@Get` (or other method) decorator checks for this attribute.
3. It automatically merges these dependencies into the `dependencies` list passed to FastAPI's router.

### Example: Shield Integration

```python
class SecureController(Controller):
    @Get("/data")
    @Shield.need(name="data:view", action="read", type="endpoint")
    async def get_secure_data(self):
        return {"content": "Top Secret"}
```

In the example above, `@Shield.need` is NOT a FastAPI decorator, but because it populates `__dependencies__`, the `@Get` decorator ensures that the security guard is executed before the handler.

---

## Automated Routing

Routes are registered automatically during application startup by the `auto_router_api` and `auto_router_templates` utilities.

1. **Scanning**: The system scans defined directories (e.g., `src/api`) for files named `controller.py`.
2. **Discovery**: It identifies classes inheriting from `Controller`.
3. **Registration**: It reads the `RouteDefinition` stored by the decorators and registers them in the FastAPI `APIRouter`.

This approach ensures a clean separation of concerns and eliminates manual route wiring in `main.py`.
