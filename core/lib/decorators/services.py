import functools
from typing import Any, Callable, Type, TypeVar

from core.lib.register.service import Service

T = TypeVar("T", bound=type)


def Services(*service_classes: Type[Service]) -> Callable[[T], T]:
    """
    Class decorator to inject service instances directly into a controller or object.

    It modifies the class's __init__ method to automatically instantiate
    the provided service classes and attach them directly to `self` using
    the service's class name.

    Usage:
        @Services(AuthService, UserService)
        class AuthController(Controller):
            # Optional type hints for IDE autocompletion
            AuthService: "AuthService"
            UserService: "UserService"

            async def sign_in(self):
                # Access injected service directly on self
                user = await self.AuthService.authenticate_user(...)
    """

    def decorator(cls: T) -> T:
        original_init = getattr(cls, "__init__", object.__init__)

        @functools.wraps(original_init)
        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Call the original __init__ if it exists and is not object.__init__
            if original_init is not object.__init__:
                original_init(self, *args, **kwargs)

            # Instantiate each service and attach directly to the instance `self`
            for service_cls in service_classes:
                service_instance = service_cls()
                # Bind the instance by its class name (e.g. self.AuthService)
                setattr(self, service_cls.__name__, service_instance)

        setattr(cls, "__init__", new_init)
        return cls

    return decorator
