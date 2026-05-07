from typing import Optional, List
from pydantic import BaseModel


# ==================== Business Entities Hierarchy Schemas ====================

class RQBusinessEntitiesHierarchy(BaseModel):
    """Request schema for creating/updating an entity hierarchy relationship"""
    ref_entity_top: int
    ref_entity_bottom: int


class RSBusinessEntitiesHierarchy(BaseModel):
    """Response schema for an entity hierarchy relationship"""
    ref_entity_top: int
    ref_entity_bottom: int

    class Config:
        from_attributes = True


class RSBusinessEntitiesHierarchyList(BaseModel):
    """Response schema for paginated list of entity hierarchy relationships"""
    data: List[RSBusinessEntitiesHierarchy]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
