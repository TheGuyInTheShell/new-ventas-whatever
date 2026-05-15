from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from core.lib.decorators.exceptions import handle_service_errors, ServiceResult

from fastapi_injectable import injectable
from core.database import get_async_db

from ..permissions.models import Permission
from .models import Role
from .schemas import RQRole, RSRole
from ..role_permissions.models import RolePermission


class RolesService(Service):
    @handle_service_errors
    @injectable
    async def create_role(
        self, rq_role: RQRole, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSRole]:
        role = await Role(**rq_role.model_dump()).save(db)

        return (
            RSRole(
                id=role.id,
                uid=role.uid,
                name=role.name,
                description=role.description,
                level=role.level,
            ),
            None,
        )

    @handle_service_errors
    @injectable
    async def get_role_by_name(
        self, name: str, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSRole]:
        result = await Role.find_by_colunm(db, "name", name)
        role = result.scalar_one_or_none()
        if not role:
            return None, None
        return (
            RSRole(
                id=role.id,
                uid=role.uid,
                name=role.name,
                description=role.description,
                level=role.level,
            ),
            None,
        )
