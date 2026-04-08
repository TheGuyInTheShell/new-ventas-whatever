from fastapi import APIRouter, Depends, Body
from typing import Annotated
from enum import Enum
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.d.schemas.transaction_and_invoice import RQAdjustBalance, InvoiceSales
from src.modules.d.services.transaction_and_invoice import (
    adjust_transaction_and_invoice_service,
    create_transaction_and_invoice_service
)

tags: list[str | Enum] = ["transaction_and_invoice"]
router = APIRouter(tags=tags)


@router.post("/")
async def create_transaction_and_invoice(
    payload: InvoiceSales,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Verify balances -> create a snapshot of comparison values in historical -> create the transaction -> create invoice -> add invoice to business ent.
    """
    return await create_transaction_and_invoice_service(db, payload)


@router.put("/adjust")
async def adjust_transaction_and_invoice(
    payload: RQAdjustBalance,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Adjust an inventory balance globally, optionally creating an Invoice and Transaction for history tracking.
    """
    return await adjust_transaction_and_invoice_service(db, payload)


@router.post("/query")
async def query_transaction_and_invoice(
    payload: dict,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all values with their comparisons.
    """
    return None

