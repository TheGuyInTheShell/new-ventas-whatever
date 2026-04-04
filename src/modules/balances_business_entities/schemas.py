from typing import List
from pydantic import BaseModel


class RQBalanceBusinessEntity(BaseModel):
    ref_business_entity: int
    ref_balance: int


class RSBalanceBusinessEntity(BaseModel):
    uid: str
    id: int
    ref_business_entity: int
    ref_balance: int


class RSBalanceBusinessEntityList(BaseModel):
    data: list[RSBalanceBusinessEntity] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
