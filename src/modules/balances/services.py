from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import Balance
from .schemas import RQBalance

class BalancesService(Service):
    async def create_balance(
        self,
        db: AsyncSession,
        balance_data: RQBalance
    ) -> Balance:
        balance = Balance(
            currency=balance_data.currency,
            ref_value=balance_data.ref_value
        )
        await balance.save(db)
        return balance

