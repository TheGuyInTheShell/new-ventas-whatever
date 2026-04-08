from sqlalchemy.ext.asyncio import AsyncSession
from core.lib.register.service import Service
from .models import InvoiceTransaction
from .schemas import RQInvoiceTransaction

class InvoiceTransactionsService(Service):
    async def create_invoice_transaction(
        self,
        db: AsyncSession,
        data: RQInvoiceTransaction,
    ) -> InvoiceTransaction:
        obj = InvoiceTransaction(
            ref_invoice=data.ref_invoice,
            ref_transaction=data.ref_transaction,
        )
        await obj.save(db)
        return obj

