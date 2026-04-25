from typing import List, Tuple, Optional
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from core.lib.register.service import Service

from .models import BusinessEntitiesGroup
from .schemas import RQBusinessEntitiesGroup

class BusinessEntitiesGroupsService(Service):
    @injectable
    async def create_business_entities_group(
        self,
        group_data: RQBusinessEntitiesGroup,
        db: AsyncSession = Depends(get_async_db),
    ) -> BusinessEntitiesGroup:
        """
        Create a new business entities group.
        """
        group = BusinessEntitiesGroup(
            name=group_data.name,
            description=group_data.description or "",
        )
        db.add(group)
        await db.flush()
        await db.refresh(group)
        return group

    @injectable
    async def update_business_entities_group(
        self,
        group_id: int | str,
        group_data: RQBusinessEntitiesGroup,
        db: AsyncSession = Depends(get_async_db),
    ) -> BusinessEntitiesGroup:
        """
        Update a business entities group.
        """
        update_data = {
            "name": group_data.name,
            "description": group_data.description or "",
        }
        result = await BusinessEntitiesGroup.update(db, group_id, update_data)
        return result

    @injectable
    async def get_groups_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order: str = "asc",
        status: str = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> Tuple[List[BusinessEntitiesGroup], int]:
        """
        Get paginated list of business entities groups with total count.
        """
        stmt = select(BusinessEntitiesGroup)

        if status == "exists":
            stmt = stmt.where(BusinessEntitiesGroup.is_deleted == False)
        elif status == "deleted":
            stmt = stmt.where(BusinessEntitiesGroup.is_deleted == True)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Ordering
        if order == "desc":
            stmt = stmt.order_by(BusinessEntitiesGroup.id.desc())
        else:
            stmt = stmt.order_by(BusinessEntitiesGroup.id.asc())

        # Pagination
        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

