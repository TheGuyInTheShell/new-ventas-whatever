from fastapi.exceptions import HTTPException
from core.lib.decorators.exceptions import BaseError


def error_response(error: BaseError, status_code: int = 400) -> HTTPException:
    """
    Converts a domain BaseError into a FastAPI JSONResponse.
    This keeps HTTP responsibility in the web/api layer.
    """
    return HTTPException(status_code=status_code, detail=error)
