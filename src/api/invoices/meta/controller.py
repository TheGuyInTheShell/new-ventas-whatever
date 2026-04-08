from typing import Literal, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete, Put
from core.lib.register import Controller

from src.modules.invoices.meta.models import MetaInvoice
from src.modules.invoices.meta.schemas import RQMetaInvoice, RSMetaInvoice, RSMetaInvoiceList


class InvoiceMetaController(Controller):
    """
    Controller for Invoice Metadata management.
    
    Path: /api/v1/invoices/meta
    """

    @Get("/id/{id}", response_model=RSMetaInvoice, status_code=200)
    async def get_meta(
        self, id: str | int, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaInvoice:
        try:
            result = await MetaInvoice.find_one(db, id)
            return RSMetaInvoice(
                id=result.id, uid=result.uid,
                key=result.key, value=result.value,
                ref_invoice=result.ref_invoice,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSMetaInvoiceList, status_code=200)
    async def get_metas(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSMetaInvoiceList:
        try:
            result = await MetaInvoice.find_some(db, pag or 1, ord=ord, status=status)
            mapped_result = list(map(
                lambda x: RSMetaInvoice(
                    id=x.id, uid=x.uid,
                    key=x.key, value=x.value,
                    ref_invoice=x.ref_invoice,
                ),
                result,
            ))
            return RSMetaInvoiceList(
                data=mapped_result,
                total=0, page=0, page_size=0, total_pages=0,
                has_next=False, has_prev=False, next_page=0, prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSMetaInvoice, status_code=201)
    async def create_meta(
        self, meta: RQMetaInvoice, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaInvoice:
        try:
            result = await MetaInvoice(**meta.model_dump()).save(db)
            return result
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_meta(self, id: str | int, db: AsyncSession = Depends(get_async_db)) -> None:
        try:
            await MetaInvoice.delete(db, id)
        except Exception as e:
            print(e)
            raise e

    @Put("/id/{id}", response_model=RSMetaInvoice, status_code=200)
    async def update_meta(
        self, id: str | int, meta: RQMetaInvoice, db: AsyncSession = Depends(get_async_db)
    ) -> RSMetaInvoice:
        try:
            result = await MetaInvoice.update(db, id, meta.model_dump())
            return result
        except Exception as e:
            print(e)
            raise e
