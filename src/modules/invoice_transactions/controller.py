from typing import List, Optional, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import InvoiceTransaction
from .schemas import RQInvoiceTransaction, RSInvoiceTransaction, RSInvoiceTransactionList
from .services import create_invoice_transaction

# prefix /invoice_transactions
router = APIRouter()

tag = "invoice_transactions"


@router.get("/id/{id}", response_model=RSInvoiceTransaction, status_code=200, tags=[tag])
async def get_InvoiceTransaction(
    id: str, db: AsyncSession = Depends(get_async_db)
) -> RSInvoiceTransaction:
    try:
        result = await InvoiceTransaction.find_one(db, id)
        return RSInvoiceTransaction(
            id=result.id, uid=result.uid,
            ref_invoice=result.ref_invoice,
            ref_transaction=result.ref_transaction,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSInvoiceTransactionList, status_code=200, tags=[tag])
async def get_InvoiceTransactions(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSInvoiceTransactionList:
    try:
        result = await InvoiceTransaction.find_some(db, pag or 1, ord=ord, status=status)
        mapped_result = [
            RSInvoiceTransaction(
                id=x.id, uid=x.uid,
                ref_invoice=x.ref_invoice,
                ref_transaction=x.ref_transaction,
            )
            for x in result
        ]
        return RSInvoiceTransactionList(
            data=mapped_result,
            total=0, page=0, page_size=0, total_pages=0,
            has_next=False, has_prev=False, next_page=0, prev_page=0,
        )
    except Exception as e:
        print(e)
        raise e


@router.post("/", response_model=RSInvoiceTransaction, status_code=201, tags=[tag])
async def create_InvoiceTransaction_endpoint(
    data: RQInvoiceTransaction, db: AsyncSession = Depends(get_async_db)
) -> RSInvoiceTransaction:
    try:
        result = await create_invoice_transaction(db, data)
        return RSInvoiceTransaction(
            id=result.id, uid=result.uid,
            ref_invoice=result.ref_invoice,
            ref_transaction=result.ref_transaction,
        )
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_InvoiceTransaction(id: str, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await InvoiceTransaction.delete(db, id)
    except Exception as e:
        print(e)
        raise e
