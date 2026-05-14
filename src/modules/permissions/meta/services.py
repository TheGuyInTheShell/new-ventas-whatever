from typing import List, Union
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service

from .models import MetaPermissions
from ..models import Permission

class PermissionsMetaService(Service):
    @injectable
    async def create_meta_permissions(
        self,
        key: str,
        value: str,
        ref_permission: int,
        db: AsyncSession = Depends(get_async_db),
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

    @injectable
    async def get_meta_permissions(
        self,
        id: Union[int, str],
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaPermissions:
        """
        Get a meta_permissions by ID from the database.
        """
        meta_obj = await MetaPermissions.find_one(db, id)
        if not meta_obj:
            raise Exception(f"MetaPermissions not found for id {id}")
        return meta_obj

    @injectable
    async def get_meta_permissions_all(
        self,
        page: int = 1,
        order: str = "asc",
        status: str = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> List[MetaPermissions]:
        """
        Get all meta_permissions from the database.
        """
        return await MetaPermissions.find_some(db, page, order, status)

    @injectable
    async def delete_meta_permissions(
        self,
        id: Union[int, str],
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """
        Delete a meta_permissions from the database.
        """
        await MetaPermissions.delete(db, id)

    @injectable
    async def update_meta_permissions(
        self,
        id: Union[int, str],
        key: str,
        value: str,
        ref_permission: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaPermissions:
        """
        Update a meta_permissions in the database.
        """
        meta_obj = await MetaPermissions.find_one(db, id)
        if not meta_obj:
            raise Exception(f"MetaPermissions not found for id {id}")
        meta_obj.key = key
        meta_obj.value = value
        meta_obj.ref_permission = ref_permission
        await meta_obj.save(db)
        return meta_obj

