from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Union

from core.lib.register.service import Service

from .models import MetaUsers
from ..models import User

class UsersMetaService(Service):
    async def create_meta_users(
        self,
        db: AsyncSession,
        key: str,
        value: str,
        ref_user: int,
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

    async def get_meta_users(
        self,
        db: AsyncSession,
        id: Union[int, str],
    ) -> MetaUsers:
        """
        Get a meta by ID from the database.
        """
        return await MetaUsers.find_one(db, id)

    async def get_meta_users_all(
        self,
        db: AsyncSession,
        page: int = 1,
        order: str = "asc",
        status: str = "exists",
    ) -> List[MetaUsers]:
        """
        Get all metas from the database.
        """
        return await MetaUsers.find_some(db, page, order, status)

    async def delete_meta_users(
        self,
        db: AsyncSession,
        id: Union[int, str],
    ) -> None:
        """
        Delete a meta from the database.
        """
        await MetaUsers.delete(db, id)

    async def update_meta_users(
        self,
        db: AsyncSession,
        id: Union[int, str],
        key: str,
        value: str,
        ref_user: int,
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

