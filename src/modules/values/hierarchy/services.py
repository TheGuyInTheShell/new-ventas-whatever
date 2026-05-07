from typing import List
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.lib.register.service import Service
from core.lib.decorators.exceptions import handle_service_errors
from .models import ValuesHierarchy
from .schemas import RQValuesHierarchy, RSValuesHierarchy, RSValuesHierarchyList
from .exceptions import (
    ValuesHierarchyNotFoundError,
    ValuesHierarchyCreationError,
    ServiceResult,
)

class ValuesHierarchyService(Service):
    @handle_service_errors
    @injectable
    async def create_values_hierarchy(
        self,
        data: RQValuesHierarchy,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSValuesHierarchy]:
        """
        Create a new parent-child hierarchy relationship between two values.
        """
        hierarchy = ValuesHierarchy(
            ref_value_top=data.ref_value_top,
            ref_value_bottom=data.ref_value_bottom,
        )
        db.add(hierarchy)
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            raise ValuesHierarchyCreationError(f"Failed to create hierarchy: {str(e)}")
            
        await db.commit()
        await db.refresh(hierarchy)
        return RSValuesHierarchy.model_validate(hierarchy), None

    @handle_service_errors
    @injectable
    async def get_children(
        self,
        value_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[List[RSValuesHierarchy]]:
        """
        Get all direct children of a value (where value is the top/parent).
        """
        stmt = (
            select(ValuesHierarchy)
            .where(ValuesHierarchy.ref_value_top == value_id)
            .where(ValuesHierarchy.is_deleted == False)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()
        return [RSValuesHierarchy.model_validate(i) for i in items], None

    @handle_service_errors
    @injectable
    async def get_parents(
        self,
        value_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[List[RSValuesHierarchy]]:
        """
        Get all direct parents of a value (where value is the bottom/child).
        """
        stmt = (
            select(ValuesHierarchy)
            .where(ValuesHierarchy.ref_value_bottom == value_id)
            .where(ValuesHierarchy.is_deleted == False)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()
        return [RSValuesHierarchy.model_validate(i) for i in items], None

    @handle_service_errors
    @injectable
    async def get_hierarchy_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order: str = "asc",
        status: str = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSValuesHierarchyList]:
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
        items = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return (
            RSValuesHierarchyList(
                data=[RSValuesHierarchy.model_validate(i) for i in items],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
                next_page=page + 1 if page < total_pages else None,
                prev_page=page - 1 if page > 1 else None,
            ),
            None,
        )

