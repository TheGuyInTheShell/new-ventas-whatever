from typing import Optional, List
from pydantic import BaseModel
# from app.modules.values.schemas import RSValue # Avoid circular imports if possible or use if needed

class RQBalance(BaseModel):
    currency: str
    ref_value: int


class RSBalance(BaseModel):
    uid: str
    id: int
    currency: str
    ref_value: int

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
