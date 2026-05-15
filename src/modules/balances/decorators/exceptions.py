from typing import Optional, TypeVar
from core.lib.decorators.exceptions import BaseError

T = TypeVar("T")
ServiceResult = tuple[Optional[T], Optional[BaseError]]


class BalanceDecoratorError(BaseError):
    """Base exception for balance decorators."""

    pass


class BalanceDecoratorNotFoundError(BalanceDecoratorError):
    """Raised when a decorator link is not found."""

    def __init__(self, from_id: int, to_id: int):
        super().__init__(f"Decorator link from {from_id} to {to_id} not found.")


class BalanceDecoratorCreationError(BalanceDecoratorError):
    """Raised when decorator creation fails."""

    pass
