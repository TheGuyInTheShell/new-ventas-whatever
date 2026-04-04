from typing import Literal, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import MetaTransactionBuffer
from .schemas import (
    RQMetaTransactionBuffer,
    RSMetaTransactionBuffer,
    RSMetaTransactionBufferList,
)

# prefix /transactions_buffer/meta
router = APIRouter()

tag = "meta"


@router.get("/id/{id}", response_model=RSMetaTransactionBuffer, status_code=200, tags=[tag])
async def get_meta(
    id: str | int, db: AsyncSession = Depends(get_async_db)
) -> RSMetaTransactionBuffer:
    try:
        result = await MetaTransactionBuffer.find_one(db, id)
        return RSMetaTransactionBuffer(
            id=result.id, uid=result.uid,
            key=result.key, value=result.value,
            ref_transaction_buffer=result.ref_transaction_buffer,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSMetaTransactionBufferList, status_code=200, tags=[tag])
async def get_metas(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSMetaTransactionBufferList:
    try:
        result = await MetaTransactionBuffer.find_some(db, pag or 1, ord=ord, status=status)
        mapped_result = list(map(
            lambda x: RSMetaTransactionBuffer(
                id=x.id, uid=x.uid,
                key=x.key, value=x.value,
                ref_transaction_buffer=x.ref_transaction_buffer,
            ),
            result,
        ))
        return RSMetaTransactionBufferList(
            data=mapped_result,
            total=0, page=0, page_size=0, total_pages=0,
            has_next=False, has_prev=False, next_page=0, prev_page=0,
        )
    except Exception as e:
        print(e)
        raise e


@router.post("/", response_model=RSMetaTransactionBuffer, status_code=201, tags=[tag])
async def create_meta(
    meta: RQMetaTransactionBuffer, db: AsyncSession = Depends(get_async_db)
) -> RSMetaTransactionBuffer:
    try:
        result = await MetaTransactionBuffer(**meta.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_meta(id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await MetaTransactionBuffer.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSMetaTransactionBuffer, status_code=200, tags=[tag])
async def update_meta(
    id: str | int, meta: RQMetaTransactionBuffer, db: AsyncSession = Depends(get_async_db)
) -> RSMetaTransactionBuffer:
    try:
        result = await MetaTransactionBuffer.update(db, id, meta.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e
