from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaTransactionBuffer
from .schemas import RQMetaTransactionBuffer

class TransactionsBufferMetaService(Service):
    async def create_meta_transaction_buffer(
        self,
        db: AsyncSession,
        meta: RQMetaTransactionBuffer,
    ) -> MetaTransactionBuffer:
        meta_obj = MetaTransactionBuffer(**meta.model_dump())
        await meta_obj.save(db)
        return meta_obj

