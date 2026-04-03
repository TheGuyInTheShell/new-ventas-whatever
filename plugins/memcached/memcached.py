import os
import dotenv
dotenv.load_dotenv()
from fastapi import FastAPI

from fastapi_plugins.memcached import memcached_plugin

from core.lib.register.plugin import Plugin
from .settings import config


class Memcached(Plugin):
    """
    Bridge plugin linking our core architecture with `fastapi-plugins[memcached]`.
    Automatically manages memcached initialization and teardown dynamically.
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.is_active = os.environ.get("CACHE_DRIVER", "MEMCACHED").upper() == "MEMCACHED"

    async def init(self) -> None:
        """
        Asynchronously load the library's App instance and its internal initialization routines.
        """
        if not self.is_active:
            print("ℹ️ Cache driver is not MEMCACHED. Skipping Memcached initialization.")
            return

        await memcached_plugin.init_app(self.app, config=config)

        try:
            await memcached_plugin.init()
        except Exception as e:
            print(f"⚠️ Memcached Plugin failed to initialize (server might be offline): {e}")

    async def terminate(self) -> None:
        """
        Asynchronously unmount the cache to drain connections neatly.
        """
        if not self.is_active:
            return

        try:
            await memcached_plugin.terminate()
        except Exception as e:
            print(f"⚠️ Memcached Plugin failed to terminate beautifully: {e}")
