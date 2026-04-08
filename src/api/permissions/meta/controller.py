from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.permissions.meta.models import MetaPermissions
from src.modules.permissions.meta.schemas import (
    RQMetaPermission,
    RSMetaPermission,
    RSMetaPermissionList,
)


class PermissionsMetaController(Controller):
    """
    Controller for Permissions Metadata management.
    
    Path: /api/v1/permissions/meta
    """

    @Get("/id/{id}", response_model=RSMetaPermission, status_code=200)
    async def get_meta_permission(
        self, id: int | str, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaPermission:
        try:
            result = await MetaPermissions.find_one(db, id)
            return RSMetaPermission(
                id=result.id,
                uid=result.uid,
                key=result.key,
                value=result.value,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSMetaPermissionList, status_code=200)
    async def get_meta_permissions(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSMetaPermissionList:
        try:
            result = await MetaPermissions.find_some(db, pag or 1, ord, status)
            mapped_result = list(map(
                lambda x: RSMetaPermission(
                    id=x.id,
                    uid=x.uid,
                    key=x.key,
                    value=x.value,
                ),
                result,
            ))
            return RSMetaPermissionList(
                data=mapped_result,
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

    @Post("/", response_model=RSMetaPermission, status_code=201)
    async def create_meta_permission(
        self, meta: RQMetaPermission, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaPermission:
        try:
            result = await MetaPermissions(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta_permission(self, id: int | str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaPermissions.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaPermission, status_code=200)
    async def update_meta_permission(
        self, id: int | str, meta: RQMetaPermission, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaPermission:
        try:
            result = await MetaPermissions.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
