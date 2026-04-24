from typing import TypeVar, Generic, Optional, Type, Any, Callable, cast
import functools
import traceback
from loguru import logger

T = TypeVar("T")

class AuthError(Exception):
    """Base exception for authentication module."""
    message = "An authentication error occurred."
    code = "AUTH_ERROR"

    def __init__(self, message: str | None = None, code: str | None = None):
        if message:
            self.message = message
        if code:
            self.code = code
        super().__init__(self.message)

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

# Type alias for the methodology (Value, Error)
ServiceResult = tuple[Optional[T], Optional[AuthError]]

def handle_service_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to apply the (Value, Error) methodology.
    Catches all exceptions and returns them as the second element of a tuple.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> tuple[Any | None, AuthError | None]:
        try:
            result = await func(*args, **kwargs)
            # Prevent double wrapping if the method manually returned a ServiceResult tuple
            if isinstance(result, tuple) and len(result) == 2:
                if result[1] is None or isinstance(result[1], AuthError):
                    return result
            return result, None
        except AuthError as e:
            # Known domain errors
            return None, e
        except Exception as e:
            # Unexpected errors
            method_name = func.__name__
            class_name = args[0].__class__.__name__ if args else "Unknown"
            logger.error(f"Unexpected error in {class_name}.{method_name}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None, AuthError(f"System error in {method_name}: {str(e)}", code="SYSTEM_ERROR")

    return cast(Callable[..., Any], wrapper)

def handle_sync_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Sync version of the (Value, Error) methodology decorator.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> tuple[Any | None, AuthError | None]:
        try:
            result = func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2:
                if result[1] is None or isinstance(result[1], AuthError):
                    return result
            return result, None
        except AuthError as e:
            return None, e
        except Exception as e:
            method_name = func.__name__
            class_name = args[0].__class__.__name__ if args else "Unknown"
            logger.error(f"Unexpected error in {class_name}.{method_name}: {str(e)}")
            return None, AuthError(f"System error in {method_name}: {str(e)}", code="SYSTEM_ERROR")

    return cast(Callable[..., Any], wrapper)
