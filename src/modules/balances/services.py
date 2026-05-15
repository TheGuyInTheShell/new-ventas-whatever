from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.lib.register.service import Service
from core.lib.decorators.exceptions import handle_service_errors, ServiceResult
from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from .models import Balance
from .schemas import RQBalance, RQUpdateBalance, RSBalance
from .exceptions import BalanceNotFoundError
from src.domain.hooks.balances import trigger_balance_updated


class BalancesService(Service):
    @handle_service_errors
    @injectable
    async def create_balance(
        self, balance_data: RQBalance, db: AsyncSession = Depends(get_async_db)
    ) -> ServiceResult[RSBalance]:
        balance = Balance(
            type=balance_data.type,
            quantity=balance_data.quantity,
            ref_value=balance_data.ref_value,
        )
        db.add(balance)
        await db.commit()
        await db.refresh(balance)
        return RSBalance.model_validate(balance), None

    @handle_service_errors
    @injectable
    @trigger_balance_updated
    async def update_balance(
        self,
        id: int,
        balance_data: RQUpdateBalance,
        db: AsyncSession = Depends(get_async_db),
    ) -> ServiceResult[RSBalance]:
        stmt = select(Balance).where(Balance.id == id)
        result = await db.execute(stmt)
        balance = result.scalar_one_or_none()

        if not balance:
            return None, BalanceNotFoundError(id)

        balance.quantity = balance_data.quantity
        await db.commit()
        await db.refresh(balance)

        return RSBalance.model_validate(balance), None
