import os
import dotenv
dotenv.load_dotenv()
from fastapi import FastAPI, Depends
from fastapi_plugins import redis_plugin, depends_redis

from core.lib.register.plugin import Plugin
from .settings import config
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from aioredis import Redis




class RedisBridge(Plugin):
    """
    Bridge plugin linking our core architecture with `fastapi-plugins` internal redis implementation.
    Automatically manages redis initialization and teardown dynamically based on environment configuration.
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.is_active = os.environ.get("CACHE_DRIVER", "MEMCACHED").upper() == "REDIS"

    async def init(self) -> None:
        """
        Asynchronously load the library's App instance and its internal initialization routines.
        """
        if not self.is_active:
            print("ℹ️ Cache driver is not REDIS. Skipping Redis initialization.")
            return

        await redis_plugin.init_app(self.app, config=config)
        try:
            await redis_plugin.init()
            
            @self.app.get("/redis")
            async def root_get(
                    cache: 'Redis'=Depends(depends_redis),
            ) -> Dict:
                await cache.set("test", "test")
                return dict(ping=await cache.ping())
            
        except Exception as e:
            print(f"⚠️ Redis Plugin failed to initialize (server might be offline): {e}")

    async def terminate(self) -> None:
        """
        Asynchronously unmount the cache to drain connections neatly.
        """
        if not self.is_active:
            return

        try:
            await redis_plugin.terminate()
        except Exception as e:
            print(f"⚠️ Redis Plugin failed to terminate gracefully: {e}")
