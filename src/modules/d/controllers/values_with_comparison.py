from fastapi import APIRouter, Depends, Body
from typing import Annotated
from enum import Enum
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.d.schemas.values_with_comparison import RQValueWithComparison, QueryValuesWithComparison

tags: list[str | Enum] = ["values_with_comparison"]
router = APIRouter(tags=tags)


@router.post("/")
async def create_value_with_comparison(
    payload: RQValueWithComparison,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Save an optional value (and its meta data) and an optional comparison (and its meta data).
    """
    from src.modules.d.services.value_with_comparison import save_value_with_comparison_service
    return await save_value_with_comparison_service(db, payload)


@router.put("/id/{id}")
async def update_value_with_comparison(
    id: str,
    payload: RQValueWithComparison,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a value (and its meta data) and its comparison.
    """
    from src.modules.d.services.value_with_comparison import update_value_with_comparison_service
    return await update_value_with_comparison_service(db, id, payload)


@router.post("/query")
async def query_values_with_comparison(
    payload: QueryValuesWithComparison,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all values with their comparisons.
    """
    from src.modules.d.services.value_with_comparison import get_values_with_comparison_service
    return await get_values_with_comparison_service(db, payload)

