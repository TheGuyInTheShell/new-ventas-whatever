import inspect
import functools
import inspect
from typing import Callable, TypeVar, Any, ParamSpec, Coroutine, Optional
from enum import Enum
from fastcore.xml import Script as ScriptX

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
            src=src,
            nomodule=nomodule,
            type=type,
            _async=_async,
            defer=defer,
            charset=charset,
            crossorigin=crossorigin,
            integrity=integrity,
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

        # We need to check if the route is async so we handle it properly.
        is_coroutine = inspect.iscoroutinefunction(class_method)

        if is_coroutine:

            @functools.wraps(class_method)
            async def async_inner(*args: P.args, **kwargs: P.kwargs) -> Any:
                injectable = None
                try:
                    if args:
                        instance: Any = args[0]
                        if hasattr(instance, "templates"):
                            template_provider: Any = instance.templates
                            injectable = template_provider.env.globals.get(
                                "_injectable"
                            )

                            if injectable:
                                section = position.value
                                if section == "head":
                                    injectable["head"]["scripts"] += f"\n{js_tag}"
                                elif section == "body_before":
                                    injectable["body"][
                                        "scripts_before"
                                    ] += f"\n{js_tag}"
                                elif section == "body_after":
                                    injectable["body"]["scripts_after"] += f"\n{js_tag}"

                    import typing

                    _async_callable = typing.cast(
                        typing.Callable[..., typing.Awaitable[typing.Any]], class_method
                    )
                    return await _async_callable(*args, **kwargs)
                finally:
                    if injectable:
                        # Ensures the context gets emptied after being returned to client.
                        injectable["body"]["scripts_after"] = ""
                        injectable["body"]["scripts_before"] = ""
                        injectable["head"]["scripts"] = ""

            from typing import cast

            return cast(Callable[P, R], async_inner)

        else:

            @functools.wraps(class_method)
            def sync_inner(*args: P.args, **kwargs: P.kwargs) -> Any:
                injectable = None
                try:
                    if args:
                        instance: Any = args[0]
                        if hasattr(instance, "templates"):
                            template_provider: Any = instance.templates
                            injectable = template_provider.env.globals.get(
                                "_injectable"
                            )

                            if injectable:
                                section = position.value
                                if section == "head":
                                    injectable["head"]["scripts"] += f"\n{js_tag}"
                                elif section == "body_before":
                                    injectable["body"][
                                        "scripts_before"
                                    ] += f"\n{js_tag}"
                                elif section == "body_after":
                                    injectable["body"]["scripts_after"] += f"\n{js_tag}"

                    return class_method(*args, **kwargs)
                finally:
                    if injectable:
                        injectable["body"]["scripts_after"] = ""
                        injectable["body"]["scripts_before"] = ""
                        injectable["head"]["scripts"] = ""

            from typing import cast

            return cast(Callable[P, R], sync_inner)

    return decorator
