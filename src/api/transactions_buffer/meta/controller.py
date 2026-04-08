from typing import Literal, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.transactions_buffer.meta.models import MetaTransactionBuffer
from src.modules.transactions_buffer.meta.schemas import (
    RQMetaTransactionBuffer,
    RSMetaTransactionBuffer,
    RSMetaTransactionBufferList,
)


class TransactionBufferMetaController(Controller):
    """
    Controller for Transaction Buffer Metadata management.
    
    Path: /api/v1/transactions_buffer/meta
    """

    @Get("/id/{id}", response_model=RSMetaTransactionBuffer, status_code=200)
    async def get_meta(
        self, id: str | int, db: AsyncSession = Depends(get_async_db)
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

    @Get("/", response_model=RSMetaTransactionBufferList, status_code=200)
    async def get_metas(
        self,
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

    @Post("/", response_model=RSMetaTransactionBuffer, status_code=201)
    async def create_meta(
        self, meta: RQMetaTransactionBuffer, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaTransactionBuffer:
        try:
            result = await MetaTransactionBuffer(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaTransactionBuffer.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaTransactionBuffer, status_code=200)
    async def update_meta(
        self, id: str | int, meta: RQMetaTransactionBuffer, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaTransactionBuffer:
        try:
            result = await MetaTransactionBuffer.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
