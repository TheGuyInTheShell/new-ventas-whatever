from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.cache import Cache
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.roles.models import Role
from src.modules.roles.schemas import RQRole, RSRole, RSRoleList
from src.modules.roles.services import create_role


class RolesController(Controller):
    """
    Controller for Roles management.
    
    Path: /api/v1/roles
    """

    cache = Cache()

    @Get("/id/{id}", response_model=RSRole, status_code=200)
    @cache.cache_endpoint(ttl=60, namespace="roles")
    async def get_Role(self, id: str, db: AsyncSession = Depends(get_async_db)) -> RSRole:
        try:
            result = await Role.find_one(db, id)
            return RSRole(
                uid=result.uid,
                id=result.id,
                description=result.description,
                name=result.name,
                level=result.level,
                permissions=result.permissions,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSRoleList, status_code=200)
    @cache.cache_endpoint(ttl=60, namespace="roles")
    async def get_Roles(
        self,
        pag: int = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSRoleList:
        try:
            result = await Role.find_some(db, pag or 1, ord, status)
            mapped_result = map(
                lambda x: RSRole(
                    uid=x.uid,
                    id=x.id,
                    description=x.description,
                    name=x.name,
                    level=x.level,
                    permissions=x.permissions,
                ),
                result,
            )
            return RSRoleList(
                data=list(mapped_result),
                total=0,
                page=0,
                page_size=0,
                total_pages=0,
                has_next=False,
                has_prev=False,
                next_page=0,
                prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSRole, status_code=201)
    async def create_Role(self, role: RQRole, db: AsyncSession = Depends(get_async_db)) -> RSRole:
        try:
            result = await create_role(db, role)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_Role(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Role.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSRole, status_code=200)
    async def update_Role(
        self, id: str, role: RQRole, db: AsyncSession = Depends(get_async_db)
    ) -> RSRole:
        try:
            result = await Role.update(db, id, role.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
