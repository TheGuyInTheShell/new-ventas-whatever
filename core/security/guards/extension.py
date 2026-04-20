from core.lib.register.extension import Extension
from fastapi import FastAPI
from guard.middleware import SecurityMiddleware


class FastAPI_Guard(Extension):
    def __init__(self, app: FastAPI):
        self.app = app

    def extends(self):
        from .settings import config

        self.app.add_middleware(SecurityMiddleware, config=config)
