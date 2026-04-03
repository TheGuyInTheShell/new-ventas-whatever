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
from functools import wraps
from typing import Callable, Optional

from fastapi import Request

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
        @wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> object:
            # Resolve the Request object from the handler signature
            request: Optional[Request] = kwargs.get("request")  # type: ignore[assignment]
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                # Cannot cache without a request context — fall through
                return await func(*args, **kwargs)

            cache: Optional[CacheProvider] = getattr(
                request.app.state, "CACHE", None
            )
            if cache is None:
                # No cache driver registered — execute without caching
                return await func(*args, **kwargs)

            # --- build cache key ---
            if key_builder is not None:
                cache_key = key_builder(request)
            else:
                effective_prefix = prefix or func.__name__
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

        return wrapper

    return decorator
