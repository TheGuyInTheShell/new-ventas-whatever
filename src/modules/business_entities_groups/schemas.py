from typing import Optional, List
from pydantic import BaseModel


# ==================== Business Entities Group Schemas ====================

class RQBusinessEntitiesGroup(BaseModel):
    """Request schema for creating/updating a business entities group"""
    name: str
    description: Optional[str] = ""


class RSBusinessEntitiesGroup(BaseModel):
    """Response schema for a business entities group"""
    id: int
    uid: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RSBusinessEntitiesGroupList(BaseModel):
    """Response schema for paginated list of business entities groups"""
    data: List[RSBusinessEntitiesGroup]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
