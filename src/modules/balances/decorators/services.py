from typing import List, Optional
from fastapi import Depends
from fastapi_injectable import injectable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from core.database import get_async_db
from core.lib.register.service import Service
from core.lib.decorators.exceptions import handle_service_errors

from .models import BalanceDecorator
from .schemas import (
    CreateBalanceDecorator,
    BalanceDecorator as BalanceDecoratorSchema,
    BalanceDecoratorPagination,
)
from .exceptions import (
    BalanceDecoratorNotFoundError,
    BalanceDecoratorCreationError,
    ServiceResult,
)


class BalanceDecoratorService(Service):
    async def _create_decorator(
        self,
        data: CreateBalanceDecorator,
        db: AsyncSession,
    ) -> BalanceDecoratorSchema:
        """
        Internal procedural method to create or update a balance decorator.
        """
        stmt = select(BalanceDecorator).where(
            BalanceDecorator.ref_balance_from == data.ref_balance_from,
            BalanceDecorator.ref_balance_to == data.ref_balance_to,
        )
        result = await db.execute(stmt)
        decorator = result.scalar_one_or_none()

        if decorator:
            decorator.balance_decorators = data.balance_decorators
            decorator.is_reactive = data.is_reactive
        else:
            decorator = BalanceDecorator(
                ref_balance_from=data.ref_balance_from,
                ref_balance_to=data.ref_balance_to,
                balance_decorators=data.balance_decorators,
                is_reactive=data.is_reactive,
            )
            db.add(decorator)

        try:
            await db.flush()
        except Exception as e:
            raise BalanceDecoratorCreationError(
                f"Failed to save decorator: {str(e)}"
            )

        # Get refreshed relationship if needed
        stmt = select(BalanceDecorator).where(
            BalanceDecorator.ref_balance_from == decorator.ref_balance_from,
            BalanceDecorator.ref_balance_to == decorator.ref_balance_to,
        )
        result = await db.execute(stmt)
        decorator = result.scalar_one()

        return BalanceDecoratorSchema.model_validate(decorator)

    @handle_service_errors
    @injectable
    async def create_decorator(
        self,
        data: CreateBalanceDecorator,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[BalanceDecoratorSchema]:
        """
        Public entry point to create or update a balance decorator.
        """
        decorator = await self._create_decorator(data, db)
        await db.commit()
        return decorator, None

    @handle_service_errors
    @injectable
    async def get_decorator_link(
        self,
        from_id: int,
        to_id: int,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[BalanceDecoratorSchema]:
        """
        Retrieve a specific decorator link.
        """
        stmt = select(BalanceDecorator).where(
            BalanceDecorator.ref_balance_from == from_id,
            BalanceDecorator.ref_balance_to == to_id,
        )
        result = await db.execute(stmt)
        decorator = result.scalar_one_or_none()

        if not decorator:
            return None, BalanceDecoratorNotFoundError(from_id, to_id)

        return BalanceDecoratorSchema.model_validate(decorator), None

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
        stmt = delete(BalanceDecorator).where(
            BalanceDecorator.ref_balance_from == from_id,
            BalanceDecorator.ref_balance_to == to_id,
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            return None, BalanceDecoratorNotFoundError(from_id, to_id)

        return True, None

    @handle_service_errors
    @injectable
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[BalanceDecoratorPagination]:
        """
        Get paginated list of decorators.
        """
        stmt = select(BalanceDecorator)

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
            BalanceDecoratorPagination(
                data=[BalanceDecoratorSchema.model_validate(i) for i in items],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
            None,
        )
