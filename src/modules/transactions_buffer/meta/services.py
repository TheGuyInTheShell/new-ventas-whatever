from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaTransactionBuffer
from .schemas import RQMetaTransactionBuffer


async def create_meta_transaction_buffer(
    db: AsyncSession,
    meta: RQMetaTransactionBuffer,
) -> MetaTransactionBuffer:
    meta_obj = MetaTransactionBuffer(**meta.model_dump())
    await meta_obj.save(db)
    return meta_obj
