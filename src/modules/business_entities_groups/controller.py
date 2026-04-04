from typing import Literal, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import BusinessEntitiesGroup
from .schemas import (
    RQBusinessEntitiesGroup,
    RSBusinessEntitiesGroup,
    RSBusinessEntitiesGroupList,
)
from .services import (
    create_business_entities_group,
    update_business_entities_group,
    get_groups_paginated,
)

# prefix /business_entities_groups (auto-registered)
router = APIRouter()

tag = "business_entities_groups"


def group_to_response(group: BusinessEntitiesGroup) -> RSBusinessEntitiesGroup:
    """Convert BusinessEntitiesGroup model to response schema"""
    return RSBusinessEntitiesGroup(
        id=group.id,
        uid=group.uid,
        name=group.name,
        description=group.description,
    )


@router.get("/id/{id}", response_model=RSBusinessEntitiesGroup, status_code=200, tags=[tag])
async def get_group(
    id: str,
    db: AsyncSession = Depends(get_async_db),
) -> RSBusinessEntitiesGroup:
    """Get a single business entities group by ID or UID"""
    result = await BusinessEntitiesGroup.find_one(db, id)
    return group_to_response(result)


@router.get("/", response_model=RSBusinessEntitiesGroupList, status_code=200, tags=[tag])
async def get_groups(
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
        data=[group_to_response(g) for g in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None,
    )


@router.get("/all", response_model=RSBusinessEntitiesGroupList, status_code=200, tags=[tag])
async def get_all_groups(
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSBusinessEntitiesGroupList:
    """Get all business entities groups without pagination"""
    result = await BusinessEntitiesGroup.find_all(db, status)

    return RSBusinessEntitiesGroupList(
        data=[group_to_response(g) for g in result],
        total=len(result),
        page=1,
        page_size=len(result),
        total_pages=1,
        has_next=False,
        has_prev=False,
        next_page=None,
        prev_page=None,
    )


@router.post("/", response_model=RSBusinessEntitiesGroup, status_code=201, tags=[tag])
async def create_group(
    group: RQBusinessEntitiesGroup,
    db: AsyncSession = Depends(get_async_db),
) -> RSBusinessEntitiesGroup:
    """Create a new business entities group"""
    result = await create_business_entities_group(db, group)
    return group_to_response(result)


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_group(
    id: str,
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Soft delete a business entities group"""
    await BusinessEntitiesGroup.delete(db, id)


@router.put("/id/{id}", response_model=RSBusinessEntitiesGroup, status_code=200, tags=[tag])
async def update_group(
    id: str,
    group: RQBusinessEntitiesGroup,
    db: AsyncSession = Depends(get_async_db),
) -> RSBusinessEntitiesGroup:
    """Update a business entities group"""
    result = await update_business_entities_group(db, id, group)
    return group_to_response(result)