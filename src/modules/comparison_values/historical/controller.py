from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import ComparisonValueHistorical
from .schemas import (
    RQHistoricalComparisonValue,
    RSHistoricalComparisonValue,
    RSHistoricalComparisonValueList,
)

# prefix comparison_values/historical
router = APIRouter()

tag = "historical_comparison_values"


@router.get("/id/{id}", response_model=RSHistoricalComparisonValue, status_code=200, tags=[tag])
async def get_historical_comparison_value(
    id: str | int, db: AsyncSession = Depends(get_async_db)
) -> RSHistoricalComparisonValue:
    try:
        result = await ComparisonValueHistorical.find_one(db, id)
        return RSHistoricalComparisonValue(
            id=result.id,
            uid=result.uid,
            quantity_from=result.quantity_from,
            quantity_to=result.quantity_to,
            value_from=result.value_from,
            value_to=result.value_to,
            original_comparison_id=result.original_comparison_id,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSHistoricalComparisonValueList, status_code=200, tags=[tag])
async def get_historicals(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSHistoricalComparisonValueList:
    try:
        result = await ComparisonValueHistorical.find_some(db, pag or 1, ord, status)
        mapped_result = list(map(
            lambda x: RSHistoricalComparisonValue(
                id=x.id,
                uid=x.uid,
                quantity_from=x.quantity_from,
                quantity_to=x.quantity_to,
                value_from=x.value_from,
                value_to=x.value_to,
                original_comparison_id=x.original_comparison_id,
            ),
            result,
        ))
        return RSHistoricalComparisonValueList(
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


@router.post("/", response_model=RSHistoricalComparisonValue, status_code=201, tags=[tag])
async def create_historical_comparison_value(
    historical: RQHistoricalComparisonValue, db: AsyncSession = Depends(get_async_db)
) -> RSHistoricalComparisonValue:
    try:
        result = await ComparisonValueHistorical(**historical.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_historical_comparison_value(id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await ComparisonValueHistorical.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSHistoricalComparisonValue, status_code=200, tags=[tag])
async def update_historical_comparison_value(
    id: str | int, historical: RQHistoricalComparisonValue, db: AsyncSession = Depends(get_async_db)
) -> RSHistoricalComparisonValue:
    try:
        result = await ComparisonValueHistorical.update(db, id, historical.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e
