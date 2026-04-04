from typing import List
from pydantic import BaseModel


class RQMetaInvoice(BaseModel):
    key: str
    value: str
    ref_invoice: int


class RSMetaInvoice(BaseModel):
    id: int
    uid: str
    key: str
    value: str
    ref_invoice: int


class RSMetaInvoiceList(BaseModel):
    data: list[RSMetaInvoice] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
