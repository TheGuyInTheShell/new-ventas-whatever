from typing import Optional, Any

from core.lib.decorators import Services
from src.modules.permissions.services import PermissionsService
from src.modules.auth.services import AuthService
from core.security.shield.provider import ResolverProvider, BasicResolverProvider
from fastapi import HTTPException, Request, status
from core.lib.dependencies.cache import get_cache
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
            print(
                f"[AuthShieldApi] resolve: name={name} type_str={type_str} action={action} context={context}"
            )
            if not request:
                raise HTTPException(
                    status_code=401, detail="Request context is missing"
                )

            auth_source = request.headers.get("Authorization") or request.cookies.get(
                "access_token"
            )
            if not auth_source:
                raise HTTPException(status_code=401, detail="Missing or invalid token")

            token = (
                auth_source.split(" ")[1]
                if auth_source.lower().startswith("bearer ")
                else auth_source
            )
            payload = self.AuthService.decode_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")

            if payload.type != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
            if not payload.role:
                raise HTTPException(status_code=403, detail="Role not defined in token")

            permission_cache_key = f"shield:perm:{context}:{type_str}:{action}:{name}"
            cache = await get_cache(request)
            perm_id = await cache.get(permission_cache_key)

            if perm_id is None:
                permission = await self.PermissionsService.get_permission(
                    name, context, action, type_str
                )
                if not permission:
                    raise HTTPException(
                        status_code=403,
                        detail=f"No tienes el permiso requerido: {name} (acción: {action})",
                    )
                perm_id = permission.id
                await cache.set(permission_cache_key, perm_id, 3600)  # 1 hour

            access_cache_key = f"shield:access:{payload.role}:{perm_id}"
            has_permission = await cache.get(access_cache_key)

            if has_permission is None:
                has_permission = (
                    await self.PermissionsService.check_role_has_permission(
                        int(payload.role), perm_id
                    )
                )
                await cache.set(access_cache_key, has_permission, 600)  # 10 minutes

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
            if not payload or payload.type != "access" or not payload.role:
                raise HTTPException(
                    status_code=status.HTTP_302_FOUND,
                    detail="Invalid request",
                    headers={"Location": "/sign/in"},
                )

            permission_cache_key = f"shield:perm:{context}:{type_str}:{action}:{name}"
            cache = await get_cache(request)
            perm_id = await cache.get(permission_cache_key)

            if perm_id is None:
                permission = await self.PermissionsService.get_permission(
                    name, context, action, type_str
                )

                if not permission:
                    raise HTTPException(
                        status_code=status.HTTP_302_FOUND,
                        detail="Invalid request",
                        headers={"Location": "/sign/in"},
                    )
                perm_id = permission.id
                await cache.set(permission_cache_key, perm_id, 3600)  # 1 hour

            access_cache_key = f"shield:access:{payload.role}:{perm_id}"
            has_permission = await cache.get(access_cache_key)

            if has_permission is None:
                has_permission = (
                    await self.PermissionsService.check_role_has_permission(
                        int(payload.role), perm_id
                    )
                )
                await cache.set(access_cache_key, has_permission, 60)  # 1 minutes

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

        # Use caching for system initialization check
        cache = await get_cache(request)
        sys_init_key = "shield:sys_init:ready"
        is_ready = await cache.get(sys_init_key)

        if is_ready is None:
            is_ready = await self.OptionsService.get_option(
                "system_init", "owner_signup", "ready"
            )
            if is_ready:
                await cache.set(sys_init_key, True, 3600)  # Ready = 1 hour
            else:
                await cache.set(sys_init_key, False, 60)  # Not ready = 1 minute

        if is_ready:
            headers = {"Location": "/sign/in"}
            if request.headers.get("hx-request"):
                headers["HX-Redirect"] = "/sign/in"

            raise HTTPException(status_code=303, headers=headers)

        return True


class SignInShield(BasicResolverProvider):
    async def resolve(
        self,
        request: Request,
        **kwargs,
    ) -> bool:
        if settings.MODE == "DEVELOPMENT":
            return True

        auth_header = request.cookies.get("access_token")
        if auth_header:
            headers = {"Location": "/dashboard"}
            if request.headers.get("hx-request"):
                headers["HX-Redirect"] = "/dashboard"
            raise HTTPException(status_code=303, headers=headers)

        return True
