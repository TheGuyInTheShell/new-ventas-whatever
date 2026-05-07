from typing import List
from pydantic import BaseModel


class RQMetaValue(BaseModel):
    """Request schema for creating/updating meta"""
    name: str
    value: str
    ref_value: int


class RSMetaValue(BaseModel):
    """Response schema for meta"""
    key: str
    value: str
    ref_value: int

class RSMetaValueList(BaseModel):
    """Response schema for list of metas"""
    data: list[RSMetaValue] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
