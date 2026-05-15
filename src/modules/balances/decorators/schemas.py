from pydantic import BaseModel, ConfigDict
from typing import Any, List, Optional


class CreateBalanceDecorator(BaseModel):
    ref_balance_from: int
    ref_balance_to: int
    balance_decorators: Optional[dict[str, Any]] = None
    is_reactive: bool = False

    model_config = ConfigDict(from_attributes=True)


class BalanceDecorator(BaseModel):
    ref_balance_from: int
    ref_balance_to: int
    balance_decorators: Optional[dict[str, Any]] = None
    is_reactive: bool = False

    model_config = ConfigDict(from_attributes=True)


class BalanceDecoratorPagination(BaseModel):
    data: List[BalanceDecorator]
    total: int
    page: int
    page_size: int
    total_pages: int
