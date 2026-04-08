from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.values.meta.models import MetaValue
from src.modules.values.meta.schemas import (
    RQMetaValue,
    RSMetaValue,
    RSMetaValueList,
)


class ValuesMetaController(Controller):
    """
    Controller for Values Metadata management.
    
    Path: /api/v1/values/meta
    """

    @Get("/id/{id}", response_model=RSMetaValue, status_code=200)
    async def get_meta(
        self, id: str | int, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaValue:
        try:
            result = await MetaValue.find_one(db, id)
            return RSMetaValue(
                id=result.id,
                uid=result.uid,
                key=result.key,
                value=result.value,
                ref_value=result.ref_value,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSMetaValueList, status_code=200)
    async def get_metas(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSMetaValueList:
        try:
            result = await MetaValue.find_some(db, pag or 1, ord, status)
            mapped_result = list(map(
                lambda x: RSMetaValue(
                    id=x.id,
                    uid=x.uid,
                    key=x.key,
                    value=x.value,
                    ref_value=x.ref_value,
                ),
                result,
            ))
            return RSMetaValueList(
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

    @Post("/", response_model=RSMetaValue, status_code=201)
    async def create_meta(
        self, meta: RQMetaValue, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaValue:
        try:
            result = await MetaValue(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaValue.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaValue, status_code=200)
    async def update_meta(
        self, id: str | int, meta: RQMetaValue, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaValue:
        try:
            result = await MetaValue.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
