from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import TransactionBuffer
from .schemas import RQTransactionBuffer

class TransactionsBufferService(Service):
    @injectable
    async def create_transaction_buffer(
        self,
        data: RQTransactionBuffer,
        db: AsyncSession = Depends(get_async_db),
    ) -> TransactionBuffer:
        obj = TransactionBuffer(
            quantity=data.quantity,
            operation_type=data.operation_type,
            state=data.state,
            trigger=data.trigger,
            ref_inverse_transaction=data.ref_inverse_transaction,
            ref_by_user=data.ref_by_user,
            ref_balance_from=data.ref_balance_from,
            ref_balance_to=data.ref_balance_to,
        )
        await obj.save(db)
        return obj

