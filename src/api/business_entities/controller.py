from typing import List, Optional, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.business_entities.models import BusinessEntity
from src.modules.business_entities.schemas import RQBusinessEntity, RSBusinessEntity, RSBusinessEntityList
from src.modules.business_entities.services import create_business_entity


class BusinessEntitiesController(Controller):
    """
    Controller for Business Entities management.
    
    Path: /api/v1/business_entities
    """

    @Get("/id/{id}", response_model=RSBusinessEntity, status_code=200)
    async def get_BusinessEntity(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> RSBusinessEntity:
        try:
            result: BusinessEntity = await BusinessEntity.find_one(db, id)
            return RSBusinessEntity(
                id=result.id,
                uid=result.uid,
                name=result.name,
                type=result.type,
                context=result.context,
                metadata_info=result.metadata_info
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSBusinessEntityList, status_code=200)
    async def get_BusinessEntities(
        self,
        pag: int = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        context: Optional[str] = None,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntityList:
        try:
            result = await BusinessEntity.find_some(db, pag or 1, ord, status) 
            if context:
                result = [e for e in result if e.context == context]
            mapped_result = [RSBusinessEntity(
                id=entity.id,
                uid=entity.uid,
                name=entity.name,
                type=entity.type,
                context=entity.context,
                metadata_info=entity.metadata_info
            ) for entity in result]
            return RSBusinessEntityList(
                data=mapped_result,
                total=len(mapped_result),
                page=pag,
                page_size=10,
                total_pages=len(mapped_result) // 10 + 1,
                has_next=pag < len(mapped_result) // 10 + 1,
                has_prev=pag > 1,
                next_page=pag + 1 if pag < len(mapped_result) // 10 + 1 else None,
                prev_page=pag - 1 if pag > 1 else None
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSBusinessEntity, status_code=201)
    async def create_BusinessEntity_endpoint(
        self, entity: RQBusinessEntity, db: AsyncSession = Depends(get_async_db)
    ) -> RSBusinessEntity:
        try:
            result = await create_business_entity(db, entity)
            return RSBusinessEntity(
                id=result.id,
                uid=result.uid,
                name=result.name,
                type=result.type,
                context=result.context,
                metadata_info=result.metadata_info
            )
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_BusinessEntity(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await BusinessEntity.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSBusinessEntity, status_code=200)
    async def update_BusinessEntity(
        self, id: str, entity: RQBusinessEntity, db: AsyncSession = Depends(get_async_db)
    ) -> RSBusinessEntity:
        try:
            result = await BusinessEntity.update(db, id, entity.model_dump())
            return RSBusinessEntity(
                id=result.id,
                uid=result.uid,
                name=result.name,
                type=result.type,
                context=result.context,
                metadata_info=result.metadata_info
            )
        except Exception as e:
            print(e)
            raise e
