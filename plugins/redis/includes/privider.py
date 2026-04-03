import asyncio
import json
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union

from redis.asyncio import Redis

from core.lib.base.cache_provider import CacheProvider

T = TypeVar('T')


class RedisProvider(CacheProvider):
    """
    Redis-backed implementation of CacheProvider.
    Receives an already-connected aioredis client; does NOT own the connection lifecycle.
    """

    def __init__(self, client: Redis, prefix: str = "cache") -> None:
        self._client = client
        self._prefix = prefix

    def _key(self, name: str) -> str:
        return f"{self._prefix}:{name}"

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        await self._client.setex(
            self._key(key),
            ttl,
            json.dumps(value, default=str),
        )

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._client.get(self._key(key))
        if raw is not None:
            return json.loads(raw)
        return None

    async def delete(self, key: str) -> None:
        await self._client.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        return (await self._client.exists(self._key(key))) > 0

    async def clear(self) -> None:
        await self._client.flushdb()

    async def remember(
        self,
        key: str,
        ttl: int,
        callback: Callable[[], Union[T, Awaitable[T]]],
    ) -> T:
        cached = await self.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        result = (
            await callback()
            if asyncio.iscoroutinefunction(callback)
            else callback()
        )
        await self.set(key, result, ttl)
        return result  # type: ignore[return-value]

    async def flush_pattern(self, pattern: str) -> int:
        cursor: int = 0
        deleted: int = 0
        full_pattern = self._key(pattern)
        while True:
            cursor, keys = await self._client.scan(
                cursor,
                match=full_pattern,
                count=100,
            )
            if keys:
                deleted += await self._client.delete(*keys)
            if cursor == 0:
                break
        return deleted