from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING, List, Tuple
from core.lib.register.service import Service

from .models import Invoice
from .schemas import RQInvoice, RSInvoiceBulkTransaction, RSInvoiceBulk, RSInvoice
from ..transactions.models import Transaction
from ..invoice_transactions.models import InvoiceTransaction
from ..invoice_business_entities.models import InvoiceBusinessEntity

if TYPE_CHECKING:
    from .schemas import RQInvoiceBulk, RQInvoiceFullTransactionBulk


class InvoicesService(Service):
    async def create_invoice(
        self,
        db: AsyncSession,
        invoice_data: RQInvoice,
    ) -> Invoice:
        invoice = Invoice(
            context=invoice_data.context,
            name=invoice_data.name,
            type=invoice_data.type,
            serial=invoice_data.serial,
            notes=invoice_data.notes,
        )
        await invoice.save(db)
        return invoice

    async def process_invoice_bulk(
        self,
        db: AsyncSession,
        data: "RQInvoiceBulk",
    ) -> RSInvoiceBulk:
        """
        Atomic operation:
        1. Create Invoice
        2. Link business entities via InvoiceBusinessEntity
        3. For each item: create Transaction with quantity (given) and quantity_to (received) → link InvoiceTransaction
        4. Single commit at the end
        """
        # 1. Create Invoice (no commit yet — we add to session manually)
        invoice = Invoice(
            context=data.context,
            name=data.name,
            type=data.type,
            serial=data.serial,
            notes=data.notes,
        )
        db.add(invoice)
        await db.flush()  # get invoice.id without committing

        # 2. Link business entities
        for be_id in data.business_entity_ids:
            link = InvoiceBusinessEntity(
                ref_invoice=invoice.id,
                ref_business_entity=be_id,
            )
            db.add(link)

        # 3. Process each line item
        transactions = []
        for item in data.items:
            # quantity    = amount given in the exchange
            # quantity_to = amount received in the exchange
            transaction = Transaction(
                quantity=str(item.quantity),
                quantity_to=str(item.quantity_to),
                operation_type=item.operation_type,
                reference_code=data.reference_code,
                ref_by_user=data.ref_by_user,
                ref_balance_from=data.ref_balance_from,
                ref_balance_to=data.ref_balance_to,
            )
            db.add(transaction)
            await db.flush()

            # Link to invoice
            db.add(InvoiceTransaction(ref_invoice=invoice.id, ref_transaction=transaction.id))

            transactions.append(transaction)

        # 4. Single atomic commit
        await db.commit()

        # Refresh all objects
        await db.refresh(invoice)
        for t in transactions:
            await db.refresh(t)

        return RSInvoiceBulk(
            invoice=RSInvoice(
                uid=invoice.uid,
                id=invoice.id,
                context=invoice.context,
                name=invoice.name,
                type=invoice.type,
                serial=invoice.serial,
                notes=invoice.notes,
            ),
            transactions=[RSInvoiceBulkTransaction(
                uid=transaction.uid,
                id=transaction.id,
                quantity=transaction.quantity,
                quantity_to=transaction.quantity_to,
                operation_type=transaction.operation_type,
                reference_code=transaction.reference_code,
                ref_balance_from=transaction.ref_balance_from,
                ref_balance_to=transaction.ref_balance_to,
            ) for transaction in transactions ],
            linked_business_entity_count=len(data.business_entity_ids),
        )

    async def process_invoice_full_transaction_bulk(
        self,
        db: AsyncSession,
        data: "RQInvoiceFullTransactionBulk",
    ) -> RSInvoiceBulk:
        """
        Atomic operation:
        1. Create Invoice (header only)
        2. For each item:
           a. Create transaction with quantity and quantity_to
           b. Link item-level business entities via InvoiceBusinessEntity
           c. Link transaction to invoice via InvoiceTransaction
        3. Single commit at the end
        """
        # 1. Create Invoice header
        invoice = Invoice(
            context=data.context,
            name=data.name,
            type=data.type,
            serial=data.serial,
            notes=data.notes,
        )
        db.add(invoice)
        await db.flush()

        # 2. Process each line item
        transactions = []
        all_be_ids: set[int] = set()

        for item in data.items:
            # Create transaction with both quantities
            transaction = Transaction(
                quantity=str(item.quantity),
                quantity_to=str(item.quantity_to),
                operation_type=item.operation_type,
                reference_code=item.reference_code,
                ref_by_user=item.ref_by_user,
                ref_balance_from=item.ref_balance_from,
                ref_balance_to=item.ref_balance_to,
            )
            db.add(transaction)
            await db.flush()

            # Link transaction to invoice
            db.add(InvoiceTransaction(ref_invoice=invoice.id, ref_transaction=transaction.id))

            # Link item-level business entities
            for be_id in item.business_entity_ids:
                if be_id not in all_be_ids:
                    db.add(InvoiceBusinessEntity(ref_invoice=invoice.id, ref_business_entity=be_id))
                    all_be_ids.add(be_id)

            transactions.append(transaction)

        # 3. Single atomic commit
        await db.commit()

        # Refresh all objects
        await db.refresh(invoice)
        for t in transactions:
            await db.refresh(t)

        return RSInvoiceBulk(
            invoice=RSInvoice(
                uid=invoice.uid,
                id=invoice.id,
                context=invoice.context,
                name=invoice.name,
                type=invoice.type,
                serial=invoice.serial,
                notes=invoice.notes,
            ),
            transactions=[RSInvoiceBulkTransaction(
                uid=t.uid, id=t.id,
                quantity=t.quantity,
                quantity_to=t.quantity_to,
                operation_type=t.operation_type,
                reference_code=t.reference_code,
                ref_balance_from=t.ref_balance_from,
                ref_balance_to=t.ref_balance_to,
            ) for t in transactions],
            linked_business_entity_count=len(all_be_ids),
        )


