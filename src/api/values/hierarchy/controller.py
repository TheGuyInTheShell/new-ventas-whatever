from typing import Literal, Optional, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.values.hierarchy.models import ValuesHierarchy
from src.modules.values.hierarchy.schemas import (
    RQValuesHierarchy,
    RSValuesHierarchy,
    RSValuesHierarchyList,
)
from src.modules.values.hierarchy.services import (
    create_values_hierarchy,
    get_children,
    get_parents,
    get_hierarchy_paginated,
)


class ValuesHierarchyController(Controller):
    """
    Controller for Values Hierarchy management.
    
    Path: /api/v1/values/hierarchy
    """

    def _hierarchy_to_response(self, h: ValuesHierarchy) -> RSValuesHierarchy:
        """Convert ValuesHierarchy model to response schema"""
        return RSValuesHierarchy(
            id=h.id,
            uid=h.uid,
            ref_value_top=h.ref_value_top,
            ref_value_bottom=h.ref_value_bottom,
        )

    @Get("/id/{id}", response_model=RSValuesHierarchy, status_code=200)
    async def get_value_hierarchy(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValuesHierarchy:
        """Get a single hierarchy relationship by ID or UID"""
        result = await ValuesHierarchy.find_one(db, id)
        return self._hierarchy_to_response(result)

    @Get("/", response_model=RSValuesHierarchyList, status_code=200)
    async def get_value_hierarchies(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValuesHierarchyList:
        """Get paginated list of hierarchy relationships"""
        page = pag or 1
        page_size = 10

        items, total = await get_hierarchy_paginated(db, page, page_size, ord, status)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return RSValuesHierarchyList(
            data=[self._hierarchy_to_response(h) for h in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None,
        )

    @Get("/children/{value_id}", response_model=List[RSValuesHierarchy], status_code=200)
    async def get_value_children(
        self,
        value_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[RSValuesHierarchy]:
        """Get all direct children of a value (where value is the parent)"""
        items = await get_children(db, value_id)
        return [self._hierarchy_to_response(h) for h in items]

    @Get("/parents/{value_id}", response_model=List[RSValuesHierarchy], status_code=200)
    async def get_value_parents(
        self,
        value_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[RSValuesHierarchy]:
        """Get all direct parents of a value (where value is the child)"""
        items = await get_parents(db, value_id)
        return [self._hierarchy_to_response(h) for h in items]

    @Post("/", response_model=RSValuesHierarchy, status_code=201)
    async def create_value_hierarchy(
        self,
        hierarchy: RQValuesHierarchy,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValuesHierarchy:
        """Create a new parent-child hierarchy relationship between values"""
        result = await create_values_hierarchy(db, hierarchy)
        return self._hierarchy_to_response(result)

    @Delete("/id/{id}", status_code=204)
    async def delete_value_hierarchy(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Soft delete a hierarchy relationship"""
        await ValuesHierarchy.delete(db, id)

    @Put("/id/{id}", response_model=RSValuesHierarchy, status_code=200)
    async def update_value_hierarchy(
        self,
        id: str,
        hierarchy: RQValuesHierarchy,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSValuesHierarchy:
        """Update a hierarchy relationship"""
        result = await ValuesHierarchy.update(db, id, hierarchy.model_dump())
        return self._hierarchy_to_response(result)
