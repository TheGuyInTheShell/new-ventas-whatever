"""
Controller de ejemplo para el módulo de health check.

Este módulo demuestra el uso del auto-registro de rutas API.
Proporciona endpoints básicos de verificación de estado del servidor.

Estructura de directorios → Ruta HTTP:
    src/api/health/controller.py → /api/v1/health
"""

from typing import Any, Dict

from core.lib.decorators import Get
from core.lib.register import Controller
from core.events import ChannelEvent
from core.security.shield import Shield
from core.lib.decorators.services import Services
from src.modules.example_permission.services import ExamplePermissionService
from .shields import HealthShieldResolver, HealthBasicResolver
from core.lib.decorators.cache import cached
from core.security.guards import guard


@Shield.register(context="HealthModule")
@Services(ExamplePermissionService)
class HealthController(Controller):
    """Controller de health check para verificar el estado del servidor.

    Endpoints:
        GET /            → Estado general del servidor
        GET /ping        → Respuesta simple de ping/pong
        GET /version     → Información de versión de la API
        GET /restricted  → Endpoint invocando un servicio con chequeos Shield
    """

    ExamplePermissionService: ExamplePermissionService

    @Get("/")
    @guard.rate_limit(requests=100, window=60)
    @Shield.need(
        name="health",
        action="read",
        type="endpoint",
        description="Permite solicitar el estado general del servidor.",
        resolver=HealthShieldResolver(),
    )
    async def health_check(self) -> Dict[str, Any]:
        """Retorna el estado general del servidor.

        Returns:
            Diccionario con el estado del servidor y metadata básica.
        """
        return {
            "status": "healthy",
            "service": "new-finance-app",
            "message": "Server is running correctly",
        }

    @Get("/ping")
    @Shield.need(
        name="ping",
        action="execute",
        type="endpoint",
        description="Permite enviar un ping general al servidor.",
        resolver=HealthShieldResolver(),
    )
    async def ping(self) -> Dict[str, str]:
        """Endpoint simple de ping para verificar conectividad.

        Returns:
            Diccionario con respuesta pong.
        """
        ChannelEvent().emit_to("test:event").run("test")
        return {
            "ping": "pong",
        }

    @Get("/version")
    @Shield.need(
        name="version",
        action="read",
        type="endpoint",
        description="Endpoint de diagnóstico - leer versión",
        resolver=HealthShieldResolver(),
    )
    @cached(ttl=60, prefix="health")
    async def version(self) -> Dict[str, str]:
        """Retorna la versión actual de la API.

        Returns:
            Diccionario con información de versión.
        """
        return {
            "api_version": "v1",
            "app_version": "0.1.0",
        }

    @Get("/restricted")
    @Shield.need(
        name="restricted",
        action="execute",
        type="endpoint",
        description="Llamada a test protegido que invoca comprobaciones imperativas.",
        resolver=HealthShieldResolver(),
    )
    async def restricted(self) -> Dict[str, Any]:
        """Llama a un servicio interno que hace una comprobación imperativa de Shield.

        Returns:
            Respuesta generada bajo la protección de un ResolverProvider abstracto.
        """
        return await self.ExamplePermissionService.perform_restricted_action()

    @Get("/test-basic-shield")
    @Shield.basic(resolver=HealthBasicResolver())
    async def test_basic_shield(self) -> Dict[str, str]:
        """Retorna la versión actual de la API.

        Returns:
            Diccionario con información de versión.
        """
        return {
            "api_version": "v1",
            "app_version": "0.1.0",
        }
