from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.lib.register.service import Service
from .models import ValuesHierarchy
from .schemas import RQValuesHierarchy

class ValuesHierarchyService(Service):
    async def create_values_hierarchy(
        self,
        db: AsyncSession,
        data: RQValuesHierarchy,
    ) -> ValuesHierarchy:
        """
        Create a new parent-child hierarchy relationship between two values.
        """
        hierarchy = ValuesHierarchy(
            ref_value_top=data.ref_value_top,
            ref_value_bottom=data.ref_value_bottom,
        )
        db.add(hierarchy)
        await db.flush()
        await db.refresh(hierarchy)
        return hierarchy

    async def get_children(
        self,
        db: AsyncSession,
        value_id: int,
    ) -> List[ValuesHierarchy]:
        """
        Get all direct children of a value (where value is the top/parent).
        """
        stmt = (
            select(ValuesHierarchy)
            .where(ValuesHierarchy.ref_value_top == value_id)
            .where(ValuesHierarchy.is_deleted == False)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_parents(
        self,
        db: AsyncSession,
        value_id: int,
    ) -> List[ValuesHierarchy]:
        """
        Get all direct parents of a value (where value is the bottom/child).
        """
        stmt = (
            select(ValuesHierarchy)
            .where(ValuesHierarchy.ref_value_bottom == value_id)
            .where(ValuesHierarchy.is_deleted == False)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_hierarchy_paginated(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        order: str = "asc",
        status: str = "exists",
    ) -> Tuple[List[ValuesHierarchy], int]:
        """
        Get paginated list of hierarchy relationships with total count.
        """
        stmt = select(ValuesHierarchy)

        if status == "exists":
            stmt = stmt.where(ValuesHierarchy.is_deleted == False)
        elif status == "deleted":
            stmt = stmt.where(ValuesHierarchy.is_deleted == True)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Ordering
        if order == "desc":
            stmt = stmt.order_by(ValuesHierarchy.id.desc())
        else:
            stmt = stmt.order_by(ValuesHierarchy.id.asc())

        # Pagination
        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

