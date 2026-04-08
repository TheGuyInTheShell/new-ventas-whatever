"""
Controller de ejemplo para el módulo de health check.

Este módulo demuestra el uso del auto-registro de rutas API.
Proporciona endpoints básicos de verificación de estado del servidor.

Estructura de directorios → Ruta HTTP:
    src/api/health/controller.py → /api/v1/health
"""

from typing import Any, Dict

from core.lib.decorators import Post, Get, Services
from core.lib.register import Controller
from src.modules.options.services import OptionsService
from src.modules.options.schemas import Option

@Services(OptionsService)
class OptionsController(Controller):
    """Controller de options para verificar el estado del options.

    Endpoints:
        POST /            → Crear options
        GET /            → Obtener options
    """

    OptionsService: "OptionsService"

    @Post("/")
    async def create_option(self, name: str, context: str, value: str) -> Option:
        """Retorna el estado general del servidor.

        Returns:
            Diccionario con el estado del servidor y metadata básica.
        """
        return await self.OptionsService.create_options(name, context, value)

    @Get("/")
    async def get_options(self) -> Dict[str, str]:
        """Endpoint simple de ping para verificar conectividad.

        Returns:
            Diccionario con respuesta pong.
        """
        return {
            "ping": "pong",
        }