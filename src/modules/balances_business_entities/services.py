from sqlalchemy.ext.asyncio import AsyncSession
from .models import BalanceBusinessEntity
from .schemas import RQBalanceBusinessEntity


async def create_balance_business_entity(
    db: AsyncSession,
    data: RQBalanceBusinessEntity,
) -> BalanceBusinessEntity:
    obj = BalanceBusinessEntity(
        ref_business_entity=data.ref_business_entity,
        ref_balance=data.ref_balance,
    )
    await obj.save(db)
    return obj
