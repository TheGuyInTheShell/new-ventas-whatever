from typing import Optional, List
from pydantic import BaseModel


class RQBusinessEntitiesSearch(BaseModel):
    name: Optional[str] = None
    group_name: Optional[str] = None
    group_id: Optional[int] = None
    parent_id: Optional[int] = None
    child_id: Optional[int] = None
    is_deleted: Optional[bool] = False
    
    # New flags
    hierarchy: bool = False
    groups: bool = False
    
    page: int = 1
    page_size: int = 10


class RSBusinessEntitiesSearchItem(BaseModel):
    id: int
    uid: str
    name: str
    groups: List[str] = []
    children: Optional[List["RSBusinessEntitiesSearchItem"]] = None
    
    class Config:
        from_attributes = True


class RSBusinessEntitiesSearchList(BaseModel):
    data: List[RSBusinessEntitiesSearchItem]
    total: int
    page: int
    page_size: int
    total_pages: int
