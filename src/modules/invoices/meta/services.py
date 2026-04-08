from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import MetaInvoice
from .schemas import RQMetaInvoice

class InvoicesMetaService(Service):
    async def create_meta_invoice(
        self,
        db: AsyncSession,
        meta: RQMetaInvoice,
    ) -> MetaInvoice:
        meta_obj = MetaInvoice(**meta.model_dump())
        await meta_obj.save(db)
        return meta_obj

