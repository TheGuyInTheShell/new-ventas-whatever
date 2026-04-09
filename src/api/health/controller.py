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
from fastapi import HTTPException
from core.security.shield.provider import ResolverProvider

class DemoGuardResolver(ResolverProvider):
    def resolve(self, name: str, type_str: str, action: str, context: str, **kwargs: Any) -> bool:
        if name == "health:read":
            print(f"✅ [SHIELD-DEMO] Permitiendo acceso al permiso: '{name}' con action '{action}' y type '{type_str}' y context '{context}'")
            return True
        elif name == "health:ping":
            print(f"❌ [SHIELD-DEMO] Denegando acceso al permiso: '{name}' con action '{action}' y type '{type_str}' y context '{context}'. Retornando HTTP 401")
            raise HTTPException(status_code=401, detail="Unauthorized - Requiere autenticación (Demo Shield Guard)")
        
        # Comportamiento por defecto
        print(f"✅ [SHIELD-DEMO] Permitiendo acceso por defecto al permiso: '{name}' con action '{action}' y type '{type_str}' y context '{context}'")
        return True

# Instalación temporal del resolver global a nivel de este archivo para la demo
Shield._global_resolver = DemoGuardResolver()


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
    @Shield.need(
        name="health:read",
        action="read",
        type="endpoint",
        description="Permite solicitar el estado general del servidor."
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
        name="health:ping",
        action="execute",
        type="endpoint",
        description="Permite enviar un ping general al servidor."
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
        name="health:version",
        action="read",
        type="endpoint",
        description="Endpoint de diagnóstico - leer versión"
    )
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
        name="health:restricted:view",
        action="view",
        type="endpoint",
        description="Llamada a test protegido que invoca comprobaciones imperativas."
    )
    async def restricted(self) -> Dict[str, Any]:
        """Llama a un servicio interno que hace una comprobación imperativa de Shield.
        
        Returns:
            Respuesta generada bajo la protección de un ResolverProvider abstracto.
        """
        return await self.ExamplePermissionService.perform_restricted_action()
