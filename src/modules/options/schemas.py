from typing import List
from pydantic import BaseModel


class RQOptions(BaseModel):
    """Request schema for creating/updating options"""
    name: str
    context: str
    value: str


class RSOptions(BaseModel):
    """Response schema for options"""
    id: int
    uid: str
    name: str
    context: str
    value: str


class RSOptionsList(BaseModel):
    """Response schema for list of options"""
    data: list[RSOptions] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
