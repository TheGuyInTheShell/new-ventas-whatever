from typing import Optional, List, Literal
from pydantic import BaseModel


class RQTransactionBuffer(BaseModel):
    quantity: str
    operation_type: Literal["+", "-"]
    state: Optional[str] = None
    trigger: Optional[str] = None
    ref_inverse_transaction: Optional[int] = None
    ref_by_user: int
    ref_balance_from: int
    ref_balance_to: int


class RSTransactionBuffer(BaseModel):
    uid: str
    id: int
    quantity: Optional[str] = None
    operation_type: Optional[str] = None
    state: Optional[str] = None
    trigger: Optional[str] = None
    ref_inverse_transaction: Optional[int] = None
    ref_by_user: int
    ref_balance_from: int
    ref_balance_to: int


class RSTransactionBufferList(BaseModel):
    data: list[RSTransactionBuffer] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
