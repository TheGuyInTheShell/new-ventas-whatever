from typing import Literal, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.business_entities_groups.models import BusinessEntitiesGroup
from src.modules.business_entities_groups.schemas import (
    RQBusinessEntitiesGroup,
    RSBusinessEntitiesGroup,
    RSBusinessEntitiesGroupList,
)
from src.modules.business_entities_groups.services import (
    create_business_entities_group,
    update_business_entities_group,
    get_groups_paginated,
)


class BusinessEntitiesGroupsController(Controller):
    """
    Controller for Business Entities Groups management.
    
    Path: /api/v1/business_entities_groups
    """

    def _group_to_response(self, group: BusinessEntitiesGroup) -> RSBusinessEntitiesGroup:
        """Convert BusinessEntitiesGroup model to response schema"""
        return RSBusinessEntitiesGroup(
            id=group.id,
            uid=group.uid,
            name=group.name,
            description=group.description,
        )

    @Get("/id/{id}", response_model=RSBusinessEntitiesGroup, status_code=200)
    async def get_group(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroup:
        """Get a single business entities group by ID or UID"""
        result = await BusinessEntitiesGroup.find_one(db, id)
        return self._group_to_response(result)

    @Get("/", response_model=RSBusinessEntitiesGroupList, status_code=200)
    async def get_groups(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroupList:
        """Get paginated list of business entities groups"""
        page = pag or 1
        page_size = 10

        items, total = await get_groups_paginated(db, page, page_size, ord, status)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return RSBusinessEntitiesGroupList(
            data=[self._group_to_response(g) for g in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None,
        )

    @Get("/all", response_model=RSBusinessEntitiesGroupList, status_code=200)
    async def get_all_groups(
        self,
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroupList:
        """Get all business entities groups without pagination"""
        result = await BusinessEntitiesGroup.find_all(db, status)

        return RSBusinessEntitiesGroupList(
            data=[self._group_to_response(g) for g in result],
            total=len(result),
            page=1,
            page_size=len(result),
            total_pages=1,
            has_next=False,
            has_prev=False,
            next_page=None,
            prev_page=None,
        )

    @Post("/", response_model=RSBusinessEntitiesGroup, status_code=201)
    async def create_group(
        self,
        group: RQBusinessEntitiesGroup,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroup:
        """Create a new business entities group"""
        result = await create_business_entities_group(db, group)
        return self._group_to_response(result)

    @Delete("/id/{id}", status_code=204)
    async def delete_group(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Soft delete a business entities group"""
        await BusinessEntitiesGroup.delete(db, id)

    @Put("/id/{id}", response_model=RSBusinessEntitiesGroup, status_code=200)
    async def update_group(
        self,
        id: str,
        group: RQBusinessEntitiesGroup,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroup:
        """Update a business entities group"""
        result = await update_business_entities_group(db, id, group)
        return self._group_to_response(result)
