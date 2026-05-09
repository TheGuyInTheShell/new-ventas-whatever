import inspect
import functools
from typing import Callable, Any, TypeVar, Coroutine, cast
from core.events import ChannelEvent
from fastapi import FastAPI

channel = ChannelEvent()


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


def on_value_with_comparison_updated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to register a function to run during the `app.init` phase."""
    handler = _wrap_hooks_handler(func)
    return cast(
        Callable[..., T],
        channel.subscribe_to(
            "value_with_comparison.updated", action="after", handler=handler
        ),
    )


def trigger_value_with_comparison_updated(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Decorator to trigger the value_with_comparison.updated event after a successful execution."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        result = (
            await func(*args, **kwargs)
            if inspect.iscoroutinefunction(func)
            else func(*args, **kwargs)
        )

        # Check if the result is a ServiceResult tuple (Data, Error)
        if isinstance(result, tuple) and len(result) == 2:
            data, err = result
            if not err and data:
                channel.emit_to("value_with_comparison.updated").run(data)
        elif result:
            channel.emit_to("value_with_comparison.updated").run(result)

        return result

    return cast(Callable[..., T], wrapper)
