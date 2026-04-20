from typing import Optional, Any

from core.lib.decorators import Services
from src.modules.permissions.services import PermissionsService
from src.modules.auth.services import AuthService
from core.security.shield.provider import ResolverProvider
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from core.config.settings import settings


@Services(PermissionsService, AuthService)
class AuthShieldApi(ResolverProvider):
    PermissionsService: PermissionsService
    AuthService: AuthService

    async def resolve(
        self,
        name: str,
        type_str: str,
        action: str,
        context: str,
        request: Optional[Request] = None,
        **kwargs: Any,
    ):
        try:
            if settings.MODE == "DEVELOPMENT":
                return True

            if not request:
                raise HTTPException(
                    status_code=401, detail="Request context is missing"
                )

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid token")

            token = auth_header.split(" ")[1]
            payload = self.AuthService.decode_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")

            if payload.type not in ["access", "refresh"]:
                raise HTTPException(status_code=401, detail="Invalid token type")

            if not payload.role:
                raise HTTPException(status_code=403, detail="Role not defined in token")

            permission = await self.PermissionsService.get_permission(
                name, context, action, type_str
            )
            if not permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"No tienes el permiso requerido: {name} (acción: {action})",
                )

            has_permission = await self.PermissionsService.check_role_has_permission(
                int(payload.role), permission.id
            )
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"No tienes el permiso requerido: {name} (acción: {action})",
                )

            return True
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=403, detail=str(e))


@Services(PermissionsService, AuthService)
class AuthShieldApp(ResolverProvider):
    PermissionsService: PermissionsService
    AuthService: AuthService

    async def resolve(
        self,
        name: str,
        type_str: str,
        action: str,
        context: str,
        request: Optional[Request] = None,
        **kwargs: Any,
    ):
        try:
            if settings.MODE == "DEVELOPMENT":
                return True
            # redirect to login page
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            token = auth_header.split(" ")[1]
            payload = self.AuthService.decode_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            if payload.type not in ["access", "refresh"]:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            if not payload.role:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            permission = await self.PermissionsService.get_permission(
                name, context, action, type_str
            )
            if not permission:
                raise HTTPException(
                    status_code=401,
                    detail=f"No tienes el permiso requerido: {name} (acción: {action})",
                )

            has_permission = await self.PermissionsService.check_role_has_permission(
                int(payload.role), permission.id
            )
            if not has_permission:
                raise HTTPException(
                    status_code=401,
                    detail=f"No tienes el permiso requerido: {name} (acción: {action})",
                )

            return True
        except HTTPException as he:
            if he.status_code == 302:
                raise he
            raise HTTPException(status_code=401, detail=str(he.detail))
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
