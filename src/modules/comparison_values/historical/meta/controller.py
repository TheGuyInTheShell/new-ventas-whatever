from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import MetaComparisonValuesHistorical
from .schemas import (
    RQMetaComparisonValuesHistorical,
    RSMetaComparisonValuesHistorical,
    RSMetaComparisonValuesHistoricalList,
)

# prefix comparison_values/historical/meta
router = APIRouter()

tag = "meta_comparison_values_historical"


@router.get("/id/{id}", response_model=RSMetaComparisonValuesHistorical, status_code=200, tags=[tag])
async def get_meta(
    id: str | int, db: AsyncSession = Depends(get_async_db)
) -> RSMetaComparisonValuesHistorical:
    try:
        result = await MetaComparisonValuesHistorical.find_one(db, id)
        return RSMetaComparisonValuesHistorical(
            id=result.id,
            uid=result.uid,
            key=result.key,
            value=result.value,
            ref_comparison_value_historical=result.ref_comparison_value_historical,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSMetaComparisonValuesHistoricalList, status_code=200, tags=[tag])
async def get_metas(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSMetaComparisonValuesHistoricalList:
    try:
        result = await MetaComparisonValuesHistorical.find_some(db, pag or 1, ord, status)
        mapped_result = list(map(
            lambda x: RSMetaComparisonValuesHistorical(
                id=x.id,
                uid=x.uid,
                key=x.key,
                value=x.value,
                ref_comparison_value_historical=x.ref_comparison_value_historical,
            ),
            result,
        ))
        return RSMetaComparisonValuesHistoricalList(
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


@router.post("/", response_model=RSMetaComparisonValuesHistorical, status_code=201, tags=[tag])
async def create_meta(
    meta: RQMetaComparisonValuesHistorical, db: AsyncSession = Depends(get_async_db)
) -> RSMetaComparisonValuesHistorical:
    try:
        result = await MetaComparisonValuesHistorical(**meta.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_meta(id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await MetaComparisonValuesHistorical.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSMetaComparisonValuesHistorical, status_code=200, tags=[tag])
async def update_meta(
    id: str | int, meta: RQMetaComparisonValuesHistorical, db: AsyncSession = Depends(get_async_db)
) -> RSMetaComparisonValuesHistorical:
    try:
        result = await MetaComparisonValuesHistorical.update(db, id, meta.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e
