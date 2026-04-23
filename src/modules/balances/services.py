from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from fastapi import Depends
from fastapi_injectable import injectable
from core.lib.database import get_async_db
from .models import Balance
from .schemas import RQBalance

class BalancesService(Service):
    @injectable
    async def create_balance(
        self,
        balance_data: RQBalance,
        db: AsyncSession = Depends(get_async_db)
    ) -> Balance:
        balance = Balance(
            currency=balance_data.currency,
            ref_value=balance_data.ref_value
        )
        await balance.save(db)
        return balance

