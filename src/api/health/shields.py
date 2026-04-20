from typing import Any
from fastapi import HTTPException, Request
from core.security.shield.provider import ResolverProvider, BasicResolverProvider


class HealthShieldResolver(ResolverProvider):
    def resolve(
        self, name: str, type_str: str, action: str, context: str, **kwargs: Any
    ) -> bool:
        if name == "health:read":
            print(
                f"✅ [SHIELD-DEMO] Permitiendo acceso al permiso: '{name}' con action '{action}' y type '{type_str}' y context '{context}'"
            )
            return True
        elif name == "health:ping":
            print(
                f"❌ [SHIELD-DEMO] Denegando acceso al permiso: '{name}' con action '{action}' y type '{type_str}' y context '{context}'. Retornando HTTP 401"
            )
            raise HTTPException(
                status_code=401,
                detail="Unauthorized - Requiere autenticación (Demo Shield Guard)",
            )

        # Comportamiento por defecto
        print(
            f"✅ [SHIELD-DEMO] Permitiendo acceso por defecto al permiso: '{name}' con action '{action}' y type '{type_str}' y context '{context}'"
        )
        return True


class HealthBasicResolver(BasicResolverProvider):
    def resolve(self, request: Request) -> bool:
        # Comportamiento por defecto
        print(f"✅ [SHIELD-DEMO] Permitiendo acceso por defecto al permiso")
        return True


# Instalación temporal del resolver global a nivel de este archivo para la demo
