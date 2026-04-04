from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class RQBusinessEntity(BaseModel):
    name: str
    type: Optional[str] = None
    context: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None


class RSBusinessEntity(BaseModel):
    uid: str
    id: int
    name: str
    type: Optional[str] = None
    context: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None


class RSBusinessEntityList(BaseModel):
    data: list[RSBusinessEntity] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0