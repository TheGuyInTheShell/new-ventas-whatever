from typing import Optional, List
from pydantic import BaseModel


class RQBusinessEntitiesSearch(BaseModel):
    name: Optional[str] = None
    is_deleted: Optional[bool] = False

    # New flags
    hierarchy: bool = False
    groups: bool = False

    page: int = 1
    page_size: int = 10


class RQBusinessEntitySearch(BaseModel):
    name: str
    hierarchy: bool = False
    groups: bool = False
    is_deleted: Optional[bool] = False
    page: int = 1
    page_size: int = 10


class RQBusinessEntitySearchChild(BaseModel):
    name: str
    child_name: str
    is_deleted: Optional[bool] = False
    page: int = 1
    page_size: int = 10


class RQBusinessEntitySearchGroups(BaseModel):
    name: str
    group_names: List[str]
    is_deleted: Optional[bool] = False
    page: int = 1
    page_size: int = 10


class RSBusinessEntitiesSearchItem(BaseModel):
    id: int
    uid: str
    name: str
    groups: List[str] = []
    child: Optional["RSBusinessEntitiesSearchItem"] = None
    children: Optional[List["RSBusinessEntitiesSearchItem"]] = None

    class Config:
        from_attributes = True


class RSBusinessEntitiesSearchList(BaseModel):
    data: List[RSBusinessEntitiesSearchItem]
    total: int
    page: int
    page_size: int
    total_pages: int
