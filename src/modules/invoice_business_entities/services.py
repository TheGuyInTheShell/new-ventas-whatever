from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import InvoiceBusinessEntity
from .schemas import RQInvoiceBusinessEntity

class InvoiceBusinessEntitiesService(Service):
    async def create_invoice_business_entity(
        self,
        db: AsyncSession,
        data: RQInvoiceBusinessEntity,
    ) -> InvoiceBusinessEntity:
        obj = InvoiceBusinessEntity(
            ref_invoice=data.ref_invoice,
            ref_business_entity=data.ref_business_entity,
        )
        await obj.save(db)
        return obj

