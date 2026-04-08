from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.business_entities.meta.models import MetaBusinessEntity
from src.modules.business_entities.meta.schemas import (
    RQMetaBusinessEntity,
    RSMetaBusinessEntity,
    RSMetaBusinessEntityList,
)


class BusinessEntitiesMetaController(Controller):
    """
    Controller for Business Entities Metadata management.
    
    Path: /api/v1/business_entities/meta
    """

    @Get("/id/{id}", response_model=RSMetaBusinessEntity, status_code=200)
    async def get_meta(
        self, id: str | int, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaBusinessEntity:
        try:
            result = await MetaBusinessEntity.find_one(db, id)
            return RSMetaBusinessEntity(
                id=result.id,
                uid=result.uid,
                key=result.key,
                value=result.value,
                ref_business_entity=result.ref_business_entity,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSMetaBusinessEntityList, status_code=200)
    async def get_metas(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSMetaBusinessEntityList:
        try:
            result = await MetaBusinessEntity.find_some(db, pag or 1, ord, status)
            mapped_result = list(map(
                lambda x: RSMetaBusinessEntity(
                    id=x.id,
                    uid=x.uid,
                    key=x.key,
                    value=x.value,
                    ref_business_entity=x.ref_business_entity,
                ),
                result,
            ))
            return RSMetaBusinessEntityList(
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

    @Post("/", response_model=RSMetaBusinessEntity, status_code=201)
    async def create_meta(
        self, meta: RQMetaBusinessEntity, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaBusinessEntity:
        try:
            result = await MetaBusinessEntity(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaBusinessEntity.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaBusinessEntity, status_code=200)
    async def update_meta(
        self, id: str | int, meta: RQMetaBusinessEntity, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaBusinessEntity:
        try:
            result = await MetaBusinessEntity.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
