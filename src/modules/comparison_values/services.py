from typing import Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.lib.register.service import Service
from fastapi import Depends
from fastapi_injectable import injectable
from core.lib.decorators.exceptions import handle_service_errors
from .exceptions import (
    ServiceResult,
    ComparisonValueNotFoundError,
    ValueNotFoundError,
    ComparisonRateNotFoundError,
)
from core.database import get_async_db

from .models import ComparisonValue
from .historical import ComparisonValueHistorical
from .schemas import (
    RQComparisonValue,
    RSComparisonValue,
    RSComparisonValueList,
    RSConvert,
    RSComparisonValueSimple,
)
from ..values.models import Value
from .meta.models import MetaComparisonValue
from src.modules.business_entities.meta.models import (
    MetaBusinessEntity,
)  # Fix mapper initialization


class ComparisonValuesService(Service):
    async def _create_comparison(
        self, data: RQComparisonValue, db: AsyncSession
    ) -> RSComparisonValue:
        """Internal procedural method to create a comparison"""
        # Check if it exists (even if deleted) to handle UniqueConstraint conflicts
        stmt = select(ComparisonValue).where(
            ComparisonValue.value_from == data.value_from,
            ComparisonValue.value_to == data.value_to,
            ComparisonValue.ref_business_entity == data.ref_business_entity,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Restore and update
            update_data = {
                "quantity_from": data.quantity_from,
                "quantity_to": data.quantity_to,
                "is_deleted": False,
                "deleted_at": None,
            }
            await ComparisonValue.update(db, existing.id, update_data)
            comparison_id = existing.id
        else:
            comparison = ComparisonValue(
                quantity_from=data.quantity_from,
                quantity_to=data.quantity_to,
                value_from=data.value_from,
                value_to=data.value_to,
                ref_business_entity=data.ref_business_entity,
            )
            await comparison.save(db)
            comparison_id = comparison.id

        if data.meta:
            for m in data.meta:
                meta_item = MetaComparisonValue(
                    key=m.key, value=m.value, ref_comparison_value=comparison_id
                )
                await meta_item.save(db)

        # Eager load relationships
        stmt = (
            select(ComparisonValue)
            .options(
                selectinload(ComparisonValue.source_value),
                selectinload(ComparisonValue.target_value),
            )
            .where(ComparisonValue.id == comparison_id)
        )

        result = await db.execute(stmt)
        comparison = result.scalar_one()

        return RSComparisonValue.model_validate(comparison)

    @handle_service_errors
    @injectable
    async def create_comparison(
        self, data: RQComparisonValue, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSComparisonValue]:
        """Public entry point for creating a comparison"""
        return await self._create_comparison(data, db), None

    async def _update_comparison(
        self, comparison_id: int | str, data: RQComparisonValue, db: AsyncSession
    ) -> RSComparisonValue:
        """Internal procedural method to update a comparison"""
        # Fetch existing comparison to check for changes and snapshot if needed
        comparison = await ComparisonValue.find_one(db, comparison_id)
        if not comparison:
            raise ComparisonValueNotFoundError()

        # Check if price (quantity_to) has changed
        if float(comparison.quantity_to) != float(data.quantity_to):
            await self.create_historical_snapshot(comparison, db=db)

        update_data = {
            "quantity_from": data.quantity_from,
            "quantity_to": data.quantity_to,
            "value_from": data.value_from,
            "value_to": data.value_to,
            "ref_business_entity": data.ref_business_entity,
        }
        await ComparisonValue.update(db, comparison_id, update_data)

        # Eager load relationships for the updated item
        stmt = (
            select(ComparisonValue)
            .options(
                selectinload(ComparisonValue.source_value),
                selectinload(ComparisonValue.target_value),
            )
            .where(ComparisonValue.id == comparison.id)
        )

        result = await db.execute(stmt)
        return RSComparisonValue.model_validate(result.scalar_one())

    @handle_service_errors
    @injectable
    async def update_comparison(
        self,
        comparison_id: int | str,
        data: RQComparisonValue,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSComparisonValue]:
        """Public entry point for updating a comparison"""
        return await self._update_comparison(comparison_id, data, db), None

    @handle_service_errors
    @injectable
    async def get_comparisons_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str = "id",
        order: str = "asc",
        status: Literal["exists", "deleted", "all"] = "exists",
        value_from: Optional[int | str] = None,
        value_to: Optional[int | str] = None,
        ref_business_entity: Optional[int] = None,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSComparisonValueList]:
        """Get paginated list of comparisons with total count"""
        # Build filters dict, only include non-None values
        filters = {}
        if value_from is not None:
            filters["value_from"] = value_from
        if value_to is not None:
            filters["value_to"] = value_to
        if ref_business_entity is not None:
            filters["ref_business_entity"] = ref_business_entity

        comparisons = await ComparisonValue.find_some(
            db, pag=page, order_by=order_by, ord=order, status=status, filters=filters
        )

        total = await ComparisonValue.count(db, status=status)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return (
            RSComparisonValueList(
                data=[RSComparisonValue.model_validate(c) for c in comparisons],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
                next_page=page + 1 if page < total_pages else None,
                prev_page=page - 1 if page > 1 else None,
            ),
            None,
        )

    @injectable
    async def find_comparison_rate(
        self,
        from_value_id: int,
        to_value_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> tuple[float, bool]:
        """
        Find the conversion rate between two values.
        Returns (rate, is_direct) tuple or raises ComparisonRateNotFoundError if not found.
        is_direct=True means from->to exists, False means to->from exists (inverse).
        """
        # Try direct comparison
        query = select(ComparisonValue).where(
            ComparisonValue.value_from == from_value_id,
            ComparisonValue.value_to == to_value_id,
            ComparisonValue.is_deleted == False,
        )
        result = (await db.execute(query)).scalar_one_or_none()

        if result:
            rate = result.quantity_to / result.quantity_from
            return (rate, True)

        # Try inverse comparison
        query = select(ComparisonValue).where(
            ComparisonValue.value_from == to_value_id,
            ComparisonValue.value_to == from_value_id,
            ComparisonValue.is_deleted == False,
        )
        result = (await db.execute(query)).scalar_one_or_none()

        if result:
            # Inverse rate: if 1 USD = 46 VES, then 1 VES = 1/46 USD
            rate = result.quantity_from / result.quantity_to
            return (rate, False)

        raise ComparisonRateNotFoundError()

    @handle_service_errors
    @injectable
    async def convert_value(
        self,
        from_value_id: int,
        to_value_id: int,
        amount: float,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSConvert]:
        """
        Convert an amount from one value to another.
        Returns conversion details or raises ComparisonRateNotFoundError if no rate found.
        """
        # Get the values
        from_value = await Value.find_one(db, from_value_id)
        if not from_value:
            raise ValueNotFoundError(f"Source value with ID {from_value_id} not found.")

        to_value = await Value.find_one(db, to_value_id)
        if not to_value:
            raise ValueNotFoundError(f"Target value with ID {to_value_id} not found.")

        # Find the rate (will raise if not found)
        rate, _ = await self.find_comparison_rate(from_value_id, to_value_id, db=db)

        converted_amount = amount * rate

        return (
            RSConvert(
                from_value=RSComparisonValueSimple.model_validate(from_value),
                to_value=RSComparisonValueSimple.model_validate(to_value),
                original_amount=amount,
                converted_amount=converted_amount,
                rate=rate,
                inverse_rate=1 / rate if rate != 0 else 0,
            ),
            None,
        )

    @injectable
    async def create_historical_snapshot(
        self, comparison: ComparisonValue, db: AsyncSession = Depends(get_async_db)
    ) -> ComparisonValueHistorical:
        """Create a historical snapshot from a comparison value"""
        historical = ComparisonValueHistorical(
            quantity_from=comparison.quantity_from,
            quantity_to=comparison.quantity_to,
            value_from=comparison.value_from,
            value_to=comparison.value_to,
            ref_business_entity=comparison.ref_business_entity,
            original_comparison_id=comparison.id,
        )
        await historical.save(db)
        return historical
