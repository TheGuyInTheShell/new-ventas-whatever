from fastapi_plugins.memcached import MemcachedSettings

class AppMemcachedSettings(MemcachedSettings):
    """
    Memcached settings configuration.
    Inherits from fastapi_plugins MemcachedSettings to seamlessly integrate.
    Variables like MEMCACHED_HOST, MEMCACHED_PORT can be loaded from the environment securely.
    """
    memcached_prestart_tries: int = 1
    memcached_prestart_wait: int = 1

config = AppMemcachedSettings()
