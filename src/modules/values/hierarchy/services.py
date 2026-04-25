from typing import List, Tuple
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.lib.register.service import Service
from .models import ValuesHierarchy
from .schemas import RQValuesHierarchy

class ValuesHierarchyService(Service):
    @injectable
    async def create_values_hierarchy(
        self,
        data: RQValuesHierarchy,
        db: AsyncSession = Depends(get_async_db),
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

    @injectable
    async def get_children(
        self,
        value_id: int,
        db: AsyncSession = Depends(get_async_db),
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

    @injectable
    async def get_parents(
        self,
        value_id: int,
        db: AsyncSession = Depends(get_async_db),
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

    @injectable
    async def get_hierarchy_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order: str = "asc",
        status: str = "exists",
        db: AsyncSession = Depends(get_async_db),
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

