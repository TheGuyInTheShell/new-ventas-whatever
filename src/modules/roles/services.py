from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service

from fastapi_injectable import injectable
from core.database import get_async_db

from ..permissions.models import Permission
from .models import Role
from .schemas import RQRole, RSRole
from ..role_permissions.models import RolePermission

class RolesService(Service):
    @injectable
    async def create_role(self, rq_role: RQRole, db: AsyncSession = Depends(get_async_db)) -> RSRole:
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

    @injectable
    async def get_role_by_name(self, name: str, db: AsyncSession = Depends(get_async_db)) -> Role | None:
        try:
            result = await Role.find_by_colunm(db, "name", name)
            return result.scalar_one_or_none()
        except Exception as e:
            raise e

