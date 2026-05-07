from typing import List, Tuple
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.lib.register.service import Service

from .models import BusinessEntitiesGroupConnection
from .schemas import RQBusinessEntitiesGroupConnection

class BusinessEntitiesGroupConnectionService(Service):
    @injectable
    async def create_connection(
        self,
        data: RQBusinessEntitiesGroupConnection,
        db: AsyncSession = Depends(get_async_db),
    ) -> BusinessEntitiesGroupConnection:
        """
        Create a new connection between a business entity and a group.
        """
        connection = BusinessEntitiesGroupConnection(
            ref_business_entities_group=data.ref_business_entities_group,
            ref_business_entities=data.ref_business_entities,
        )
        db.add(connection)
        await db.flush()
        await db.refresh(connection)
        return connection

    @injectable
    async def get_connections_by_group(
        self,
        group_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[BusinessEntitiesGroupConnection]:
        """
        Get all connections for a specific group.
        """
        stmt = (
            select(BusinessEntitiesGroupConnection)
            .where(BusinessEntitiesGroupConnection.ref_business_entities_group == group_id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @injectable
    async def get_connections_by_entity(
        self,
        entity_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> List[BusinessEntitiesGroupConnection]:
        """
        Get all connections for a specific business entity.
        """
        stmt = (
            select(BusinessEntitiesGroupConnection)
            .where(BusinessEntitiesGroupConnection.ref_business_entities == entity_id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @injectable
    async def get_connections_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order: str = "asc",
        status: str = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> Tuple[List[BusinessEntitiesGroupConnection], int]:
        """
        Get paginated list of connections with total count.
        """
        stmt = select(BusinessEntitiesGroupConnection)

        stmt = select(BusinessEntitiesGroupConnection)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Ordering
        if order == "desc":
            stmt = stmt.order_by(BusinessEntitiesGroupConnection.ref_business_entities_group.desc())
        else:
            stmt = stmt.order_by(BusinessEntitiesGroupConnection.ref_business_entities_group.asc())

        # Pagination
        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

