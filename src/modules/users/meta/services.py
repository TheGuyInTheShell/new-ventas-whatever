from typing import List, Union
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service

from .models import MetaUsers
from ..models import User

class UsersMetaService(Service):
    @injectable
    async def create_meta_users(
        self,
        key: str,
        value: str,
        ref_user: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaUsers:
        """
        Create a new meta in the database.
        """
        meta_obj = MetaUsers(
            key=key,
            value=value,
            ref_user=await User.find_one(db, ref_user),
        )
        await meta_obj.save(db)
        return meta_obj

    @injectable
    async def get_meta_users(
        self,
        id: Union[int, str],
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaUsers:
        """
        Get a meta by ID from the database.
        """
        return await MetaUsers.find_one(db, id)

    @injectable
    async def get_meta_users_all(
        self,
        page: int = 1,
        order: str = "asc",
        status: str = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> List[MetaUsers]:
        """
        Get all metas from the database.
        """
        return await MetaUsers.find_some(db, page, order, status)

    @injectable
    async def delete_meta_users(
        self,
        id: Union[int, str],
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """
        Delete a meta from the database.
        """
        await MetaUsers.delete(db, id)

    @injectable
    async def update_meta_users(
        self,
        id: Union[int, str],
        key: str,
        value: str,
        ref_user: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaUsers:
        """
        Update a meta in the database.
        """
        meta_obj = await MetaUsers.find_one(db, id)
        meta_obj.key = key
        meta_obj.value = value
        meta_obj.ref_user = ref_user
        await meta_obj.save(db)
        return meta_obj

