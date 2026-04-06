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


class HealthController(Controller):
    """Controller de health check para verificar el estado del servidor.

    Endpoints:
        GET /            → Estado general del servidor
        GET /ping        → Respuesta simple de ping/pong
        GET /version     → Información de versión de la API
    """

    @Get("/")
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
    async def version(self) -> Dict[str, str]:
        """Retorna la versión actual de la API.

        Returns:
            Diccionario con información de versión.
        """
        return {
            "api_version": "v1",
            "app_version": "0.1.0",
        }
