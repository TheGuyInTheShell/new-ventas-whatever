from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import BalanceBusinessEntity
from .schemas import RQBalanceBusinessEntity

class BalancesBusinessEntitiesService(Service):
    @injectable
    async def create_balance_business_entity(
        self,
        data: RQBalanceBusinessEntity,
        db: AsyncSession = Depends(get_async_db),
    ) -> BalanceBusinessEntity:
        obj = BalanceBusinessEntity(
            ref_business_entity=data.ref_business_entity,
            ref_balance=data.ref_balance,
        )
        await obj.save(db)
        return obj

