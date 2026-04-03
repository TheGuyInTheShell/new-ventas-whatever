from fastapi_plugins import RedisSettings
import os

class AppRedisSettings(RedisSettings):
    """
    Redis settings configuration.
    Inherits from fastapi_plugins RedisSettings to seamlessly integrate.
    Variables like REDIS_HOST, REDIS_PORT can be loaded from the environment securely.
    """
    redis_prestart_tries: int = 1
    redis_prestart_wait: int = 1
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

config = AppRedisSettings()
