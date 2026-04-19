from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service

from ..permissions.models import Permission
from .models import Role
from .schemas import RQRole, RSRole
from ..role_permissions.models import RolePermission

class RolesService(Service):
    async def create_role(self, db: AsyncSession, rq_role: RQRole) -> RSRole:
        try:

            role = await Role(**rq_role.model_dump()).save(db)

            return RSRole(
                id=role.id,
                uid=role.uid,
                name=role.name,
                description=role.description,
                level=role.level
            )

        except Exception as e:
            raise e

