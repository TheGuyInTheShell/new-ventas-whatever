from sqlalchemy.ext.asyncio import AsyncSession
from .models import InvoiceBusinessEntity
from .schemas import RQInvoiceBusinessEntity


async def create_invoice_business_entity(
    db: AsyncSession,
    data: RQInvoiceBusinessEntity,
) -> InvoiceBusinessEntity:
    obj = InvoiceBusinessEntity(
        ref_invoice=data.ref_invoice,
        ref_business_entity=data.ref_business_entity,
    )
    await obj.save(db)
    return obj
