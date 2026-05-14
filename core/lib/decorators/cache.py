"""
Caching decorator for FastAPI endpoints.

Automatically caches the JSON-serializable return value of an endpoint
keyed by route + query parameters.  Pulls the CacheProvider from
`request.app.state.CACHE` at runtime so it stays fully decoupled from
any concrete driver.

Usage:

    from core.lib.decorators.cache import cached

    @router.get("/products")
    @cached(ttl=600, prefix="products")
    async def list_products(request: Request):
        ...

    # Or with a custom key builder:
    @router.get("/products/{product_id}")
    @cached(ttl=300, key_builder=lambda req: f"product:{req.path_params['product_id']}")
    async def get_product(request: Request, product_id: int):
        ...
"""

import hashlib
import json
import inspect
from functools import wraps
from typing import Callable, Optional, Annotated, cast, Any

from fastapi import Request, Depends
from fastapi_injectable import injectable

from core.lib.base.cache_provider import CacheProvider


def cached(
    ttl: int = 300,
    prefix: Optional[str] = None,
    key_builder: Optional[Callable[[Request], str]] = None,
) -> Callable:
    """
    Decorator that caches the response of a FastAPI endpoint handler.

    Args:
        ttl:         Time-to-live in seconds.
        prefix:      Key prefix (defaults to the function name).
        key_builder: Optional callable that receives the Request and returns a
                     custom cache key string. When provided, `prefix` is ignored.
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        needs_request = True
        for param in sig.parameters.values():
            if param.name == "request" or param.annotation is Request:
                needs_request = False
                break

        @wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> object:
            request = cast(Optional[Request], kwargs.get("request"))

            if needs_request and "request" in kwargs:
                # Remove dynamically injected request to avoid unexpected kwarg errors
                kwargs.pop("request")

            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                # Cannot cache without a request context — fall through
                return await func(*args, **kwargs)

            cache: Optional[CacheProvider] = getattr(request.app.state, "CACHE", None)
            if cache is None:
                # No cache driver registered — execute without caching
                return await func(*args, **kwargs)

            # --- build cache key ---
            if key_builder is not None:
                cache_key = key_builder(request)
            else:
                effective_prefix = prefix or getattr(func, "__name__", "unknown")
                key_data = json.dumps(
                    {
                        "path": request.url.path,
                        "query": str(request.query_params),
                    },
                    sort_keys=True,
                )
                key_hash = hashlib.md5(key_data.encode()).hexdigest()
                cache_key = f"{effective_prefix}:{key_hash}"

            # --- check cache ---
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # --- execute handler & store ---
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        if needs_request:
            params_list = list(sig.parameters.values())
            insert_idx = len(params_list)
            for i, p in enumerate(params_list):
                if p.kind == inspect.Parameter.VAR_KEYWORD:
                    insert_idx = i
                    break
            params_list.insert(
                insert_idx,
                inspect.Parameter(
                    "request", inspect.Parameter.KEYWORD_ONLY, annotation=Request
                ),
            )
            setattr(wrapper, "__signature__", sig.replace(parameters=params_list))

        return wrapper

    return decorator


# Define your dependencies that need app state access
async def get_request(*, request: Request) -> Request:
    return request


def func_cached(
    ttl: int = 300,
    prefix: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable:
    """
    Decorator that caches the return value of a *service-layer* method.

    Unlike :func:`cached` (which targets FastAPI endpoint handlers and keys on
    the HTTP request URL + query params), this variant is designed for
    injectable service methods that:

    - Are called programmatically, not directly from an HTTP handler.
    - May receive a *mock* ``Request`` with no real path, query params, or
      other HTTP fields — only ``request.app.state.CACHE`` is guaranteed.
    - Must derive the cache key from the actual **call arguments**, not from
      HTTP metadata.

    Key-building strategy (no ``key_builder`` supplied):
        ``<prefix>:<md5(sorted json of stringified non-db/non-request args)>``

    Usage::

        @injectable
        @func_cached(ttl=60, prefix="auth:get_user")
        async def get_user(self, username: str, db: AsyncSession = ...) -> User:
            ...

    Args:
        ttl:         Time-to-live in seconds.
        prefix:      Key prefix (defaults to ``func.__qualname__``).
        key_builder: Optional callable ``(func, args, kwargs) -> str`` that
                     returns the full cache key.  When supplied, ``prefix``
                     is ignored.
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())  # ordered param names

        @wraps(func)
        @injectable
        async def wrapper(
            *args: object, request: Request = Depends(get_request), **kwargs: object
        ) -> object:
            # ----------------------------------------------------------------
            # 1. Locate CacheProvider
            #    fastapi_injectable injects a Request-like object so services
            #    can reach app.state.  We only use it for the CACHE reference.
            # ----------------------------------------------------------------
            cache: Optional[CacheProvider] = None

            # Check kwargs first (injectable may pass request as kwarg)
            req: Optional[object] = request
            # Then scan positional args (skip 'self' at index 0)
            if req is None:
                return await func(*args, **kwargs)

            if req is not None:
                app_state = getattr(getattr(req, "app", None), "state", None)
                cache = getattr(app_state, "CACHE", None)

            if cache is None:
                # No cache driver registered — execute without caching
                return await func(*args, **kwargs)

            # ----------------------------------------------------------------
            # 2. Build cache key from the actual call arguments
            #    Services receive db sessions and mock Requests — skip those.
            # ----------------------------------------------------------------
            if key_builder is not None:
                cache_key = key_builder(func, args, kwargs)
            else:
                effective_prefix = prefix or getattr(func, "__qualname__", "unknown")

                # Map positional args to their parameter names (skip 'self')
                named: dict = {}
                for i, arg in enumerate(args):
                    if i >= len(param_names):
                        break
                    pname = param_names[i]
                    if pname == "self":
                        continue
                    # Skip async session objects and request-like objects
                    if hasattr(arg, "execute") or hasattr(arg, "app"):
                        continue
                    named[pname] = str(arg)

                # Include keyword args, skipping db/session/request objects
                for k, v in kwargs.items():
                    if k in ("db", "request", "session"):
                        continue
                    if hasattr(v, "execute") or hasattr(v, "app"):
                        continue
                    named[k] = str(v)

                key_data = json.dumps(named, sort_keys=True)
                key_hash = hashlib.md5(key_data.encode()).hexdigest()
                cache_key = f"{effective_prefix}:{key_hash}"

            # ----------------------------------------------------------------
            # 3. Cache read → execute → cache write
            # ----------------------------------------------------------------
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
