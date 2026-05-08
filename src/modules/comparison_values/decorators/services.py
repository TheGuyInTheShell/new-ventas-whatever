from typing import List, Optional, Tuple
from fastapi import Depends
from fastapi_injectable import injectable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from core.database import get_async_db
from core.lib.register.service import Service
from core.lib.decorators.exceptions import handle_service_errors

from .models import ComparisonValueDecorator, ComparisonValueDecoratorHistorical
from .schemas import (
    RQComparisonValueDecorator,
    RSComparisonValueDecorator,
    RSComparisonValueDecoratorList,
)
from .exceptions import (
    ComparisonValueDecoratorNotFoundError,
    ComparisonValueDecoratorCreationError,
    ServiceResult,
)


class ComparisonValueDecoratorService(Service):
    @handle_service_errors
    @injectable
    async def create_decorator(
        self,
        data: RQComparisonValueDecorator,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSComparisonValueDecorator]:
        """
        Create or update a decorator for a comparison value relationship.
        """
        # Check if it exists to update
        stmt = select(ComparisonValueDecorator).where(
            ComparisonValueDecorator.ref_comparation_values_from
            == data.ref_comparation_values_from,
            ComparisonValueDecorator.ref_comparation_values_to
            == data.ref_comparation_values_to,
        )
        result = await db.execute(stmt)
        decorator = result.scalar_one_or_none()

        if decorator:
            decorator.comparison_decorators = data.comparison_decorators
        else:
            decorator = ComparisonValueDecorator(
                ref_comparation_values_from=data.ref_comparation_values_from,
                ref_comparation_values_to=data.ref_comparation_values_to,
                comparison_decorators=data.comparison_decorators,
            )
            db.add(decorator)

        try:
            await db.flush()
            await db.commit()
            await db.refresh(decorator)
        except Exception as e:
            await db.rollback()
            raise ComparisonValueDecoratorCreationError(
                f"Failed to save decorator: {str(e)}"
            )

        return RSComparisonValueDecorator.model_validate(decorator), None

    @handle_service_errors
    @injectable
    async def get_decorator_link(
        self,
        from_id: int,
        to_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSComparisonValueDecorator]:
        """
        Retrieve a specific decorator link.
        """
        stmt = select(ComparisonValueDecorator).where(
            ComparisonValueDecorator.ref_comparation_values_from == from_id,
            ComparisonValueDecorator.ref_comparation_values_to == to_id,
        )
        result = await db.execute(stmt)
        decorator = result.scalar_one_or_none()

        if not decorator:
            return None, ComparisonValueDecoratorNotFoundError(from_id, to_id)

        return RSComparisonValueDecorator.model_validate(decorator), None

    @handle_service_errors
    @injectable
    async def delete_decorator(
        self,
        from_id: int,
        to_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[bool]:
        """
        Delete a decorator link.
        """
        stmt = delete(ComparisonValueDecorator).where(
            ComparisonValueDecorator.ref_comparation_values_from == from_id,
            ComparisonValueDecorator.ref_comparation_values_to == to_id,
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            return None, ComparisonValueDecoratorNotFoundError(from_id, to_id)

        return True, None

    @handle_service_errors
    @injectable
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSComparisonValueDecoratorList]:
        """
        Get paginated list of decorators.
        """
        stmt = select(ComparisonValueDecorator)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Pagination
        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        result = await db.execute(stmt)
        items = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return (
            RSComparisonValueDecoratorList(
                data=[RSComparisonValueDecorator.model_validate(i) for i in items],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
            None,
        )
