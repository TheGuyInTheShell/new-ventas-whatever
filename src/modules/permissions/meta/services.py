from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Union

from core.lib.register.service import Service

from .models import MetaPermissions
from ..models import Permission

class PermissionsMetaService(Service):
    async def create_meta_permissions(
        self,
        db: AsyncSession,
        key: str,
        value: str,
        ref_permission: int,
    ) -> MetaPermissions:
        """
        Create a new meta_permissions in the database.
        """
        meta_obj = MetaPermissions(
            key=key,
            value=value,
            ref_permission=await Permission.find_one(db, ref_permission),
        )
        await meta_obj.save(db)
        return meta_obj

    async def get_meta_permissions(
        self,
        db: AsyncSession,
        id: Union[int, str],
    ) -> MetaPermissions:
        """
        Get a meta_permissions by ID from the database.
        """
        return await MetaPermissions.find_one(db, id)

    async def get_meta_permissions_all(
        self,
        db: AsyncSession,
        page: int = 1,
        order: str = "asc",
        status: str = "exists",
    ) -> List[MetaPermissions]:
        """
        Get all meta_permissions from the database.
        """
        return await MetaPermissions.find_some(db, page, order, status)

    async def delete_meta_permissions(
        self,
        db: AsyncSession,
        id: Union[int, str],
    ) -> None:
        """
        Delete a meta_permissions from the database.
        """
        await MetaPermissions.delete(db, id)

    async def update_meta_permissions(
        self,
        db: AsyncSession,
        id: Union[int, str],
        key: str,
        value: str,
        ref_permission: int,
    ) -> MetaPermissions:
        """
        Update a meta_permissions in the database.
        """
        meta_obj = await MetaPermissions.find_one(db, id)
        meta_obj.key = key
        meta_obj.value = value
        meta_obj.ref_permission = ref_permission
        await meta_obj.save(db)
        return meta_obj

