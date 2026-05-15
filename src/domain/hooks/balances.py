import inspect
import functools
from typing import Callable, TypeVar, cast
from core.events import ChannelEvent
from fastapi import FastAPI
from .value_with_comparison import _wrap_hooks_handler

channel = ChannelEvent()

T = TypeVar("T")

def on_balance_updated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to register a function to run when a balance is updated."""
    handler = _wrap_hooks_handler(func)
    return cast(
        Callable[..., T],
        channel.subscribe_to(
            "balance.updated", action="after", handler=handler
        ),
    )

def trigger_balance_updated(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Decorator to trigger the balance.updated event after a successful execution."""

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
                channel.emit_to("balance.updated").run(data)
        elif result:
            channel.emit_to("balance.updated").run(result)

        return result

    return cast(Callable[..., T], wrapper)
