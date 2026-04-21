from typing import Optional, Any

from core.lib.decorators import Services
from src.modules.permissions.services import PermissionsService
from src.modules.auth.services import AuthService
from core.security.shield.provider import ResolverProvider
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from src.modules.options.services import OptionsService
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

            auth_header = request.cookies.get("access_token")
            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            payload = self.AuthService.decode_token(auth_header)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            if payload.type != "access":
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
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            has_permission = await self.PermissionsService.check_role_has_permission(
                int(payload.role), permission.id
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            return True
        except HTTPException as he:
            if he.status_code == 302:
                raise he
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail="Invalid request",
                headers={"Location": "/sign/in"},
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail="Invalid request",
                headers={"Location": "/sign/in"},
            )


@Services(OptionsService)
class SysInitShield(ResolverProvider):

    OptionsService: OptionsService

    async def resolve(
        self,
        name: str,
        type_str: str,
        action: str,
        context: str,
        request: Request,
        **kwargs,
    ) -> bool:

        if settings.MODE == "DEVELOPMENT":
            return True

        # If the system is ALREADY initialized
        # We redirect to /sign/in to prevent accessing init again
        is_ready = await self.OptionsService.get_option(
            "system_init", "owner_signup", "ready"
        )

        if is_ready:
            headers = {"Location": "/sign/in"}
            if request.headers.get("hx-request"):
                headers["HX-Redirect"] = "/sign/in"

            raise HTTPException(status_code=303, headers=headers)

        return True
