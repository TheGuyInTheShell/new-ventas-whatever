from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.lib.register.service import Service
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db

from .models import Value
from .meta.models import MetaValue
from .schemas import RQValue, RQMetaValue
from ..comparison_values.models import ComparisonValue


class ValuesService(Service):
    @injectable
    async def create_value_with_meta(
        self, value_data: RQValue, db: AsyncSession = Depends(get_async_db)
    ) -> Value:
        """
        Create a new value with optional metadata.
        Also creates a price comparison if provided.
        """
        value = Value(
            name=value_data.name,
            expression=value_data.expression,
            type=value_data.type,
            context=value_data.context,
            identifier=value_data.identifier,
        )
        db.add(value)
        await db.flush()

        # Create metadata if provided
        if value_data.meta:
            for meta_item in value_data.meta:
                meta = MetaValue(
                    ref_value=value.id, key=meta_item.key, value=meta_item.value
                )
                db.add(meta)
            await db.flush()

        # Create price comparison if provided
        if value_data.price is not None and value_data.currency_id is not None:
            comparison = ComparisonValue(
                quantity_from=1,
                quantity_to=value_data.price,
                value_from=value.id,  # The item we just created
                value_to=value_data.currency_id,  # The currency (e.g. USD)
            )
            db.add(comparison)
            await db.flush()

        # Refresh to get relationships including meta
        stmt = (
            select(Value).options(selectinload(Value.meta)).where(Value.id == value.id)
        )
        result = await db.execute(stmt)
        value = result.scalar_one()

        await db.commit()
        await db.refresh(value)
        return value

    @injectable
    async def create_values_bulk(
        self, values_data: List[RQValue], db: AsyncSession = Depends(get_async_db)
    ) -> List[Value]:
        """
        Create multiple values in bulk with metadata.
        """
        created_values = []

        for value_data in values_data:
            value = await self.create_value_with_meta(value_data)
            created_values.append(value)

        return created_values

    @injectable
    async def update_value_with_meta(
        self,
        value_id: int | str,
        value_data: RQValue,
        db: AsyncSession = Depends(get_async_db),
    ) -> Value:
        """
        Update a value and its metadata.
        """
        # Update main value
        update_data = {"name": value_data.name, "expression": value_data.expression}
        value = await Value.update(db, value_id, update_data)

        # If meta is provided, delete existing and create new
        if value_data.meta is not None:
            # Delete existing meta
            existing_meta = await MetaValue.find_all(
                db, status="exists", filters={"ref_value": value.id}
            )
            for meta in existing_meta:
                await MetaValue.delete(db, meta.id)

            # Create new meta
            for meta_item in value_data.meta:
                meta = MetaValue(
                    ref_value=value.id, key=meta_item.key, value=meta_item.value
                )
                await meta.save(db)

        await db.commit()
        await db.refresh(value)
        return value

    @injectable
    async def get_values_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str = "id",
        order: str = "asc",
        filters: Optional[dict] = None,
        db: AsyncSession = Depends(get_async_db),
    ) -> Tuple[List[Value], int]:
        """
        Get paginated list of values with total count.
        """
        values = await Value.find_some(
            db,
            pag=page,
            order_by=order_by,
            ord=order,
            status="exists",
            filters=filters or {},
        )
        # Count total matching filters
        all_values = await Value.find_all(db, status="exists", filters=filters or {})
        total = len(all_values)

        return values, total
