from typing import Literal, Optional, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.business_entities.hierarchy.models import BusinessEntitiesHierarchy
from src.modules.business_entities.hierarchy.schemas import (
    RQBusinessEntitiesHierarchy,
    RSBusinessEntitiesHierarchy,
    RSBusinessEntitiesHierarchyList,
)
from src.modules.business_entities.hierarchy.services import (
    create_entity_hierarchy,
    get_children,
    get_parents,
    get_hierarchy_paginated,
)


class BusinessEntitiesHierarchyController(Controller):
    """
    Controller for Business Entities Hierarchy management.
    
    Path: /api/v1/business_entities/hierarchy
    """

    def _hierarchy_to_response(self, h: BusinessEntitiesHierarchy) -> RSBusinessEntitiesHierarchy:
        """Convert BusinessEntitiesHierarchy model to response schema"""
        return RSBusinessEntitiesHierarchy(
            id=h.id,
            uid=h.uid,
            ref_entity_top=h.ref_entity_top,
            ref_entity_bottom=h.ref_entity_bottom,
        )

    @Get("/id/{id}", response_model=RSBusinessEntitiesHierarchy, status_code=200)
    async def get_business_entities_hierarchy(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesHierarchy:
        """Get a single hierarchy relationship by ID or UID"""
        result = await BusinessEntitiesHierarchy.find_one(db, id)
        return self._hierarchy_to_response(result)

    @Get("/", response_model=RSBusinessEntitiesHierarchyList, status_code=200)
    async def get_business_entities_hierarchies(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesHierarchyList:
        """Get paginated list of hierarchy relationships"""
        page = pag or 1
        page_size = 10

        items, total = await get_hierarchy_paginated(db, page, page_size, ord, status)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return RSBusinessEntitiesHierarchyList(
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

    @Get("/children/{entity_id}", response_model=List[RSBusinessEntitiesHierarchy], status_code=200)
    async def get_business_entities_hierarchy_children(
        self,
        entity_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[RSBusinessEntitiesHierarchy]:
        """Get all direct children of a business entity (where entity is the parent)"""
        items = await get_children(db, entity_id)
        return [self._hierarchy_to_response(h) for h in items]

    @Get("/parents/{entity_id}", response_model=List[RSBusinessEntitiesHierarchy], status_code=200)
    async def get_business_entities_hierarchy_parents(
        self,
        entity_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[RSBusinessEntitiesHierarchy]:
        """Get all direct parents of a business entity (where entity is the child)"""
        items = await get_parents(db, entity_id)
        return [self._hierarchy_to_response(h) for h in items]

    @Post("/", response_model=RSBusinessEntitiesHierarchy, status_code=201)
    async def create_business_entities_hierarchy(
        self,
        hierarchy: RQBusinessEntitiesHierarchy,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesHierarchy:
        """Create a new parent-child hierarchy relationship between entities"""
        result = await create_entity_hierarchy(db, hierarchy)
        return self._hierarchy_to_response(result)

    @Delete("/id/{id}", status_code=204)
    async def delete_business_entities_hierarchy(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Soft delete a hierarchy relationship"""
        await BusinessEntitiesHierarchy.delete(db, id)

    @Put("/id/{id}", response_model=RSBusinessEntitiesHierarchy, status_code=200)
    async def update_business_entities_hierarchy(
        self,
        id: str,
        hierarchy: RQBusinessEntitiesHierarchy,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesHierarchy:
        """Update a hierarchy relationship"""
        result = await BusinessEntitiesHierarchy.update(db, id, hierarchy.model_dump())
        return self._hierarchy_to_response(result)
