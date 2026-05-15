from typing import Optional, List
from pydantic import BaseModel

class RQBalance(BaseModel):
    type: str
    quantity: float
    ref_value: int

class RQUpdateBalance(BaseModel):
    quantity: float

class RSBalance(BaseModel):
    uid: str
    id: int
    type: str
    quantity: float
    ref_value: int

    model_config = {"from_attributes": True}

class RSBalanceList(BaseModel):
    data: List[RSBalance]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: int
    prev_page: int
