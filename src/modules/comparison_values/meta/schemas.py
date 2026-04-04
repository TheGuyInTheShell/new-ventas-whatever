from typing import List
from pydantic import BaseModel


class RQMetaComparisonValue(BaseModel):
    """Request schema for creating/updating meta"""
    key: str
    value: str
    ref_comparison_value: int


class RSMetaComparisonValue(BaseModel):
    """Response schema for meta"""
    id: int
    uid: str
    key: str
    value: str
    ref_comparison_value: int


class RSMetaComparisonValueList(BaseModel):
    """Response schema for list of metas"""
    data: list[RSMetaComparisonValue] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
