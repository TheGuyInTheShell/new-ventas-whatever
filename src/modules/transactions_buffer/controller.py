from typing import List, Optional, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import TransactionBuffer
from .schemas import RQTransactionBuffer, RSTransactionBuffer, RSTransactionBufferList
from .services import create_transaction_buffer

# prefix /transactions_buffer
router = APIRouter()

tag = "transactions_buffer"


@router.get("/id/{id}", response_model=RSTransactionBuffer, status_code=200, tags=[tag])
async def get_TransactionBuffer(
    id: str, db: AsyncSession = Depends(get_async_db)
) -> RSTransactionBuffer:
    try:
        result = await TransactionBuffer.find_one(db, id)
        return RSTransactionBuffer(
            id=result.id, uid=result.uid,
            quantity=result.quantity,
            operation_type=result.operation_type,
            state=result.state,
            trigger=result.trigger,
            ref_inverse_transaction=result.ref_inverse_transaction,
            ref_by_user=result.ref_by_user,
            ref_balance_from=result.ref_balance_from,
            ref_balance_to=result.ref_balance_to,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSTransactionBufferList, status_code=200, tags=[tag])
async def get_TransactionBuffers(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSTransactionBufferList:
    try:
        result = await TransactionBuffer.find_some(db, pag or 1, ord=ord, status=status)
        mapped_result = [
            RSTransactionBuffer(
                id=x.id, uid=x.uid,
                quantity=x.quantity,
                operation_type=x.operation_type,
                state=x.state,
                trigger=x.trigger,
                ref_inverse_transaction=x.ref_inverse_transaction,
                ref_by_user=x.ref_by_user,
                ref_balance_from=x.ref_balance_from,
                ref_balance_to=x.ref_balance_to,
            )
            for x in result
        ]
        return RSTransactionBufferList(
            data=mapped_result,
            total=0, page=0, page_size=0, total_pages=0,
            has_next=False, has_prev=False, next_page=0, prev_page=0,
        )
    except Exception as e:
        print(e)
        raise e


@router.post("/", response_model=RSTransactionBuffer, status_code=201, tags=[tag])
async def create_TransactionBuffer_endpoint(
    data: RQTransactionBuffer, db: AsyncSession = Depends(get_async_db)
) -> RSTransactionBuffer:
    try:
        result = await create_transaction_buffer(db, data)
        return RSTransactionBuffer(
            id=result.id, uid=result.uid,
            quantity=result.quantity,
            operation_type=result.operation_type,
            state=result.state,
            trigger=result.trigger,
            ref_inverse_transaction=result.ref_inverse_transaction,
            ref_by_user=result.ref_by_user,
            ref_balance_from=result.ref_balance_from,
            ref_balance_to=result.ref_balance_to,
        )
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_TransactionBuffer(
    id: str, db: AsyncSession = Depends(get_async_db)
) -> None:
    try:
        await TransactionBuffer.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSTransactionBuffer, status_code=200, tags=[tag])
async def update_TransactionBuffer(
    id: str, data: RQTransactionBuffer, db: AsyncSession = Depends(get_async_db)
) -> RSTransactionBuffer:
    try:
        result = await TransactionBuffer.update(db, id, data.model_dump())
        return RSTransactionBuffer(
            id=result.id, uid=result.uid,
            quantity=result.quantity,
            operation_type=result.operation_type,
            state=result.state,
            trigger=result.trigger,
            ref_inverse_transaction=result.ref_inverse_transaction,
            ref_by_user=result.ref_by_user,
            ref_balance_from=result.ref_balance_from,
            ref_balance_to=result.ref_balance_to,
        )
    except Exception as e:
        print(e)
        raise e
