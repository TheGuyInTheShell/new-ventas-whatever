from typing import List
from pydantic import BaseModel


class RQMetaPerson(BaseModel):
    """Request schema for creating/updating meta"""
    key: str
    value: str
    ref_person: int


class RSMetaPerson(BaseModel):
    """Response schema for meta"""
    key: str
    value: str
    ref_person: int


class RSMetaPersonList(BaseModel):
    """Response schema for list of metas"""
    data: list[RSMetaPerson] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
