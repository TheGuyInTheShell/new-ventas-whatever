import functools
import asyncio
from typing import Callable, TypeVar, Any, ParamSpec, Coroutine, Optional
from enum import Enum
from fasthtml.common import ScriptX

# ParamSpec preserves the original function's parameters (e.g. self, request)
# TypeVar R preserves the original return type (e.g. HTMLResponse)
P = ParamSpec("P")
R = TypeVar("R")


def Script(
    src: Optional[str] = None,
    nomodule: Optional[bool] = None,
    type: Optional[str] = None,
    _async: Optional[bool] = None,
    defer: Optional[bool] = None,
    charset: Optional[str] = None,
    crossorigin: Optional[str] = None,
    integrity: Optional[str] = None,
    **kw: Any,
) -> str:
    """Helper for ScriptX."""
    return str(
        ScriptX(
            "./core/services/ui/none.js",
            src,
            nomodule,
            type,
            _async,
            defer,
            charset,
            crossorigin,
            integrity,
            **kw,
        )
    )


class Site(Enum):
    """Available locations for injecting code in the HTML template."""

    HEAD = "head"
    BODY_BEFORE = "body_before"
    BODY_AFTER = "body_after"


def enqueue_js(
    js_tag: Any, position: Site = Site.BODY_AFTER
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enqueue a script tag into the template globals."""

    def decorator(class_method: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(class_method)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            # We assume a class method where the first argument is the class instance (self).
            # The instance has access to its templates (self.templates).
            if args:
                instance: Any = args[0]
                if hasattr(instance, "templates"):
                    template_provider: Any = instance.templates
                    injectable = template_provider.env.globals["_injectable"]
                    
                    section = position.value
                    if section == "head":
                        injectable["head"]["scripts"] += f"\n{js_tag}"
                    elif section == "body_before":
                        injectable["body"]["scripts_before"] += f"\n{js_tag}"
                    elif section == "body_after":
                        injectable["body"]["scripts_after"] += f"\n{js_tag}"

            # Original async support: if the method is async, we return the coroutine.
            # FastAPI/Uvicorn handles awaiting the result of the decorator.
            return class_method(*args, **kwargs)

        return inner

    return decorator