from fastapi import Depends
from fastapi_injectable import injectable
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import InvoiceTransaction
from .schemas import RQInvoiceTransaction

class InvoiceTransactionsService(Service):
    @injectable
    async def create_invoice_transaction(
        self,
        data: RQInvoiceTransaction,
        db: AsyncSession = Depends(get_async_db),
    ) -> InvoiceTransaction:
        obj = InvoiceTransaction(
            ref_invoice=data.ref_invoice,
            ref_transaction=data.ref_transaction,
        )
        await obj.save(db)
        return obj

