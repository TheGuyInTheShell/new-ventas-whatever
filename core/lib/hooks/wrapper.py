import inspect
import functools
from typing import Callable, TypeVar, cast
from fastapi import FastAPI

T = TypeVar("T")


def _wrap_hooks_handler(func: Callable[..., T]) -> Callable[..., T]:
    """
    Wraps a function to support class methods in hooks.
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

    return cast(Callable[..., T], wrapper)
