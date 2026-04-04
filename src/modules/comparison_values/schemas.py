from typing import List, Optional
from pydantic import BaseModel


# ==================== Comparison Value Meta Schemas ====================

class RQMetaComparisonValue(BaseModel):
    """Request schema for creating/updating comparison metadata"""
    key: str
    value: Optional[str] = None


# ==================== Comparison Value Schemas ====================

class RQComparisonValue(BaseModel):
    """Request schema for creating/updating a comparison value"""
    quantity_from: int = 1
    quantity_to: float
    value_from: Optional[int] = None  # ID of source value
    value_to: int    # ID of target value
    context: str
    meta: Optional[List[RQMetaComparisonValue]] = None


class RSComparisonValueSimple(BaseModel):
    """Simplified response for nested value references"""
    id: int
    uid: str
    name: str
    expression: str

    class Config:
        from_attributes = True


class RSComparisonValue(BaseModel):
    """Response schema for a comparison value"""
    uid: str
    id: int
    quantity_from: int
    quantity_to: float
    value_from: int
    value_to: int
    context: str
    source_value: Optional[RSComparisonValueSimple] = None
    target_value: Optional[RSComparisonValueSimple] = None

    class Config:
        from_attributes = True


class RSComparisonValueList(BaseModel):
    """Response schema for paginated comparison list"""
    data: List[RSComparisonValue]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


# ==================== Conversion Schemas ====================

class RQConvert(BaseModel):
    """Request schema for value conversion"""
    from_value_id: int
    to_value_id: int
    amount: float


class RSConvert(BaseModel):
    """Response schema for conversion result"""
    from_value: RSComparisonValueSimple
    to_value: RSComparisonValueSimple
    original_amount: float
    converted_amount: float
    rate: float
    inverse_rate: float
