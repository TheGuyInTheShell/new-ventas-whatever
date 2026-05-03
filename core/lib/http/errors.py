from fastapi.responses import JSONResponse
from core.lib.decorators.exceptions import BaseError

def error_response(error: BaseError, status_code: int = 400) -> JSONResponse:
    """
    Converts a domain BaseError into a FastAPI JSONResponse.
    This keeps HTTP responsibility in the web/api layer.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": error.message,
            "code": error.code
        }
    )
