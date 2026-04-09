from core.lib.register.service import Service
from core.security.shield import Shield
from core.security.shield.provider import ResolverProvider
from fastapi_injectable import injectable

class ExampleResolverProvider(ResolverProvider):
    """
    Un Provider de ejemplo que asume que el usuario tiene permisos siempre.
    En un provider real, inyectarías la request o un token JWT y las reglas.
    """
    def resolve(self, name: str, type_str: str, context: str) -> bool:
        print(f"[Shield Simulation] Se ha verificado exitosamente el permiso '{name}' de tipo '{type_str}' para el contexto '{context}'")
        # Simula que si posee el permiso
        return True

class ExamplePermissionService(Service):
    """
    Servicio de prueba que demuestra el uso imperativo de Shield en partes internas 
    fuera del ecosistema de decoradores de fastapi.
    """
    
    @injectable
    async def perform_restricted_action(self) -> dict:
        """Una acción en el servicio que requiere permisos comprobados imperativamente."""
        provider = ExampleResolverProvider()
        
        def internal_action():
            return {
                "success": True,
                "message": "Se ejecutó la acción imperativa restringida con Shield",
                "shield_checked": True
            }

        # Ejecutamos con comprobación imperativa `Shield.use`
        return Shield.use(
            name="services:health:execute",
            type="service_action",
            context="ExamplePermissionService"
        )(provider, callback=internal_action)
