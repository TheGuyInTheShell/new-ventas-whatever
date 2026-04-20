from .settings import config
from guard import SecurityDecorator
from .extension import FastAPI_Guard

guard = SecurityDecorator(config)

__all__ = ["guard", "FastAPI_Guard"]
