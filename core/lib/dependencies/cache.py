"""
FastAPI dependency to inject the active CacheProvider from app.state.CACHE.

Usage in any route:

    from core.lib.dependencies.cache import get_cache, CacheDep

    @router.get("/items")
    async def list_items(cache: CacheDep):
        ...
"""

from typing import Annotated

from fastapi import Depends, Request

from core.lib.base.cache_provider import CacheProvider


async def get_cache(request: Request) -> CacheProvider:
    """
    Extract the CacheProvider instance from the application state.
    Raises RuntimeError if no cache driver has been registered.
    """
    cache: CacheProvider | None = getattr(request.app.state, "CACHE", None)
    if cache is None:
        raise RuntimeError(
            "No CacheProvider registered on app.state.CACHE. "
            "Ensure a cache plugin (Redis / Memcached) is active and the "
            "CACHE_DRIVER environment variable is set correctly."
        )
    return cache


CacheDep = Annotated[CacheProvider, Depends(get_cache)]
