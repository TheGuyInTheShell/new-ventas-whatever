from sqlalchemy.ext.asyncio import AsyncSession
from .models import InvoiceTransaction
from .schemas import RQInvoiceTransaction


async def create_invoice_transaction(
    db: AsyncSession,
    data: RQInvoiceTransaction,
) -> InvoiceTransaction:
    obj = InvoiceTransaction(
        ref_invoice=data.ref_invoice,
        ref_transaction=data.ref_transaction,
    )
    await obj.save(db)
    return obj
