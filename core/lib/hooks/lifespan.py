import inspect
import functools
from typing import Callable, Any, Type, Optional
from core.events import ChannelEvent
from fastapi import FastAPI

channel = ChannelEvent()


def _wrap_lifespan_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wraps a function to support class methods in lifespan hooks.
    If the function is a method (has 'self'), it attempts to resolve the instance.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    is_method = params and params[0].name == "self"

    if not is_method:
        return func

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # If 'self' is already in args, just call it
        if args and isinstance(args[0], object) and not isinstance(args[0], FastAPI):
            return (
                await func(*args, **kwargs)
                if inspect.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

        # Try to resolve 'self' from the class
        qualname = getattr(func, "__qualname__", "")
        if "." in qualname:
            cls_name = qualname.rsplit(".", 1)[0]
            module = inspect.getmodule(func)
            cls = getattr(module, cls_name, None) if module else None

            if cls:
                instance = None
                try:
                    instance = cls()
                except:
                    pass

                if instance:
                    return (
                        await func(instance, *args, **kwargs)
                        if inspect.iscoroutinefunction(func)
                        else func(instance, *args, **kwargs)
                    )

        # Fallback to original call if resolution fails
        return (
            await func(*args, **kwargs)
            if inspect.iscoroutinefunction(func)
            else func(*args, **kwargs)
        )

    return wrapper


def on_app_init(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to register a function to run during the `app.init` phase."""
    handler = _wrap_lifespan_handler(func)
    return channel.subscribe_to("app.init", action="after", handler=handler)


def on_app_ready(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to register a function to run during the `app.ready` phase."""
    handler = _wrap_lifespan_handler(func)
    return channel.subscribe_to("app.ready", action="after", handler=handler)


def on_app_shutdown(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to register a function to run during the `app.shutdown` phase."""
    handler = _wrap_lifespan_handler(func)
    # Shutdown logic should run before the core terminates
    return channel.subscribe_to("app.shutdown", action="before", handler=handler)
