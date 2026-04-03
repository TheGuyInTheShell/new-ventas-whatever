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

    async def init(self) -> None:
        """
        Asynchronously load the library's App instance and its internal initialization routines.
        """
        await memcached_plugin.init_app(self.app, config=config)
        try:
            await memcached_plugin.init()
        except Exception as e:
            print(f"⚠️ Memcached Plugin failed to initialize (server might be offline): {e}")

    async def terminate(self) -> None:
        """
        Asynchronously unmount the cache to drain connections neatly.
        """
        try:
            await memcached_plugin.terminate()
        except Exception as e:
            print(f"⚠️ Memcached Plugin failed to terminate beautifully: {e}")
