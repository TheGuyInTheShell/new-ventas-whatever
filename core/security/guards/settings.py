from guard import SecurityConfig
from guard import IPInfoManager


config = SecurityConfig(
    geo_ip_handler=IPInfoManager("a531a4633623a4"),
    enable_redis=False,
    auto_ban_threshold=10,
)
