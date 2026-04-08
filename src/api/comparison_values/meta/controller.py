from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.comparison_values.meta.models import MetaComparisonValue
from src.modules.comparison_values.meta.schemas import (
    RQMetaComparisonValue,
    RSMetaComparisonValue,
    RSMetaComparisonValueList,
)


class ComparisonValuesMetaController(Controller):
    """
    Controller for Comparison Values Metadata management.
    
    Path: /api/v1/comparison_values/meta
    """

    @Get("/id/{id}", response_model=RSMetaComparisonValue, status_code=200)
    async def get_meta(
        self, id: str | int, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaComparisonValue:
        try:
            result = await MetaComparisonValue.find_one(db, id)
            return RSMetaComparisonValue(
                id=result.id,
                uid=result.uid,
                key=result.key,
                value=result.value,
                ref_comparison_value=result.ref_comparison_value,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSMetaComparisonValueList, status_code=200)
    async def get_metas(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSMetaComparisonValueList:
        try:
            result = await MetaComparisonValue.find_some(db, pag or 1, ord, status)
            mapped_result = list(map(
                lambda x: RSMetaComparisonValue(
                    id=x.id,
                    uid=x.uid,
                    key=x.key,
                    value=x.value,
                    ref_comparison_value=x.ref_comparison_value,
                ),
                result,
            ))
            return RSMetaComparisonValueList(
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

    @Post("/", response_model=RSMetaComparisonValue, status_code=201)
    async def create_meta(
        self, meta: RQMetaComparisonValue, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaComparisonValue:
        try:
            result = await MetaComparisonValue(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaComparisonValue.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaComparisonValue, status_code=200)
    async def update_meta(
        self, id: str | int, meta: RQMetaComparisonValue, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaComparisonValue:
        try:
            result = await MetaComparisonValue.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
