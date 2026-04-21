# Global Cache Architecture

The application implements a decoupled, plugin-based caching system. This ensures that the core logic remains independent of the specific cache driver (Redis, Memcached, etc.).

## Core Components

- **`CacheProvider`** (`core/lib/base/cache_provider.py`): Abstract base class defining the standard interface (`get`, `set`, `delete`).
- **`app.state.CACHE`**: The global storage location for the active `CacheProvider` instance.
- **`get_cache`** (`core/lib/dependencies/cache.py`): A FastAPI dependency used to retrieve the active provider.

---

## Redis Plugin Implementation

The Redis plugin (`plugins/redis/redis.py`) is responsible for bootstrapping the cache and attaching it to the application state.

### Initialization Flow

1. **Detection**: During startup, the `RedisBridge` plugin checks the `CACHE_DRIVER` environment variable.
2. **Bootstrapping**: It uses `fastapi_plugins.redis_plugin` to initialize the connection.
3. **Provider Wrapping**: It wraps the raw Redis client in a `RedisProvider` instance.
4. **State Reassignment**: It reassigns the `app.state.CACHE` object:

```python
# plugins/redis/redis.py

async def init(self) -> None:
    ...
    await redis_plugin.init_app(self.app, config=config)
    await redis_plugin.init()

    from .includes.provider import RedisProvider

    self.app.state.CACHE = RedisProvider(
        client=redis_plugin.redis,
        prefix="cache",
    )
```

### Why `app.state.CACHE`?
Storing the provider in `app.state.CACHE` allows any part of the application (API routes, templates, or background services) to access the cache simply by having a reference to the `app` object or through the `get_cache` dependency.

---

## Usage in Dependencies

To use the cache in a route, use the `CacheDep` annotation:

```python
from core.lib.dependencies.cache import CacheDep

@router.get("/data")
async def get_data(cache: CacheDep):
    value = await cache.get("my_key")
    return {"data": value}
```

> [!IMPORTANT]
> If no cache plugin is active or correctly configured, the `get_cache` dependency will raise a `RuntimeError` at runtime to prevent silent failures.
