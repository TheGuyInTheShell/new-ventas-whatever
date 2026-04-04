from typing import Optional, List
from pydantic import BaseModel


# ==================== Values Hierarchy Schemas ====================

class RQValuesHierarchy(BaseModel):
    """Request schema for creating/updating a value hierarchy relationship"""
    ref_value_top: int
    ref_value_bottom: int


class RSValuesHierarchy(BaseModel):
    """Response schema for a value hierarchy relationship"""
    id: int
    uid: str
    ref_value_top: int
    ref_value_bottom: int

    class Config:
        from_attributes = True


class RSValuesHierarchyList(BaseModel):
    """Response schema for paginated list of value hierarchy relationships"""
    data: List[RSValuesHierarchy]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
