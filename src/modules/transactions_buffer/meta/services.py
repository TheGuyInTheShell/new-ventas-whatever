from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaTransactionBuffer
from .schemas import RQMetaTransactionBuffer

class TransactionsBufferMetaService(Service):
    @injectable
    async def create_meta_transaction_buffer(
        self,
        meta: RQMetaTransactionBuffer,
        db: AsyncSession = Depends(get_async_db),
    ) -> MetaTransactionBuffer:
        meta_obj = MetaTransactionBuffer(**meta.model_dump())
        await meta_obj.save(db)
        return meta_obj

