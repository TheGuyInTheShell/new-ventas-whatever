import inspect
import functools
from typing import Callable, TypeVar, cast
from core.events import ChannelEvent
from core.lib.hooks.wrapper import _wrap_hooks_handler

channel = ChannelEvent()

T = TypeVar("T")


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
