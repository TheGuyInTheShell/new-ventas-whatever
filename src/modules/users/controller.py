from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from src.modules.auth.services import decode_token, create_token, TokenData

from .models import User
from .schemas import RSUserTokenData
from src.modules.permissions.schemas import RSPermission, RSUserMe
from src.modules.role_permissions.models import RolePermission
from src.modules.permissions.models import Permission
from src.modules.permissions.meta.models import MetaPermissions
from src.modules.roles.models import Role
from sqlalchemy import select

# prefix /users
router = APIRouter()

tag = "users"


@router.get("/me", response_model=RSUserMe, tags=[tag])
async def current_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get current user profile with hierarchical menu tree and permissions.
    Reads JWT from HttpOnly access_token cookie (Security-First).
    """
    # 1. Extract JWT from cookie
    access_token = request.cookies.get("access_token")
    payload: TokenData | None = None

    if access_token:
        payload = decode_token(access_token)

    # If access token invalid/expired, try refresh
    if not payload:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            refresh_payload = decode_token(refresh_token)
            if refresh_payload and refresh_payload.type == "refresh":
                payload = refresh_payload
                # Issue new access token
                new_access_token = create_token(
                    data={
                        "sub": payload.sub,
                        "email": payload.email,
                        "role": payload.role,
                        "full_name": payload.full_name,
                        "id": payload.id,
                        "uid": payload.uid,
                    }
                )
                response.set_cookie(
                    key="access_token",
                    value=new_access_token,
                    httponly=True,
                    samesite="lax",
                )

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Get role name and permissions with meta for this role
    role_id = payload.role
    role_name = "unknown"
    permissions = []

    if role_id:
        # Get role name
        role_res = await db.execute(select(Role.name).where(Role.id == role_id))
        role_name = role_res.scalar_one_or_none() or "unknown"
        # Get permission IDs for role
        rp_result = await db.execute(
            select(RolePermission.permission_id).where(
                RolePermission.role_id == role_id
            )
        )
        permission_ids = [row[0] for row in rp_result.all()]

        if permission_ids:
            # Get permissions
            perm_result = await db.execute(
                select(Permission).where(Permission.id.in_(permission_ids))
            )
            perms = perm_result.scalars().all()

            # Get meta for these permissions
            meta_result = await db.execute(
                select(MetaPermissions).where(
                    MetaPermissions.ref_permission.in_(permission_ids)
                )
            )
            metas = meta_result.scalars().all()
            
            # Group meta
            meta_by_perm: dict[int, dict[str, Any]] = {}
            for m in metas:
                if m.ref_permission not in meta_by_perm:
                    meta_by_perm[m.ref_permission] = {}
                meta_by_perm[m.ref_permission][m.key] = m.value

            # Build response list
            for p in perms:
                permissions.append(RSPermission(
                    id=p.id,
                    uid=p.uid,
                    type=p.type,
                    name=p.name,
                    action=p.action,
                    description=p.description,
                    meta=meta_by_perm.get(p.id, {})
                ))

    # 3. Return full user profile + permissions
    return RSUserMe(
        id=payload.id or 0,
        uid=payload.uid or "",
        username=payload.sub or "",
        email=payload.email or "",
        full_name=payload.full_name or "",
        role=payload.role or 0,
        role_name=role_name,
        otp_enabled=payload.otp_enabled,
        permissions=permissions,
    )


@router.get("", tags=[tag])
async def get_users(db: AsyncSession = Depends(get_async_db)):
    try:
        result = await User.find_some(db, status="exists")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

