from typing import List, Tuple
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.lib.register.service import Service

from .models import BusinessEntitiesHierarchy
from .schemas import RQBusinessEntitiesHierarchy

class BusinessEntitiesHierarchyService(Service):
    @injectable
    async def create_entity_hierarchy(
        self,
        data: RQBusinessEntitiesHierarchy,
        db: AsyncSession = Depends(get_async_db),
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

    @injectable
    async def get_children(
        self,
        entity_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[BusinessEntitiesHierarchy]:
        """
        Get all direct children of an entity (where entity is the top/parent).
        """
        stmt = (
            select(BusinessEntitiesHierarchy)
            .where(BusinessEntitiesHierarchy.ref_entity_top == entity_id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @injectable
    async def get_parents(
        self,
        entity_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[BusinessEntitiesHierarchy]:
        """
        Get all direct parents of an entity (where entity is the bottom/child).
        """
        stmt = (
            select(BusinessEntitiesHierarchy)
            .where(BusinessEntitiesHierarchy.ref_entity_bottom == entity_id)
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
    ) -> Tuple[List[BusinessEntitiesHierarchy], int]:
        """
        Get paginated list of hierarchy relationships with total count.
        """
        stmt = select(BusinessEntitiesHierarchy)

        stmt = select(BusinessEntitiesHierarchy)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Ordering
        if order == "desc":
            stmt = stmt.order_by(BusinessEntitiesHierarchy.ref_entity_top.desc())
        else:
            stmt = stmt.order_by(BusinessEntitiesHierarchy.ref_entity_top.asc())

        # Pagination
        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @injectable
    async def get_hierarchy_link(
        self,
        ref_entity_top: int,
        ref_entity_bottom: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> BusinessEntitiesHierarchy | None:
        """
        Check if a parent-child relationship already exists.
        """
        stmt = (
            select(BusinessEntitiesHierarchy)
            .where(BusinessEntitiesHierarchy.ref_entity_top == ref_entity_top)
            .where(BusinessEntitiesHierarchy.ref_entity_bottom == ref_entity_bottom)
        )
        result = await db.execute(stmt)
        return result.scalars().first()
