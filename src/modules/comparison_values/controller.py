from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import ComparisonValue
from .schemas import (
    RQComparisonValue,
    RSComparisonValue,
    RSComparisonValueList,
    RSComparisonValueSimple,
    RSConvert
)
from .services import (
    create_comparison,
    update_comparison,
    get_comparisons_paginated,
    convert_value
)

# prefix /comparison_values (auto-registered by core/routes)
router = APIRouter()

tag = "comparison_values"


def comparison_to_response(comparison: ComparisonValue) -> RSComparisonValue:
    """Convert ComparisonValue model to response schema"""
    from sqlalchemy import inspect as sa_inspect

    source = None
    target = None

    # Check loaded state to avoid lazy-load in async context
    attrs = sa_inspect(comparison) if hasattr(comparison, '_sa_instance_state') else None
    loaded_keys = attrs.dict if attrs else {}

    if 'source_value' in loaded_keys and comparison.source_value:
        source = RSComparisonValueSimple(
            id=comparison.source_value.id,
            uid=comparison.source_value.uid,
            name=comparison.source_value.name,
            expression=comparison.source_value.expression
        )
    
    if 'target_value' in loaded_keys and comparison.target_value:
        target = RSComparisonValueSimple(
            id=comparison.target_value.id,
            uid=comparison.target_value.uid,
            name=comparison.target_value.name,
            expression=comparison.target_value.expression
        )
    
    return RSComparisonValue(
        uid=comparison.uid,
        id=comparison.id,
        quantity_from=comparison.quantity_from,
        quantity_to=comparison.quantity_to,
        value_from=comparison.value_from,
        value_to=comparison.value_to,
        context=comparison.context,
        source_value=source,
        target_value=target
    )


@router.get("/id/{id}", response_model=RSComparisonValue, status_code=200, tags=[tag])
async def get_comparison(
    id: str,
    db: AsyncSession = Depends(get_async_db)
) -> RSComparisonValue:
    """Get a single comparison by ID or UID"""
    result = await ComparisonValue.find_one(db, id)
    return comparison_to_response(result)


@router.get("/", response_model=RSComparisonValueList, status_code=200, tags=[tag])
async def get_comparisons(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    context: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
) -> RSComparisonValueList:
    """Get paginated list of comparisons, optionally filtered by context"""
    page = pag or 1
    page_size = 10
    
    comparisons, total = await get_comparisons_paginated(db, page, page_size, "id", ord, context=context)
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return RSComparisonValueList(
        data=[comparison_to_response(c) for c in comparisons],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None,
    )


@router.get("/all", response_model=RSComparisonValueList, status_code=200, tags=[tag])
async def get_all_comparisons(
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSComparisonValueList:
    """Get all comparisons without pagination"""
    result = await ComparisonValue.find_all(db, status)
    
    return RSComparisonValueList(
        data=[comparison_to_response(c) for c in result],
        total=len(result),
        page=1,
        page_size=len(result),
        total_pages=1,
        has_next=False,
        has_prev=False,
        next_page=None,
        prev_page=None,
    )


@router.post("/", response_model=RSComparisonValue, status_code=201, tags=[tag])
async def create_comparison_value(
    comparison: RQComparisonValue,
    db: AsyncSession = Depends(get_async_db)
) -> RSComparisonValue:
    """Create a new comparison between two values"""
    result = await create_comparison(db, comparison)
    return comparison_to_response(result)


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_comparison(
    id: str,
    db: AsyncSession = Depends(get_async_db)
) -> None:
    """Soft delete a comparison by ID or UID"""
    await ComparisonValue.delete(db, id)


@router.put("/id/{id}", response_model=RSComparisonValue, status_code=200, tags=[tag])
async def update_comparison_value(
    id: str,
    comparison: RQComparisonValue,
    db: AsyncSession = Depends(get_async_db)
) -> RSComparisonValue:
    """Update a comparison value"""
    result = await update_comparison(db, id, comparison)
    return comparison_to_response(result)


@router.get("/convert", response_model=RSConvert, status_code=200, tags=[tag])
async def convert(
    from_id: int,
    to_id: int,
    amount: float,
    db: AsyncSession = Depends(get_async_db)
) -> RSConvert:
    """
    Convert an amount from one value to another.
    
    Example: /convert?from_id=1&to_id=2&amount=100
    If 1 USD = 46 VES, converting 100 USD returns 4600 VES
    """
    result = await convert_value(db, from_id, to_id, amount)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No conversion rate found between value {from_id} and {to_id}"
        )
    
    return RSConvert(
        from_value=RSComparisonValueSimple(
            id=result["from_value"].id,
            uid=result["from_value"].uid,
            name=result["from_value"].name,
            expression=result["from_value"].expression
        ),
        to_value=RSComparisonValueSimple(
            id=result["to_value"].id,
            uid=result["to_value"].uid,
            name=result["to_value"].name,
            expression=result["to_value"].expression
        ),
        original_amount=result["original_amount"],
        converted_amount=result["converted_amount"],
        rate=result["rate"],
        inverse_rate=result["inverse_rate"]
    )
