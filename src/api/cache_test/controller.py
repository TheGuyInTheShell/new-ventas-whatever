"""
Controller de ejemplo para probar la funcionalidad de caché.

Estructura de directorios → Ruta HTTP:
    src/api/cache_test/controller.py → /api/v1/cache_test
"""

from typing import Dict, Any
from fastapi import Request

from core.lib.decorators import Get
from core.lib.register import Controller
from core.lib.decorators.cache import cached
from core.lib.dependencies.cache import CacheDep
from core.security.shield import Shield
from src.api.health.shields import HealthShieldResolver


@Shield.register(context="CacheTestModule")
class CacheTestController(Controller):
    """Controller para pruebas experimentales del proveedor de caché global."""

    @Get("/manual")
    async def test_manual_cache(self, cache: CacheDep) -> Dict[str, Any]:
        """Prueba inyección de caché manual.

        Genera un número aleatorio y lo almacena por 60 segundos si es nuevo.
        """
        import random

        async def fetch_random_number():
            return random.randint(1000, 9999)

        value = await cache.remember("test_manual_random", 60, fetch_random_number)

        return {"status": "success", "message": "Manual cache test", "value": value}

    @Get("/decorator")
    @Shield.need(
        name="version",
        action="read",
        type="endpoint",
        description="Endpoint de diagnóstico - leer versión",
        resolver=HealthShieldResolver(),
    )
    @cached(ttl=60, prefix="test_decorator")
    async def test_decorator_cache(self) -> Dict[str, Any]:
        """Prueba de caché a través del decorador global.

        Debe cachear este JSON serializable entero y retornarlo sin recalculación en los próximos 60s.
        """
        import random

        return {
            "status": "success",
            "message": "Decorator cache test",
            "random": random.randint(1000, 9999),
        }

    @Get("/clear")
    async def clear_cache(self, cache: CacheDep) -> Dict[str, str]:
        """Flush DB cache (Prueba de purgado)."""
        await cache.clear()
        return {"status": "Cache was fully flushed!"}
