from typing import Optional, TypeVar
from core.lib.decorators.exceptions import (
    BaseError,
    ServiceResult as CoreServiceResult,
)

T = TypeVar("T")

class ValueWithComparisonError(BaseError):
    """Base exception for value with comparison module."""
    message = "A value with comparison error occurred."
    code = "VALUE_WITH_COMPARISON_ERROR"

class ValueWithComparisonNotFoundError(ValueWithComparisonError):
    message = "Value with comparison not found."
    code = "VALUE_WITH_COMPARISON_NOT_FOUND"

class ComparisonCreationFailedError(ValueWithComparisonError):
    message = "Failed to create comparison for the value."
    code = "COMPARISON_CREATION_FAILED"

class ComparisonUpdateFailedError(ValueWithComparisonError):
    message = "Failed to update comparison for the value."
    code = "COMPARISON_UPDATE_FAILED"

# Keep ServiceResult alias for compatibility
ServiceResult = CoreServiceResult[T]
