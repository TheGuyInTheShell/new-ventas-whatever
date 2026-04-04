from typing import Optional, List
from pydantic import BaseModel


# ==================== Group Connection Schemas ====================

class RQBusinessEntitiesGroupConnection(BaseModel):
    """Request schema for creating/updating a group-entity connection"""
    ref_business_entities_group: int
    ref_business_entities: int


class RSBusinessEntitiesGroupConnection(BaseModel):
    """Response schema for a group-entity connection"""
    id: int
    uid: str
    ref_business_entities_group: int
    ref_business_entities: int

    class Config:
        from_attributes = True


class RSBusinessEntitiesGroupConnectionList(BaseModel):
    """Response schema for paginated list of connections"""
    data: List[RSBusinessEntitiesGroupConnection]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
