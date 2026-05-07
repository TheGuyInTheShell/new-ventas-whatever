from typing import TypeVar
from core.lib.decorators.exceptions import (
    BaseError,
    ServiceResult as CoreServiceResult,
)

T = TypeVar("T")

class ValueError(BaseError):
    """Base exception for values module."""
    message = "A value error occurred."
    code = "VALUE_ERROR"

class ValueNotFoundError(ValueError):
    message = "Value not found."
    code = "VALUE_NOT_FOUND"

class ValueCreationError(ValueError):
    message = "Failed to create value."
    code = "VALUE_CREATION_ERROR"

class ValueUpdateError(ValueError):
    message = "Failed to update value."
    code = "VALUE_UPDATE_ERROR"

# Keep ServiceResult alias for compatibility
ServiceResult = CoreServiceResult[T]
