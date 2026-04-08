from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List

from core.lib.register.service import Service

from ..roles.models import Role
from ..permissions.models import Permission
from .models import RolePermission
from .schemas import RSPermissionDetail, RSRolePermissions

class RolePermissionsService(Service):
    async def assign_permission_to_role(
        self,
        db: AsyncSession, role_id: int, permission_id: int
    ) -> Role:
        """
        Assigns a permission to a role by adding the permission UID to the role's permissions array.
        """
        # Get the role
        role = await Role.find_one(db, role_id)

        # Get the permission to verify it exists
        permission = await Permission.find_one(db, permission_id)

        # Add permission ID to role's permissions array if not already present
        if permission.id not in (role.permissions or []):
            updated_permissions = list(role.permissions or []) + [permission.id]
            await role.update(db, role_id, {"permissions": updated_permissions})

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

    async def remove_permission_from_role(
        self,
        db: AsyncSession, role_id: int, permission_id: int
    ) -> Role:
        """
        Removes a permission from a role by removing the permission UID from the role's permissions array.
        """
        # Get the role
        role = await Role.find_one(db, role_id)

        # Remove permission ID from role's permissions array if present
        if role.permissions and permission_id in role.permissions:
            updated_permissions = [p for p in role.permissions if p != permission_id]
            await role.update(db, role_id, {"permissions": updated_permissions})

        # Remove from Pivot Table (RolePermission)
        await db.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission_id
            )
        )
        await db.commit()

        return role

    async def get_role_permissions(self, db: AsyncSession, role_id: int) -> RSRolePermissions:
        """
        Gets all permissions for a role, returning full Permission objects.
        """
        # Get the role
        role = await Role.find_one(db, role_id)

        # Get all permissions for this role
        permissions = []
        for permission_id in (role.permissions or []):
            try:
                permission = await Permission.find_one(db, permission_id)
                permissions.append(
                    RSPermissionDetail(
                        id=permission.id,
                        name=permission.name,
                        action=permission.action,
                        description=permission.description,
                        type=permission.type,
                    )
                )
            except:
                # Skip permissions that no longer exist
                continue

        return RSRolePermissions(
            role_id=role.id, role_name=role.name, permissions=permissions
        )

