from sqlalchemy.ext.asyncio import AsyncSession
from .models import Balance
from .schemas import RQBalance

async def create_balance(
    db: AsyncSession,
    balance_data: RQBalance
) -> Balance:
    balance = Balance(
        currency=balance_data.currency,
        ref_value=balance_data.ref_value
    )
    await balance.save(db)
    return balance
