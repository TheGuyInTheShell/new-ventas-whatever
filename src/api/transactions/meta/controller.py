from typing import Literal, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.transactions.meta.models import MetaTransaction
from src.modules.transactions.meta.schemas import (
    RQMetaTransaction,
    RSMetaTransaction,
    RSMetaTransactionList,
)


class TransactionsMetaController(Controller):
    """
    Controller for Transactions Metadata management.
    
    Path: /api/v1/transactions/meta
    """

    @Get("/id/{id}", response_model=RSMetaTransaction, status_code=200)
    async def get_meta(
        self, id: str | int, db: AsyncSession = Depends(get_async_db)
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

    @Get("/", response_model=RSMetaTransactionList, status_code=200)
    async def get_metas(
        self,
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

    @Post("/", response_model=RSMetaTransaction, status_code=201)
    async def create_meta(
        self, meta: RQMetaTransaction, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaTransaction:
        try:
            result = await MetaTransaction(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaTransaction.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaTransaction, status_code=200)
    async def update_meta(
        self, id: str | int, meta: RQMetaTransaction, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaTransaction:
        try:
            result = await MetaTransaction.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
