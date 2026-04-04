from typing import List
from pydantic import BaseModel


class RQInvoiceBusinessEntity(BaseModel):
    ref_invoice: int
    ref_business_entity: int


class RSInvoiceBusinessEntity(BaseModel):
    uid: str
    id: int
    ref_invoice: int
    ref_business_entity: int


class RSInvoiceBusinessEntityList(BaseModel):
    data: list[RSInvoiceBusinessEntity] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
