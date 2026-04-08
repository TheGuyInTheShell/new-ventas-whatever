from typing import Literal, Optional, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.business_entities_groups.connection.models import BusinessEntitiesGroupConnection
from src.modules.business_entities_groups.connection.schemas import (
    RQBusinessEntitiesGroupConnection,
    RSBusinessEntitiesGroupConnection,
    RSBusinessEntitiesGroupConnectionList,
)
from src.modules.business_entities_groups.connection.services import (
    create_connection,
    get_connections_by_group,
    get_connections_by_entity,
    get_connections_paginated,
)


class BusinessEntitiesGroupsConnectionController(Controller):
    """
    Controller for Business Entities Groups Connection management.
    
    Path: /api/v1/business_entities_groups/connection
    """

    def _connection_to_response(self, conn: BusinessEntitiesGroupConnection) -> RSBusinessEntitiesGroupConnection:
        """Convert BusinessEntitiesGroupConnection model to response schema"""
        return RSBusinessEntitiesGroupConnection(
            id=conn.id,
            uid=conn.uid,
            ref_business_entities_group=conn.ref_business_entities_group,
            ref_business_entities=conn.ref_business_entities,
        )

    @Get("/id/{id}", response_model=RSBusinessEntitiesGroupConnection, status_code=200)
    async def get_business_entities_group_connection(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroupConnection:
        """Get a single connection by ID or UID"""
        result = await BusinessEntitiesGroupConnection.find_one(db, id)
        return self._connection_to_response(result)

    @Get("/", response_model=RSBusinessEntitiesGroupConnectionList, status_code=200)
    async def get_business_entities_group_connections(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroupConnectionList:
        """Get paginated list of connections"""
        page = pag or 1
        page_size = 10

        items, total = await get_connections_paginated(db, page, page_size, ord, status)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return RSBusinessEntitiesGroupConnectionList(
            data=[self._connection_to_response(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_page=page + 1 if page < total_pages else None,
            prev_page=page - 1 if page > 1 else None,
        )

    @Get("/by-group/{group_id}", response_model=List[RSBusinessEntitiesGroupConnection], status_code=200)
    async def get_business_entities_group_connections_for_group(
        self,
        group_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[RSBusinessEntitiesGroupConnection]:
        """Get all connections for a specific group"""
        items = await get_connections_by_group(db, group_id)
        return [self._connection_to_response(c) for c in items]

    @Get("/by-entity/{entity_id}", response_model=List[RSBusinessEntitiesGroupConnection], status_code=200)
    async def get_business_entities_group_connections_for_entity(
        self,
        entity_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[RSBusinessEntitiesGroupConnection]:
        """Get all connections for a specific business entity"""
        items = await get_connections_by_entity(db, entity_id)
        return [self._connection_to_response(c) for c in items]

    @Post("/", response_model=RSBusinessEntitiesGroupConnection, status_code=201)
    async def create_business_entities_group_connection(
        self,
        connection: RQBusinessEntitiesGroupConnection,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroupConnection:
        """Create a new connection between a business entity and a group"""
        result = await create_connection(db, connection)
        return self._connection_to_response(result)

    @Delete("/id/{id}", status_code=204)
    async def delete_business_entities_group_connection(
        self,
        id: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Soft delete a connection"""
        await BusinessEntitiesGroupConnection.delete(db, id)

    @Put("/id/{id}", response_model=RSBusinessEntitiesGroupConnection, status_code=200)
    async def update_business_entities_group_connection(
        self,
        id: str,
        connection: RQBusinessEntitiesGroupConnection,
        db: AsyncSession = Depends(get_async_db),
    ) -> RSBusinessEntitiesGroupConnection:
        """Update a connection"""
        result = await BusinessEntitiesGroupConnection.update(db, id, connection.model_dump())
        return self._connection_to_response(result)
