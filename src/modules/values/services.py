from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.lib.register.service import Service
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db

from .models import Value
from .meta.models import MetaValue
from .schemas import RQValue, RSValueList, RSValue, RQValueQuery
from .exceptions import (
    ValueNotFoundError,
    ValueCreationError,
    ValueUpdateError,
    ServiceResult,
)
from ..comparison_values.models import ComparisonValue
from src.modules.business_entities.meta.models import (
    MetaBusinessEntity,
)  # Fix mapper initialization
from core.lib.decorators.exceptions import handle_service_errors


class ValuesService(Service):
    @handle_service_errors
    @injectable
    async def create_value_with_meta(
        self, value_data: RQValue, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSValue]:
        """
        Create a new value with optional metadata.
        Also creates a price comparison if provided.
        """
        value = Value(
            name=value_data.name,
            expression=value_data.expression,
            type=value_data.type,
            ref_business_entity=value_data.ref_business_entity,
            identifier=value_data.identifier,
        )
        db.add(value)
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            raise ValueCreationError(f"Failed to create value: {str(e)}")

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
                ref_business_entity=value_data.ref_business_entity,
            )
            db.add(comparison)
            await db.flush()

        # Refresh to get relationships including meta
        stmt = (
            select(Value)
            .options(selectinload(Value.meta), selectinload(Value.balances))
            .where(Value.id == value.id)
        )
        result = await db.execute(stmt)
        refreshed_value = result.scalar_one_or_none()

        if not refreshed_value:
            raise ValueCreationError("Value was created but could not be retrieved.")

        await db.commit()
        await db.refresh(refreshed_value)

        return RSValue.model_validate(refreshed_value), None

    @handle_service_errors
    @injectable
    async def create_values_bulk(
        self, values_data: List[RQValue], db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[List[RSValue]]:
        """
        Create multiple values in bulk with metadata.
        """
        created_values: List[RSValue] = []

        for value_data in values_data:
            value, error = await self.create_value_with_meta(value_data, db=db)
            if error or value is None:
                return None, error
            created_values.append(value)

        return created_values, None

    @handle_service_errors
    @injectable
    async def update_value_with_meta(
        self,
        value_id: int | str,
        value_data: RQValue,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSValue]:
        """
        Update a value and its metadata.
        """
        # Check if exists
        value = await Value.find_one(db, value_id)
        if not value:
            raise ValueNotFoundError(f"Value with id {value_id} not found.")

        # Update main value
        update_data = {"name": value_data.name, "expression": value_data.expression}
        try:
            value = await Value.update(db, value_id, update_data)
        except Exception as e:
            raise ValueUpdateError(f"Failed to update value: {str(e)}")

        # If meta is provided, delete existing and create new
        if value_data.meta is not None:
            # Delete existing meta
            await MetaValue.delete_by_specification(db, specification={"ref_value": value.id})

            # Create new meta
            for meta_item in value_data.meta:
                meta = MetaValue(
                    ref_value=value.id, key=meta_item.key, value=meta_item.value
                )
                await meta.save(db)

        await db.commit()
        await db.refresh(value)
        return RSValue.model_validate(value), None

    @handle_service_errors
    @injectable
    async def get_values_paginated(
        self,
        query: RQValueQuery,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSValueList]:
        """
        Get paginated list of values with total count using the query schema.
        """
        values, total = await Value.query(db, query)

        total_pages = (total + query.page_size - 1) // query.page_size if total > 0 else 1

        return (
            RSValueList(
                data=[RSValue.model_validate(v) for v in values],
                total=total,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages,
                has_prev=query.page > 1,
                has_next=query.page < total_pages,
                next_page=query.page + 1 if query.page < total_pages else None,
                prev_page=query.page - 1 if query.page > 1 else None,
            ),
            None,
        )

    @handle_service_errors
    @injectable
    async def delete_value(
        self, value_id: int | str, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[bool]:
        """
        Delete a value by id.
        """
        value = await Value.find_one(db, value_id)
        if not value:
            raise ValueNotFoundError(f"Value with id {value_id} not found.")

        await Value.delete(db, value_id)
        await db.commit()
        return True, None
