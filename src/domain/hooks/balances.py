from typing import Callable, TypeVar, cast
from core.events import ChannelEvent
from core.lib.hooks.wrapper import _wrap_hooks_handler

channel = ChannelEvent()

T = TypeVar("T")


def on_balance_updated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to register a function to run when a balance is updated."""
    handler = _wrap_hooks_handler(func)
    return cast(
        Callable[..., T],
        channel.subscribe_to("balance.updated", action="after", handler=handler),
    )
