from typing import Optional, List
from pydantic import BaseModel


class RQBusinessEntitiesSearch(BaseModel):
    name: Optional[str] = None
    child_name: Optional[str] = None
    group_name: Optional[str] = None
    group_names: Optional[List[str]] = None
    group_id: Optional[int] = None
    parent_id: Optional[int] = None
    child_id: Optional[int] = None
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

    def to_generic(self) -> RQBusinessEntitiesSearch:
        return RQBusinessEntitiesSearch(
            name=self.name,
            hierarchy=self.hierarchy,
            groups=self.groups,
            is_deleted=self.is_deleted,
            page=self.page,
            page_size=self.page_size
        )


class RQBusinessEntitySearchChild(BaseModel):
    name: str
    child_name: str
    is_deleted: Optional[bool] = False
    page: int = 1
    page_size: int = 10

    def to_generic(self) -> RQBusinessEntitiesSearch:
        return RQBusinessEntitiesSearch(
            name=self.name,
            child_name=self.child_name,
            is_deleted=self.is_deleted,
            page=self.page,
            page_size=self.page_size
        )


class RQBusinessEntitySearchGroups(BaseModel):
    name: str
    group_names: List[str]
    is_deleted: Optional[bool] = False
    page: int = 1
    page_size: int = 10

    def to_generic(self) -> RQBusinessEntitiesSearch:
        return RQBusinessEntitiesSearch(
            name=self.name,
            group_names=self.group_names,
            groups=True,
            is_deleted=self.is_deleted,
            page=self.page,
            page_size=self.page_size
        )


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


class RSBusinessEntitySearchChild(BaseModel):
    parent: RSBusinessEntitiesSearchItem
    child: RSBusinessEntitiesSearchItem


class RSBusinessEntitySearchGroups(BaseModel):
    entity: RSBusinessEntitiesSearchItem
    groups: List[str]
