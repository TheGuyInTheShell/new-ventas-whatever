from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db

from .models import MetaTransaction
from .schemas import (
    RQMetaTransaction,
    RSMetaTransaction,
    RSMetaTransactionList,
)

# prefix /meta
router = APIRouter()

tag = "meta"


@router.get("/id/{id}", response_model=RSMetaTransaction, status_code=200, tags=[tag])
async def get_meta(
    id: str | int, db: AsyncSession = Depends(get_async_db)
) -> RSMetaTransaction:
    try:
        result = await MetaTransaction.find_one(db, id)
        return RSMetaTransaction(
            id=result.id,
            uid=result.uid,
            key=result.key,
            value=result.value,
            ref_transaction=result.ref_transaction,
        )
    except Exception as e:
        print(e)
        raise e


@router.get("/", response_model=RSMetaTransactionList, status_code=200, tags=[tag])
async def get_metas(
    pag: Optional[int] = 1,
    ord: Literal["asc", "desc"] = "asc",
    status: Literal["deleted", "exists", "all"] = "exists",
    db: AsyncSession = Depends(get_async_db),
) -> RSMetaTransactionList:
    try:
        result = await MetaTransaction.find_some(db, pag or 1, ord, status)
        mapped_result = list(map(
            lambda x: RSMetaTransaction(
                id=x.id,
                uid=x.uid,
                key=x.key,
                value=x.value,
                ref_transaction=x.ref_transaction,
            ),
            result,
        ))
        return RSMetaTransactionList(
            data=mapped_result,
            total=0,
            page=0,
            page_size=0,
            total_pages=0,
            has_next=False,
            has_prev=False,
            next_page=0,
            prev_page=0,
        )
    except Exception as e:
        print(e)
        raise e


@router.post("/", response_model=RSMetaTransaction, status_code=201, tags=[tag])
async def create_meta(
    meta: RQMetaTransaction, db: AsyncSession = Depends(get_async_db)
) -> RSMetaTransaction:
    try:
        result = await MetaTransaction(**meta.model_dump()).save(db)
        return result
    except Exception as e:
        print(e)
        raise e


@router.delete("/id/{id}", status_code=204, tags=[tag])
async def delete_meta(id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
    try:
        await MetaTransaction.delete(db, id)
    except Exception as e:
        print(e)
        raise e


@router.put("/id/{id}", response_model=RSMetaTransaction, status_code=200, tags=[tag])
async def update_meta(
    id: str | int, meta: RQMetaTransaction, db: AsyncSession = Depends(get_async_db)
) -> RSMetaTransaction:
    try:
        result = await MetaTransaction.update(db, id, meta.model_dump())
        return result
    except Exception as e:
        print(e)
        raise e
