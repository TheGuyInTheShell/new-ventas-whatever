from typing import Optional, TypeVar
from core.lib.decorators.exceptions import (
    BaseError,
    handle_service_errors,
    handle_sync_errors,
    ServiceResult as CoreServiceResult,
)

T = TypeVar("T")

class AuthError(BaseError):
    """Base exception for authentication module."""
    message = "An authentication error occurred."
    code = "AUTH_ERROR"

class AuthenticationError(AuthError):
    message = "Invalid username or password."
    code = "AUTHENTICATION_FAILED"

class UserNotFoundError(AuthError):
    message = "User not found."
    code = "USER_NOT_FOUND"

class UserAlreadyExistsError(AuthError):
    message = "A user with this username or email already exists."
    code = "USER_ALREADY_EXISTS"

class TokenError(AuthError):
    message = "Invalid or expired token."
    code = "TOKEN_ERROR"

class TokenExpiredError(TokenError):
    message = "Token has expired."
    code = "TOKEN_EXPIRED"

class OTPError(AuthError):
    message = "Invalid OTP code."
    code = "OTP_INVALID"

# Keep ServiceResult alias for compatibility, but it now uses BaseError compatible types
ServiceResult = CoreServiceResult[T]

