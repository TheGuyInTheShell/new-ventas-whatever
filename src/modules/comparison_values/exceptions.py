from typing import Optional, TypeVar
from core.lib.decorators.exceptions import (
    BaseError,
    ServiceResult as CoreServiceResult,
)

T = TypeVar("T")

class ComparisonValueError(BaseError):
    """Base exception for comparison values module."""
    message = "A comparison value error occurred."
    code = "COMPARISON_VALUE_ERROR"

class ComparisonValueNotFoundError(ComparisonValueError):
    message = "Comparison value not found."
    code = "COMPARISON_VALUE_NOT_FOUND"

class ValueNotFoundError(ComparisonValueError):
    message = "Referenced value not found."
    code = "VALUE_NOT_FOUND"

class ComparisonRateNotFoundError(ComparisonValueError):
    message = "No conversion rate found between the specified values."
    code = "COMPARISON_RATE_NOT_FOUND"

# Keep ServiceResult alias for compatibility
ServiceResult = CoreServiceResult[T]
