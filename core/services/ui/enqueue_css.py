import functools
import asyncio
from typing import Callable, TypeVar, Any, ParamSpec, Optional
from enum import Enum
from fasthtml.common import Link

# ParamSpec preserves the original function's parameters (e.g. self, request)
# TypeVar R preserves the original return type (e.g. HTMLResponse)
P = ParamSpec("P")
R = TypeVar("R")


def Style(
    href: Optional[str] = None,
    rel: str = "stylesheet",
    type: Optional[str] = None,
    media: Optional[str] = None,
    **kw: Any,
) -> str:
    """Helper for CSS Link tag."""
    # Build standard attributes
    attrs = {"rel": rel}
    if href:
        attrs["href"] = href
    if type:
        attrs["type"] = type
    if media:
        attrs["media"] = media
    attrs.update(kw)
    
    return str(Link(**attrs))


class CssSite(Enum):
    """Available locations for injecting CSS in the HTML template."""
    HEAD = "head"


def enqueue_css(
    css_tag: Any, position: CssSite = CssSite.HEAD
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enqueue a CSS link tag into the template globals."""

    def decorator(class_method: Callable[P, R]) -> Callable[P, R]:
        
        # We need to check if the route is async so we handle it properly.
        is_coroutine = asyncio.iscoroutinefunction(class_method)

        if is_coroutine:
            @functools.wraps(class_method)
            async def async_inner(*args: P.args, **kwargs: P.kwargs) -> Any:
                injectable = None
                try:
                    if args:
                        instance: Any = args[0]
                        if hasattr(instance, "templates"):
                            template_provider: Any = instance.templates
                            injectable = template_provider.env.globals.get("_injectable")
                            
                            if injectable:
                                section = position.value
                                if section == "head":
                                    injectable["head"]["styles"] += f"\n{css_tag}"

                    import typing
                    _async_callable = typing.cast(typing.Callable[..., typing.Awaitable[typing.Any]], class_method)
                    return await _async_callable(*args, **kwargs)
                finally:
                    if injectable:
                        # Ensures the context gets emptied after being returned to client.
                        injectable["head"]["styles"] = ""
            return async_inner  # type: ignore

        else:
            @functools.wraps(class_method)
            def sync_inner(*args: P.args, **kwargs: P.kwargs) -> Any:
                injectable = None
                try:
                    if args:
                        instance: Any = args[0]
                        if hasattr(instance, "templates"):
                            template_provider: Any = instance.templates
                            injectable = template_provider.env.globals.get("_injectable")
                            
                            if injectable:
                                section = position.value
                                if section == "head":
                                    injectable["head"]["styles"] += f"\n{css_tag}"

                    return class_method(*args, **kwargs)
                finally:
                    if injectable:
                        injectable["head"]["styles"] = ""
            return sync_inner  # type: ignore

    return decorator
