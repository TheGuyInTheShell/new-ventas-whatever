from typing import Callable, Any
from core.events import ChannelEvent
from fastapi import FastAPI

channel = ChannelEvent()

def on_app_init(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to register a function to run during the `app.init` phase."""
    return channel.subscribe_to("app.init", action="after", handler=func)

def on_app_ready(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to register a function to run during the `app.ready` phase."""
    return channel.subscribe_to("app.ready", action="after", handler=func)

def on_app_shutdown(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to register a function to run during the `app.shutdown` phase."""
    # Shutdown logic should run before the core terminates
    return channel.subscribe_to("app.shutdown", action="before", handler=func)