from typing import TypeVar
from core.lib.decorators.exceptions import (
    BaseError,
    ServiceResult as CoreServiceResult,
)

T = TypeVar("T")

class ValuesHierarchyError(BaseError):
    """Base exception for values hierarchy module."""
    message = "A values hierarchy error occurred."
    code = "VALUES_HIERARCHY_ERROR"

class ValuesHierarchyNotFoundError(ValuesHierarchyError):
    message = "Values hierarchy relationship not found."
    code = "VALUES_HIERARCHY_NOT_FOUND"

class ValuesHierarchyCreationError(ValuesHierarchyError):
    message = "Failed to create values hierarchy relationship."
    code = "VALUES_HIERARCHY_CREATION_ERROR"

# Keep ServiceResult alias for compatibility
ServiceResult = CoreServiceResult[T]
