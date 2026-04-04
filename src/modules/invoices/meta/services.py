from sqlalchemy.ext.asyncio import AsyncSession

from .models import MetaInvoice
from .schemas import RQMetaInvoice


async def create_meta_invoice(
    db: AsyncSession,
    meta: RQMetaInvoice,
) -> MetaInvoice:
    meta_obj = MetaInvoice(**meta.model_dump())
    await meta_obj.save(db)
    return meta_obj
