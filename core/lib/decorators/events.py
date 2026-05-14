from core.events import ChannelEvent
from core.events.types import TAction
from typing import Callable, ParamSpec, TypeVar
import inspect

P = ParamSpec("P")
R = TypeVar("R")


class Channel:
    @classmethod
    def subscribe_to(cls, event: str, action: TAction = "after") -> Callable[[Callable[P, R]], Callable[P, R]]:
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            
            # Annote the function for potential auto-routers (e.g. class methods)
            setattr(func, "__channel_event__", event)
            setattr(func, "__channel_action__", action)
            
            # Auto-register global functions (not attached to a class natively).
            # We assume it's global if 'self' is not the first parameter.
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            if not params or params[0] != 'self':
                ChannelEvent().subscribe_to(event, action, handler=func)
                
            return func
        return decorator