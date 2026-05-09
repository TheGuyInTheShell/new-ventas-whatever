from core.lib.decorators.exceptions import BaseError

class BusinessEntityNotFoundError(BaseError):
    message = "Business entity not found"
    code = "BUSINESS_ENTITY_NOT_FOUND"

class ParentEntityNotFoundError(BaseError):
    message = "Parent business entity not found"
    code = "PARENT_ENTITY_NOT_FOUND"

class ChildEntityNotFoundError(BaseError):
    message = "Child business entity not found for the given parent"
    code = "CHILD_ENTITY_NOT_FOUND"
