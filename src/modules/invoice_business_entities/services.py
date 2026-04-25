from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import InvoiceBusinessEntity
from .schemas import RQInvoiceBusinessEntity

class InvoiceBusinessEntitiesService(Service):
    @injectable
    async def create_invoice_business_entity(
        self,
        data: RQInvoiceBusinessEntity,
        db: AsyncSession = Depends(get_async_db),
    ) -> InvoiceBusinessEntity:
        obj = InvoiceBusinessEntity(
            ref_invoice=data.ref_invoice,
            ref_business_entity=data.ref_business_entity,
        )
        await obj.save(db)
        return obj

