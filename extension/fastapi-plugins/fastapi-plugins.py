from core.lib.register.extension import Extension
from fastapi import FastAPI
import fastapi_plugins



class FastAPIPlugins(Extension):
    def __init__(self, app: FastAPI):
        self.app = app

    def extends(self):
        self.app = fastapi_plugins.register_middleware(self.app)
