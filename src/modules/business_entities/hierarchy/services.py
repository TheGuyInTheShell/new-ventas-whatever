from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .models import BusinessEntitiesHierarchy
from .schemas import RQBusinessEntitiesHierarchy


async def create_entity_hierarchy(
    db: AsyncSession,
    data: RQBusinessEntitiesHierarchy,
) -> BusinessEntitiesHierarchy:
    """
    Create a new parent-child hierarchy relationship between two business entities.
    """
    hierarchy = BusinessEntitiesHierarchy(
        ref_entity_top=data.ref_entity_top,
        ref_entity_bottom=data.ref_entity_bottom,
    )
    db.add(hierarchy)
    await db.flush()
    await db.refresh(hierarchy)
    return hierarchy


async def get_children(
    db: AsyncSession,
    entity_id: int,
) -> List[BusinessEntitiesHierarchy]:
    """
    Get all direct children of an entity (where entity is the top/parent).
    """
    stmt = (
        select(BusinessEntitiesHierarchy)
        .where(BusinessEntitiesHierarchy.ref_entity_top == entity_id)
        .where(BusinessEntitiesHierarchy.is_deleted == False)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_parents(
    db: AsyncSession,
    entity_id: int,
) -> List[BusinessEntitiesHierarchy]:
    """
    Get all direct parents of an entity (where entity is the bottom/child).
    """
    stmt = (
        select(BusinessEntitiesHierarchy)
        .where(BusinessEntitiesHierarchy.ref_entity_bottom == entity_id)
        .where(BusinessEntitiesHierarchy.is_deleted == False)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_hierarchy_paginated(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    order: str = "asc",
    status: str = "exists",
) -> Tuple[List[BusinessEntitiesHierarchy], int]:
    """
    Get paginated list of hierarchy relationships with total count.
    """
    stmt = select(BusinessEntitiesHierarchy)

    if status == "exists":
        stmt = stmt.where(BusinessEntitiesHierarchy.is_deleted == False)
    elif status == "deleted":
        stmt = stmt.where(BusinessEntitiesHierarchy.is_deleted == True)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Ordering
    if order == "desc":
        stmt = stmt.order_by(BusinessEntitiesHierarchy.id.desc())
    else:
        stmt = stmt.order_by(BusinessEntitiesHierarchy.id.asc())

    # Pagination
    offset = (max(page, 1) - 1) * page_size
    stmt = stmt.limit(page_size).offset(offset)

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total
