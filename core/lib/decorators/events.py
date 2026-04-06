from core.events import ChannelEvent


class Channel:

    @classmethod
    def subscribe_to(cls, event: str):
        def decorator(func):
            ChannelEvent().subscribe_to(event, func)
        return decorator