from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core import cache

from .models import Permission
from .schemas import (
    RQPermission, 
    RQCreatePermission,
    RQBulkPermissions,
    RSPermission, 
    RSPermissionList,
    RSBulkPermissionsResponse
)
from .services import create_permission, create_bulk_permissions_with_roles
from app.modules.permissions.meta.models import MetaPermissions
from sqlalchemy import select
from app.modules.role_permissions.models import RolePermission
from app.modules.auth.services import decode_token

# prefix /permissions
router = APIRouter()

tag = "permissions"


@router.get("/id/{id}", response_model=RSPermission, status_code=200, tags=[tag])
async def get_Permission(
    id: str, db: AsyncSession = Depends(get_async_db)
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


@router.get("/", response_model=RSPermissionList, status_code=200, tags=[tag])
async def get_Permissions(
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


@router.get("/all", response_model=RSPermissionList, status_code=200, tags=[tag])
@cache.cache_endpoint(ttl=60, namespace="permissions")
async def get_all_Permissions(
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


@router.post("/", response_model=RSPermission, status_code=201, tags=[tag])
async def create_Permission(
    permission: RQPermission, db: AsyncSession = Depends(get_async_db)
) -> RSPermission:
    try:
        result = await Permission(**permission.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_Permission(id: str, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await Permission.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSPermission, status_code=200, tags=[tag])
async def update_Permission(
    id: str, permission: RQPermission, db: AsyncSession = Depends(get_async_db)
) -> RSPermission:
    try:
        result = await Permission.update(db, id, permission.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e


@router.post("/bulk", response_model=RSBulkPermissionsResponse, status_code=201, tags=[tag])
async def create_bulk_permissions(
    bulk_data: RQBulkPermissions, 
    db: AsyncSession = Depends(get_async_db)
) -> RSBulkPermissionsResponse:
    """
    Crea múltiples permisos en bulk y los asigna a sus roles correspondientes.
    
    Args:
        bulk_data: Datos de los permisos a crear con sus roles asociados
        db: Sesión de base de datos
        
    Returns:
        RSBulkPermissionsResponse: Resultado de la creación en bulk
        
    Example:
        ```json
        {
            "permissions": [
                {
                    "name": "create_user",
                    "action": "POST",
                    "description": "/api/users",
                    "type": "api",
                    "role_id": "uuid-del-rol"
                },
                {
                    "name": "delete_user",
                    "action": "DELETE",
                    "description": "/api/users/{id}",
                    "type": "api",
                    "role_id": "uuid-del-rol"
                }
            ]
        }
        ```
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


@router.post("/resolve", response_model=list[RSPermission], tags=[tag])
async def resolve_permissions(
    permission_ids: list[int],
    db: AsyncSession = Depends(get_async_db)
) -> list[RSPermission]:
    """
    Resolve a list of permission IDs to their full objects including metadata.
    Used by frontend to lazy-load submenus or detailed permission info.
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


@router.get("/check/{id}", response_model=bool, tags=[tag])
async def check_permission(
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
        # Try refresh logic effectively skipped for simple check, 
        # but could be added if critical. For now, strict check.
        return False

    # 2. Check RolePermission pivot
    # Requires importing RolePermission (ensure it's imported)
    query = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == id
    )
    result = await db.execute(query)
    has_permission = result.scalar_one_or_none()
    
    return has_permission is not None
