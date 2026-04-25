from typing import List
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from core.lib.register.service import Service

from ..roles.models import Role
from ..permissions.models import Permission
from .models import RolePermission
from .schemas import RSPermissionDetail, RSRolePermissions

class RolePermissionsService(Service):
    @injectable
    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> Role:
        """
        Assigns a permission to a role via the RolePermission pivot table.
        """
        # Get the role
        role = await Role.find_one(db, role_id)

        # Get the permission to verify it exists
        permission = await Permission.find_one(db, permission_id)

        # No longer updating role.permissions array (redundancy removed)

        # Sync Pivot Table (RolePermission)
        rp_query = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id
            )
        )
        if not rp_query.scalar_one_or_none():
            await RolePermission(
                role_id=role.id,
                permission_id=permission.id
            ).save(db)

        return role

    @injectable
    async def remove_permission_from_role(
        self,
        role_id: int,
        permission_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> Role:
        """
        Removes a permission from a role by deleting the entry from the RolePermission pivot table.
        """
        # Get the role
        role = await Role.find_one(db, role_id)

        # No longer updating role.permissions array (redundancy removed)

        # Remove from Pivot Table (RolePermission)
        await db.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission_id
            )
        )
        await db.commit()

        return role

    @injectable
    async def get_role_permissions(self, role_id: int, db: AsyncSession = Depends(get_async_db)) -> RSRolePermissions:
        """
        Gets all permissions for a role, returning full Permission objects.
        """
        # Get the role
        role = await Role.find_one(db, role_id)

        # Get all permissions for this role from the Pivot Table
        query = await db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        permission_objs = query.scalars().all()

        permissions = [
            RSPermissionDetail(
                id=perm.id,
                name=perm.name,
                action=perm.action,
                description=perm.description,
                type=perm.type,
            )
            for perm in permission_objs
        ]

        return RSRolePermissions(
            role_id=role.id, role_name=role.name, permissions=permissions
        )

