from typing import Literal, Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import Value
from .schemas import RQValue, RQValueQuery, RSValue, RSValueList, RSMetaValue
from .services import create_value_with_meta, update_value_with_meta, get_values_paginated
from app.modules.comparison_values.controller import comparison_to_response

# prefix /values (auto-registered by core/routes)
router = APIRouter()

tag = "values"


def value_to_response(value: Value) -> RSValue:
    """Convert Value model to RSValue response schema"""
    from sqlalchemy import inspect as sa_inspect

    # Check which relationships are actually loaded (avoid lazy-load in async)
    loaded = sa_inspect(value).dict if hasattr(value, '__dict__') else {}
    attrs = sa_inspect(value) if hasattr(value, '_sa_instance_state') else None

    meta_list = None
    if attrs and 'meta' in attrs.dict:
        meta_list = [
            RSMetaValue(
                uid=m.uid,
                id=m.id,
                key=m.key,
                value=m.value
            )
            for m in value.meta if not m.is_deleted
        ]

    comparison_data = None
    if attrs and 'comparisons_from' in attrs.dict and value.comparisons_from:
        comparison_data = comparison_to_response(value.comparisons_from[0])

    balances_data = None
    if attrs and 'balances' in attrs.dict and value.balances is not None:
        from .schemas import RSBalance
        balances_data = [
            RSBalance(
                id=b.id,
                quantity=round(b.quantity, 4),
                type=b.type 
            )
            for b in value.balances if not b.is_deleted
        ]

    return RSValue(
        uid=value.uid,
        id=value.id,
        name=value.name,
        expression=value.expression,
        type=value.type,
        context=value.context,
        identifier=value.identifier,
        meta=meta_list,
        balances=balances_data,
        comparison=comparison_data
    )


@router.get("/id/{id}", response_model=RSValue, status_code=200, tags=[tag])
async def get_value(
    id: str, 
    db: AsyncSession = Depends(get_async_db)
) -> RSValue:
    """Get a single value by ID or UID"""
    result = await Value.find_one(db, id)
    return value_to_response(result)


@router.get("/", response_model=RSValueList, status_code=200, tags=[tag])
async def get_values(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    context: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
) -> RSValueList:
    """Get paginated list of values"""
    page = pag or 1
    page_size = 10
    
    filters = {}
    if context:
        filters["context"] = context
    if type:
        filters["type"] = type
    
    values, total = await get_values_paginated(db, page, page_size, "id", ord, filters=filters)
    # create generic find_some with filters if get_values_paginated doesn't support it 
    # but get_values_paginated is a wrapper.
    # I should check services.py get_values_paginated signature.
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return RSValueList(
        data=[value_to_response(v) for v in values],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page < total_pages else None,
    )


@router.get("/all", response_model=RSValueList, status_code=200, tags=[tag])
async def get_all_values(
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSValueList:
    """Get all values without pagination"""
    result = await Value.find_all(db, status)
    
    return RSValueList(
        data=[value_to_response(v) for v in result],
        total=len(result),
        page=1,
        page_size=len(result),
        total_pages=1,
        has_next=False,
        has_prev=False,
        next_page=None,
        prev_page=None,
    )


@router.post("/", response_model=RSValue, status_code=201, tags=[tag])
async def create_value(
    value: RQValue, 
    db: AsyncSession = Depends(get_async_db)
) -> RSValue:
    """Create a new value with optional metadata"""
    result = await create_value_with_meta(db, value)
    return value_to_response(result)


@router.post("/bulk", response_model=List[RSValue], status_code=201, tags=[tag])
async def create_values_bulk_endpoint(
    values: List[RQValue],
    db: AsyncSession = Depends(get_async_db)
) -> List[RSValue]:
    """Create multiple values in bulk with optional metadata"""
    from .services import create_values_bulk
    results = await create_values_bulk(db, values)
    return [value_to_response(v) for v in results]


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_value(
    id: str, 
    db: AsyncSession = Depends(get_async_db)
) -> None:
    """Soft delete a value by ID or UID"""
    await Value.delete(db, id)


@router.put("/id/{id}", response_model=RSValue, status_code=200, tags=[tag])
async def update_value(
    id: str, 
    value: RQValue, 
    db: AsyncSession = Depends(get_async_db)
) -> RSValue:
    """Update a value and its metadata"""
    result = await update_value_with_meta(db, id, value)
    return value_to_response(result)

# {prefix global}/values/query
@router.post("/query", response_model=RSValueList, status_code=200, tags=[tag])
async def query_values(
    query: RQValueQuery,
    db: AsyncSession = Depends(get_async_db)
) -> RSValueList:
    """Query values based on filters with optional comparison join"""
    values, total = await Value.query(db, query)

    page = max(query.page, 1)
    page_size = query.page_size
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return RSValueList(
        data=[value_to_response(v) for v in values],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None,
    )
