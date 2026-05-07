from typing import List
from pydantic import BaseModel


class RQMetaTransactionBuffer(BaseModel):
    key: str
    value: str
    ref_transaction_buffer: int


class RSMetaTransactionBuffer(BaseModel):
    key: str
    value: str
    ref_transaction_buffer: int


class RSMetaTransactionBufferList(BaseModel):
    data: list[RSMetaTransactionBuffer] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
