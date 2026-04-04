from typing import List, Optional, Literal
from app.modules.comparison_values.schemas import RSComparisonValue
from pydantic import BaseModel


# ==================== Value Meta Schemas ====================

class RQMetaValue(BaseModel):
    """Request schema for creating/updating value metadata"""
    key: str
    value: Optional[str] = None


class RQValueQuery(BaseModel):
    """Request schema for querying values"""
    name: Optional[str] = None
    expression: Optional[str] = None
    type: Optional[str] = None
    context: Optional[str] = None
    identifier: Optional[str] = None
    meta: Optional[bool] = False
    comparison: Optional[bool] = False
    comparison_to_id: Optional[int] = None
    comparison_meta: Optional[bool] = False
    balances: Optional[bool] = False
    balance_type: Optional[str] = None
    page: int = 1
    page_size: int = 10
    order: Literal["asc", "desc"] = "asc"
    order_by: Literal["name", "expression", "type", "context", "identifier"] = "name"
    status: Literal["deleted", "exists", "all"] = "exists"


class RSMetaValue(BaseModel):
    """Response schema for value metadata"""
    uid: str
    id: int
    key: str
    value: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Balance Schemas (Lightweight) ====================

class RSBalance(BaseModel):
    id: int
    quantity: float
    type: str

    class Config:
        from_attributes = True


# ==================== Value Schemas ====================

class RQValue(BaseModel):
    """Request schema for creating/updating a value"""
    name: str
    expression: str
    type: str
    context: Optional[str] = ""
    identifier: Optional[str] = None
    # Optional price information for inventory items
    price: Optional[float] = None
    currency_id: Optional[int] = None
    meta: Optional[List[RQMetaValue]] = None


class RSValue(BaseModel):
    """Response schema for a single value"""
    uid: str
    id: int
    name: str
    expression: str
    type: str
    context: str
    identifier: Optional[str] = None
    meta: Optional[List[RSMetaValue]] = None
    balances: Optional[List[RSBalance]] = None
    comparison: Optional["RSComparisonValue"] = None

    class Config:
        from_attributes = True


class RSValueList(BaseModel):
    """Response schema for paginated value list"""
    data: List[RSValue]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
