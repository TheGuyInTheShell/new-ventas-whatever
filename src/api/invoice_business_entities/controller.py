from typing import List, Optional, Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from core.lib.decorators import Get, Post, Delete
from core.lib.register import Controller

from src.modules.invoice_business_entities.models import InvoiceBusinessEntity
from src.modules.invoice_business_entities.schemas import (
    RQInvoiceBusinessEntity,
    RSInvoiceBusinessEntity,
    RSInvoiceBusinessEntityList,
)
from src.modules.invoice_business_entities.services import create_invoice_business_entity


class InvoiceBusinessEntitiesController(Controller):
    """
    Controller for Invoice-BusinessEntities relationship management.
    
    Path: /api/v1/invoice_business_entities
    """

    @Get("/id/{id}", response_model=RSInvoiceBusinessEntity, status_code=200)
    async def get_InvoiceBusinessEntity(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoiceBusinessEntity:
        try:
            result = await InvoiceBusinessEntity.find_one(db, id)
            return RSInvoiceBusinessEntity(
                id=result.id, uid=result.uid,
                ref_invoice=result.ref_invoice,
                ref_business_entity=result.ref_business_entity,
            )
        except Exception as e:
            print(e)
            raise e

    @Get("/", response_model=RSInvoiceBusinessEntityList, status_code=200)
    async def get_InvoiceBusinessEntities(
        self,
        pag: Optional[int] = 1,
        ord: Literal["asc", "desc"] = "asc",
        status: Literal["deleted", "exists", "all"] = "exists",
        db: AsyncSession = Depends(get_async_db),
    ) -> RSInvoiceBusinessEntityList:
        try:
            result = await InvoiceBusinessEntity.find_some(db, pag or 1, ord=ord, status=status)
            mapped_result = [
                RSInvoiceBusinessEntity(
                    id=x.id, uid=x.uid,
                    ref_invoice=x.ref_invoice,
                    ref_business_entity=x.ref_business_entity,
                )
                for x in result
            ]
            return RSInvoiceBusinessEntityList(
                data=mapped_result,
                total=0, page=0, page_size=0, total_pages=0,
                has_next=False, has_prev=False, next_page=0, prev_page=0,
            )
        except Exception as e:
            print(e)
            raise e

    @Post("/", response_model=RSInvoiceBusinessEntity, status_code=201)
    async def create_InvoiceBusinessEntity_endpoint(
        self, data: RQInvoiceBusinessEntity, db: AsyncSession = Depends(get_async_db)
    ) -> RSInvoiceBusinessEntity:
        try:
            result = await create_invoice_business_entity(db, data)
            return RSInvoiceBusinessEntity(
                id=result.id, uid=result.uid,
                ref_invoice=result.ref_invoice,
                ref_business_entity=result.ref_business_entity,
            )
        except Exception as e:
            print(e)
            raise e

    @Delete("/id/{id}", status_code=204)
    async def delete_InvoiceBusinessEntity(
        self, id: str, db: AsyncSession = Depends(get_async_db)
    ) -> None:
        try:
            await InvoiceBusinessEntity.delete(db, id)
        except Exception as e:
            print(e)
            raise e
