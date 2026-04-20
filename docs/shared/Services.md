# Service Layer and Dependency Injection

The application implements a decoupled architecture using a custom service layer. Services are responsible for business logic and data access, and they can be injected into any class using a custom decorator.

## Service Base Class

All services should inherit from the `Service` base class (`core/lib/register/service.py`).

```python
from core.lib.register import Service

class AuthService(Service):
    async def authenticate(self, credentials):
        ...
```

---

## Service Injection (@Services)

The `@Services` class decorator (`core/lib/decorators/services.py`) is the primary way to inject service instances. It automatically instantiates the requested service classes and attaches them to the instance of the decorated class.

### Usage

```python
from core.lib.decorators import Services
from src.modules.auth.services import AuthService
from src.modules.users.services import UsersService

@Services(AuthService, UsersService)
class MyController(Controller):
    # Optional typing for IDE support
    AuthService: AuthService
    UsersService: UsersService

    async def my_handler(self, request: Request):
        # Access services directly
        user = await self.UsersService.get_user(...)
        token = await self.AuthService.generate_token(user)
        return {"token": token}
```

### Benefits
- **Minimal Coupling**: Classes don't need to know how to instantiate their dependencies.
- **Improved Readability**: Constructors remain clean and focused on initialization logic.
- **Easy Mocking**: Service instances can be replaced easily during testing.

---

## Internal Dependency Resolution (fastapi_injectable)

To allow FastAPI-style dependency injection (`Depends()`) within the service layer (where there is no active request handler), the project integrates the `fastapi_injectable` library.

### @injectable Decorator
Use the `@injectable` decorator on service methods to resolve `Depends()` parameters internally.

```python
from fastapi_injectable import injectable
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db

class UsersService(Service):
    @injectable
    async def get_current_user(self, db: AsyncSession = Depends(get_async_db)):
        # `db` is automatically resolved here using the provided dependency
        ...
```

### Application Registration
The dependency injection system is initialized during the application lifespan in `core/lib/register/plugin_loader.py`:

```python
from fastapi_injectable import register_app

async def plugin_lifespan(app: FastAPI):
    ...
    await register_app(app)
    ...
```

### Testing and Mocking
`fastapi_injectable` is particularly useful for testing because it allows you to **mock FastAPI requests** and override dependencies within the service layer, enabling you to run service logic that relies on `Depends()` in isolation or during the application's lifespan setup.
