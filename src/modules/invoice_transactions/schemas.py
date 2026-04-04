from typing import List
from pydantic import BaseModel


class RQInvoiceTransaction(BaseModel):
    ref_invoice: int
    ref_transaction: int


class RSInvoiceTransaction(BaseModel):
    uid: str
    id: int
    ref_invoice: int
    ref_transaction: int


class RSInvoiceTransactionList(BaseModel):
    data: list[RSInvoiceTransaction] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
