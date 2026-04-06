from core.lib.register.websocket import WebSocket
from core.lib.decorators.ws import Sio
from core.lib.decorators.events import Channel


class LiveEvents(WebSocket):

    @Sio.on("connect")
    async def on_connect(self, sid, environ, auth):
        await self.sio.emit(
            event="connect_info",
            data={"message": "Connection successful!", "status": "ready"},
            room=sid,
            namespace=self.namespace,
        )

    @Channel.subscribe_to("test:event")
    async def test(self, msg):

        print(msg)

        await self.sio.emit("test:event", msg, namespace=self.namespace)
