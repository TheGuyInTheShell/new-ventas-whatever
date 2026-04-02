import functools
from typing import Callable, TypeVar, Any, ParamSpec, Coroutine, Type, Union
from enum import Enum
from fasthtml import *

# ParamSpec preserves the original function's parameters (e.g. self, request)
# TypeVar R preserves the original return type (e.g. HTMLResponse)
P = ParamSpec("P")
R = TypeVar("R")


class Site(Enum):
    """Available locations for injecting code in the HTML template."""

    HEAD = "head"
    BODY_BEFORE = "body_before"
    BODY_AFTER = "body_after"


def enqueue_js(
    js_tag: Any, position: Site = Site.BODY_AFTER
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enqueue a script tag in a specific site/location.

    Args:
        js_tag: The script tag or string to inject.
        position: The location (HEAD, BODY_BEFORE, BODY_AFTER) where the script
            will be placed.
    """

    def decorator(class_method: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(class_method)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            # 'args[0]' represents 'self' if used in a Template class method.
            if args:
                instance: Any = args[0]
                if hasattr(instance, "templates"):
                    # We access the Jinja2Templates instance from the controller.
                    template_provider: Any = instance.templates
                    injectable = template_provider.env.globals.get("_injectable")

                    if injectable is not None:
                        # Append the tag based on the target position.
                        # Using [position.value] allows dynamic keyed access.
                        # Note: We currently append to the string as requested.
                        section = position.value
                        if section == "head":
                            injectable["head"]["scripts"] += f"\n{js_tag}"
                        else:
                            injectable["body"][f"scripts_{section.split('_')[1]}"] += (
                                f"\n{js_tag}"
                            )

            # Ensure we await the original async method.
            return await class_method(*args, **kwargs)  # type: ignore[no-any-return]

        return inner  # type: ignore[no-any-return]

    return decorator