from typing import List
from pydantic import BaseModel


class RQHistoricalComparisonValue(BaseModel):
    """Request schema for creating/updating historical"""
    quantity_from: int
    quantity_to: float
    value_from: int
    value_to: int
    original_comparison_id: int


class RSHistoricalComparisonValue(BaseModel):
    """Response schema for historical"""
    id: int
    uid: str
    quantity_from: int
    quantity_to: float
    value_from: int
    value_to: int
    original_comparison_id: int


class RSHistoricalComparisonValueList(BaseModel):
    """Response schema for list of historicals"""
    data: list[RSHistoricalComparisonValue] | List = []
    total: int = 0
    page: int | None = 0
    page_size: int | None = 0
    total_pages: int | None = 0
    has_next: bool | None = False
    has_prev: bool | None = False
    next_page: int | None = 0
    prev_page: int | None = 0
