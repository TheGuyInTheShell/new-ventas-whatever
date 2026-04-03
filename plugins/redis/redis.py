import os
import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI
from fastapi_plugins import redis_plugin

from core.lib.register.plugin import Plugin
from .settings import config


class RedisBridge(Plugin):
    """
    Bridge plugin linking our core architecture with `fastapi-plugins` redis.
    On init it:
      1. Boots the underlying redis_plugin connection.
      2. Wraps the raw client in a RedisProvider.
      3. Stores it on `app.state.CACHE` so the rest of the app can use it.
    """

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.is_active: bool = (
            os.environ.get("CACHE_DRIVER", "REDIS").upper() == "REDIS"
        )

    async def init(self) -> None:
        if not self.is_active:
            print("ℹ️ Cache driver is not REDIS. Skipping Redis initialization.")
            return

        await redis_plugin.init_app(self.app, config=config)
        try:
            await redis_plugin.init()

            # Late import to avoid circular references at module load time
            from .includes.privider import RedisProvider

            self.app.state.CACHE = RedisProvider(
                client=redis_plugin.redis,
                prefix="cache",
            )
            print("✅ Redis CacheProvider registered on app.state.CACHE")
        except Exception as e:
            print(f"⚠️ Redis Plugin failed to initialize (server might be offline): {e}")

    async def terminate(self) -> None:
        if not self.is_active:
            return

        try:
            await redis_plugin.terminate()
        except Exception as e:
            print(f"⚠️ Redis Plugin failed to terminate gracefully: {e}")
