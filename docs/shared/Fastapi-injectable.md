# internal Dependency Injection with `fastapi_injectable`

The project utilizes the `fastapi_injectable` library to enable FastAPI-style dependency resolution (`Depends()`) in contexts where a standard HTTP request doesn't exist, such as service layers, background tasks, and application lifespan hooks.

## Purpose

Standard FastAPI dependencies rely on the `Request` object provided by a route handler. Service-layer methods or startup tasks (like syncing permissions from `Shield.scan`) often need access to the database or cache but aren't called via HTTP. `fastapi_injectable` bridges this gap.

## Initialization

The system is initialized globally during the application lifespan:

```python
# core/lib/register/plugin_loader.py

from fastapi_injectable import register_app

async def plugin_lifespan(app: FastAPI):
    ...
    # Register injectable dependencies
    await register_app(app)
    ...
```

---

## The `@injectable` Decorator

By marking a method with `@injectable`, the library intercepts calls and automatically resolves any `Depends()` parameters.

```python
from fastapi_injectable import injectable
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

class PermissionsService(Service):
    @injectable
    async def get_permission(self, name: str, db: AsyncSession = Depends(get_async_db)):
        # `db` is resolved even if called from a background task or startup hook
        ...
```

---

## Lifespan Injection and Mock Requests

A critical feature of this implementation is the ability to resolve dependencies during the `on_app_ready` phase or within asynchronous background tasks.

### Mock Request Logic
`fastapi_injectable` generates a **"Mock Request"** (an object with a `.app` attribute) specifically for dependencies that require the current application state (like `get_db` or `get_cache`).

- **No HTTP Overhead**: This mock request doesn't contain headers, query params, or body data.
- **State Access**: It provides just enough context (`request.app.state`) for core dependencies to function.

### Example in Background Tasks
When `Shield.scan` triggers a synchronization callback, it runs in a background task using `asyncio.create_task`. Because the processing method is `@injectable`, it can resolve the database session even though it's disconnected from the original HTTP flow.

```python
@injectable
async def _process_shield_permissions(
    self,
    registry_dict: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db) # Automatically resolved
):
    ...
```

---

## Benefits for Testing

The combination of `@injectable` and mock requests allows developers to:
1.  **Test services in isolation**: Pass a mock or real DB session to service methods without spinning up the entire FastAPI server.
2.  **Verify lifespan logic**: Execute startup hooks during unit tests while ensuring dependencies are correctly resolved.
