from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_async_db
from core.lib.decorators.cache import cached
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.permissions.models import Permission
from src.modules.permissions.schemas import (
    RQPermission, 
    RQCreatePermission,
    RQBulkPermissions,
    RSPermission, 
    RSPermissionList,
    RSBulkPermissionsResponse
)
from src.modules.permissions.services import create_permission, create_bulk_permissions_with_roles
from src.modules.permissions.meta.models import MetaPermissions
from src.modules.role_permissions.models import RolePermission
from src.modules.auth.services import decode_token


class PermissionsController(Controller):
    """
    Controller for Permissions management.
    
    Path: /api/v1/permissions
    """

    @Get("/id/{id}", response_model=RSPermission, status_code=200)
    async def get_Permission(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> RSPermission:
        try:
            result: Permission = await Permission.find_one(db, id)
            return RSPermission(
                uid=result.uid,
                id=result.id,
                action=result.action,
                description=result.description,
                name=result.name,
                type=result.type,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSPermissionList, status_code=200)
    async def get_Permissions(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSPermissionList:
        try:
            result = await Permission.find_some(db,  pag or 1, ord, status)
            result2 = list(map(
                lambda x: RSPermission(
                    uid=x.uid,
                    id=x.id,
                    action=x.action,
                    description=x.description,
                    name=x.name,
                    type=x.type,
                ),
                result,
            ))
            return RSPermissionList(
                data=result2,
                total=0,
                page=0,
                page_size=0,
                total_pages=0,
                has_next=False,
                has_prev=False,
                next_page=0,
                prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/all", response_model=RSPermissionList, status_code=200)
    @cached(ttl=60)
    async def get_all_Permissions(
        self,
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSPermissionList:
        try:
            result = await Permission.find_all(db, status)
            result2 = list(map(
                lambda x: RSPermission(
                    uid=x.uid,
                    id=x.id,
                    action=x.action,
                    description=x.description,
                    name=x.name,
                    type=x.type,
                ),
                result,
            ))
            return RSPermissionList(
                data=result2,
                total=len(result),
                page=0,
                page_size=0,
                total_pages=0,
                has_next=False,
                has_prev=False,
                next_page=0,
                prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSPermission, status_code=201)
    async def create_Permission(
        self, permission: RQPermission, db: AsyncSession = Depends(get_async_db)
    ) -> RSPermission:
        try:
            result = await Permission(**permission.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_Permission(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Permission.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSPermission, status_code=200)
    async def update_Permission(
        self, id: str, permission: RQPermission, db: AsyncSession = Depends(get_async_db)
    ) -> RSPermission:
        try:
            result = await Permission.update(db, id, permission.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e

    @Post("/bulk", response_model=RSBulkPermissionsResponse, status_code=201)
    async def create_bulk_permissions(
        self,
        bulk_data: RQBulkPermissions, 
        db: AsyncSession = Depends(get_async_db)
    ) -> RSBulkPermissionsResponse:
        """
        Crea múltiples permisos en bulk y los asigna a sus roles correspondientes.
        """
        try:
            results, success_count, error_count = await create_bulk_permissions_with_roles(
                db=db,
                permissions_data=bulk_data.permissions
            )
            
            return RSBulkPermissionsResponse(
                created=results,
                total=len(bulk_data.permissions),
                success_count=success_count,
                error_count=error_count
            )
        except Exception as e:
            print(f"Error in create_bulk_permissions endpoint: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al crear permisos en bulk: {str(e)}"
            )

    @Post("/resolve", response_model=list[RSPermission])
    async def resolve_permissions(
        self,
        permission_ids: list[int],
        db: AsyncSession = Depends(get_async_db)
    ) -> list[RSPermission]:
        """
        Resolve a list of permission IDs to their full objects including metadata.
        """
        if not permission_ids:
            return []

        # 1. Fetch permissions
        query = select(Permission).where(Permission.id.in_(permission_ids))
        result = await db.execute(query)
        permissions = result.scalars().all()

        # 2. Fetch metadata for these permissions
        meta_query = select(MetaPermissions).where(MetaPermissions.ref_permission.in_(permission_ids))
        meta_result = await db.execute(meta_query)
        meta_rows = meta_result.scalars().all()

        # 3. Group metadata by permission ID
        meta_by_perm: dict[int, dict[str, str]] = {}
        for meta in meta_rows:
            if meta.ref_permission not in meta_by_perm:
                meta_by_perm[meta.ref_permission] = {}
            meta_by_perm[meta.ref_permission][meta.key] = meta.value

        # 4. Construct response
        response_list = []
        for perm in permissions:
            response_list.append(RSPermission(
                id=perm.id,
                uid=perm.uid,
                type=perm.type,
                name=perm.name,
                action=perm.action,
                description=perm.description,
                meta=meta_by_perm.get(perm.id, {})
            ))

        return response_list

    @Get("/check/{id}", response_model=bool)
    async def check_permission(
        self,
        id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db)
    ) -> bool:
        """
        Check if the current user has a specific permission ID.
        Reads user role from HttpOnly cookie.
        """
        # 1. Extract role from cookie
        access_token = request.cookies.get("access_token")
        role_id = None
        
        if access_token:
            try:
                payload = decode_token(access_token)
                if payload and payload.role:
                    role_id = payload.role
            except Exception:
                pass

        if not role_id:
            return False

        # 2. Check RolePermission pivot
        query = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == id
        )
        result = await db.execute(query)
        has_permission = result.scalar_one_or_none()
        
        return has_permission is not None
