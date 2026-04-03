from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union

T = TypeVar('T')


class CacheProvider(ABC):
    """
    Abstract base class for all cache providers.
    Any cache driver (Redis, Memcached, etc.) must implement this contract.
    """

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        ...

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...

    @abstractmethod
    async def remember(
        self,
        key: str,
        ttl: int,
        callback: Callable[[], Union[T, Awaitable[T]]],
    ) -> T:
        ...

    @abstractmethod
    async def flush_pattern(self, pattern: str) -> int:
        ...