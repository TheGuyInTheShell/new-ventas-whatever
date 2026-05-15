from typing import Optional, TypeVar
from core.lib.decorators.exceptions import BaseError

T = TypeVar("T")
ServiceResult = tuple[Optional[T], Optional[BaseError]]

class BalanceError(BaseError):
    """Base exception for balance-related errors."""
    pass

class BalanceNotFoundError(BalanceError):
    """Raised when a balance is not found."""
    def __init__(self, id_or_msg: str | int = "Balance not found"):
        if isinstance(id_or_msg, int):
            super().__init__(f"Balance with id {id_or_msg} not found.")
        else:
            super().__init__(id_or_msg)
