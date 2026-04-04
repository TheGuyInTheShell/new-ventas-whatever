from typing import List, Optional, Tuple, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .models import ComparisonValue
from .historical import ComparisonValueHistorical
from .schemas import RQComparisonValue
from app.modules.values.models import Value


async def create_comparison(
    db: AsyncSession,
    data: RQComparisonValue
) -> ComparisonValue:
    """Create a new comparison value"""
    from .meta.models import MetaComparisonValue
    
    comparison = ComparisonValue(
        quantity_from=data.quantity_from,
        quantity_to=data.quantity_to,
        value_from=data.value_from,
        value_to=data.value_to,
        context=data.context
    )
    await comparison.save(db)
    
    if data.meta:
        for m in data.meta:
            meta_item = MetaComparisonValue(
                key=m.key,
                value=m.value,
                ref_comparison_value=comparison.id
            )
            await meta_item.save(db)
    
    # Eager load relationships
    stmt = select(ComparisonValue).options(
        selectinload(ComparisonValue.source_value),
        selectinload(ComparisonValue.target_value)
    ).where(ComparisonValue.id == comparison.id)
    
    result = await db.execute(stmt)
    comparison = result.scalar_one()
    
    return comparison


async def update_comparison(
    db: AsyncSession,
    comparison_id: int | str,
    data: RQComparisonValue
) -> ComparisonValue:
    """Update a comparison value"""
    # Fetch existing comparison to check for changes and snapshot if needed
    comparison = await ComparisonValue.find_one(db, comparison_id)
    
    # Check if price (quantity_to) has changed
    if float(comparison.quantity_to) != float(data.quantity_to):
        await create_historical_snapshot(db, comparison)
    
    update_data = {
        "quantity_from": data.quantity_from,
        "quantity_to": data.quantity_to,
        "value_from": data.value_from,
        "value_to": data.value_to,
        "context": data.context
    }
    await ComparisonValue.update(db, comparison_id, update_data)
    
    # Eager load relationships for the updated item
    stmt = select(ComparisonValue).options(
        selectinload(ComparisonValue.source_value),
        selectinload(ComparisonValue.target_value)
    ).where(ComparisonValue.id == int(comparison_id))
    
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_comparisons_paginated(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    order_by: str = "id",
    order: str = "asc",
    status: Literal["exists", "deleted", "all"] = "exists",
    value_from: Optional[int | str] = None,
    value_to: Optional[int | str] = None,
    context: Optional[str] = None,
) -> Tuple[List[ComparisonValue], int]:
    """Get paginated list of comparisons with total count"""
    # Build filters dict, only include non-None values
    filters = {}
    if value_from is not None:
        filters["value_from"] = value_from
    if value_to is not None:
        filters["value_to"] = value_to
    if context is not None:
        filters["context"] = context

    comparisons = await ComparisonValue.find_some(
        db, 
        pag=page, 
        order_by=order_by, 
        ord=order, 
        status=status,
        filters=filters
    )
    
    total = await ComparisonValue.count(db, status=status)
    
    return comparisons, total


async def find_comparison_rate(
    db: AsyncSession,
    from_value_id: int,
    to_value_id: int
) -> Optional[Tuple[float, bool]]:
    """
    Find the conversion rate between two values.
    Returns (rate, is_direct) tuple or None if not found.
    is_direct=True means from->to exists, False means to->from exists (inverse).
    """
    # Try direct comparison
    query = select(ComparisonValue).where(
        ComparisonValue.value_from == from_value_id,
        ComparisonValue.value_to == to_value_id,
        ComparisonValue.is_deleted == False
    )
    result = (await db.execute(query)).scalar_one_or_none()
    
    if result:
        rate = result.quantity_to / result.quantity_from
        return (rate, True)
    
    # Try inverse comparison
    query = select(ComparisonValue).where(
        ComparisonValue.value_from == to_value_id,
        ComparisonValue.value_to == from_value_id,
        ComparisonValue.is_deleted == False
    )
    result = (await db.execute(query)).scalar_one_or_none()
    
    if result:
        # Inverse rate: if 1 USD = 46 VES, then 1 VES = 1/46 USD
        rate = result.quantity_from / result.quantity_to
        return (rate, False)
    
    return None


async def convert_value(
    db: AsyncSession,
    from_value_id: int,
    to_value_id: int,
    amount: float
) -> Optional[dict]:
    """
    Convert an amount from one value to another.
    Returns conversion details or None if no rate found.
    """
    # Get the values
    from_value = await Value.find_one(db, from_value_id)
    to_value = await Value.find_one(db, to_value_id)
    
    # Find the rate
    rate_result = await find_comparison_rate(db, from_value_id, to_value_id)
    
    if not rate_result:
        return None
    
    rate, _ = rate_result
    converted_amount = amount * rate
    
    return {
        "from_value": from_value,
        "to_value": to_value,
        "original_amount": amount,
        "converted_amount": converted_amount,
        "rate": rate,
        "inverse_rate": 1 / rate if rate != 0 else 0
    }


async def create_historical_snapshot(
    db: AsyncSession,
    comparison: ComparisonValue
) -> ComparisonValueHistorical:
    """Create a historical snapshot from a comparison value"""
    historical = ComparisonValueHistorical(
        quantity_from=comparison.quantity_from,
        quantity_to=comparison.quantity_to,
        value_from=comparison.value_from,
        value_to=comparison.value_to,
        context=comparison.context,
        original_comparison_id=comparison.id
    )
    await historical.save(db)
    return historical
