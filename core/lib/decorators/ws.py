from core.events import ChannelEvent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socketio import AsyncServer


class SocketIO:

    sio: "AsyncServer"
    namespace: str

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        pass

    def on(self, event: str):
        def decorator(func):
            func.__ws_event__ = event
            return func
        return decorator


def init_sio_decorator(sio: "AsyncServer", namespace: str):
    instance = SocketIO()
    instance.sio = sio
    instance.namespace = namespace
    return instance



Sio = SocketIO()