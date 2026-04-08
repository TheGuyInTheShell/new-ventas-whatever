from typing import List, Optional, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.invoices.models import Invoice
from src.modules.invoices.schemas import (
    RQInvoice, RSInvoice, RSInvoiceList,
    RQInvoiceBulk, RSInvoiceBulk, RSInvoiceBulkTransaction,
    RQInvoiceFullTransactionBulk,
)
from src.modules.invoices.services import create_invoice, process_invoice_bulk, process_invoice_full_transaction_bulk


class InvoicesController(Controller):
    """
    Controller for Invoices management.
    
    Path: /api/v1/invoices
    """

    @Get("/id/{id}", response_model=RSInvoice, status_code=200)
    async def get_Invoice(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoice:
        try:
            result: Invoice = await Invoice.find_one(db, id)
            return RSInvoice(
                id=result.id,
                uid=result.uid,
                context=result.context,
                name=result.name,
                type=result.type,
                serial=result.serial,
                notes=result.notes,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSInvoiceList, status_code=200)
    async def get_Invoices(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSInvoiceList:
        try:
            current_page = pag or 1
            result = await Invoice.find_some(db, current_page, ord=ord, status=status)
            mapped_result = [
                RSInvoice(
                    id=x.id,
                    uid=x.uid,
                    context=x.context,
                    name=x.name,
                    type=x.type,
                    serial=x.serial,
                    notes=x.notes,
                )
                for x in result
            ]
            total_items = len(mapped_result) # Note: find_some might return a list, but pagination info usually comes from db
            return RSInvoiceList(
                data=mapped_result,
                total=total_items,
                page=current_page,
                page_size=10,
                total_pages=total_items // 10 + 1,
                has_next=current_page < total_items // 10 + 1,
                has_prev=current_page > 1,
                next_page=current_page + 1 if current_page < total_items // 10 + 1 else None,
                prev_page=current_page - 1 if current_page > 1 else None,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSInvoice, status_code=201)
    async def create_Invoice_endpoint(
        self, invoice: RQInvoice, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoice:
        try:
            result = await create_invoice(db, invoice)
            return RSInvoice(
                id=result.id,
                uid=result.uid,
                context=result.context,
                name=result.name,
                type=result.type,
                serial=result.serial,
                notes=result.notes,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/bulk", response_model=RSInvoiceBulk, status_code=201)
    async def create_Invoice_bulk_endpoint(
        self, data: RQInvoiceBulk, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoiceBulk:
        """
        Complex bulk endpoint: create an invoice, link business entities,
        and register N transactions with price snapshots — atomically.
        """
        try:
            result = await process_invoice_bulk(db, data)
            invoice = result.invoice
            transactions = result.transactions
            inverse_transactions = result.inverse_transactions

            def _map_tx(t):
                return RSInvoiceBulkTransaction(
                    id=t.id,
                    uid=t.uid,
                    quantity=t.quantity,
                    operation_type=t.operation_type,
                    reference_code=t.reference_code,
                    ref_inverse_transaction=t.ref_inverse_transaction,
                    ref_balance_from=t.ref_balance_from,
                    ref_balance_to=t.ref_balance_to,
                )

            return RSInvoiceBulk(
                invoice=RSInvoice(
                    id=invoice.id,
                    uid=invoice.uid,
                    context=invoice.context,
                    name=invoice.name,
                    type=invoice.type,
                    serial=invoice.serial,
                    notes=invoice.notes,
                ),
                transactions=[_map_tx(t) for t in transactions],
                inverse_transactions=[_map_tx(t) for t in inverse_transactions],
                linked_business_entity_count=result.linked_business_entity_count,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(e)
            raise e

    @Post("/bulk-full", response_model=RSInvoiceBulk, status_code=201)
    async def create_Invoice_bulk_full_endpoint(
        self, data: RQInvoiceFullTransactionBulk, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoiceBulk:
        """
        Full bulk endpoint: each item carries its own transaction context
        (balances, user, quantities, business entities).
        """
        try:
            return await process_invoice_full_transaction_bulk(db, data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_Invoice(self, id: str, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await Invoice.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSInvoice, status_code=200)
    async def update_Invoice(
        self, id: str, invoice: RQInvoice, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoice:
        try:
            result = await Invoice.update(db, id, invoice.model_dump())
            return RSInvoice(
                id=result.id,
                uid=result.uid,
                context=result.context,
                name=result.name,
                type=result.type,
                serial=result.serial,
                notes=result.notes,
            )
        except Exception as e:
            print(e)
            raise e
