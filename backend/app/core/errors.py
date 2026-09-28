"""
backend/app/core/errors.py
Custom application exception classes and standard error schemas.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, code: str = "internal_error", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class LLMUnavailableError(AppException):
    """Raised when the LLM service is unreachable, timed out, or returning server errors."""
    def __init__(self, message: str = "The assistant is temporarily unavailable. Please try again."):
        super().__init__(
            message=message,
            code="llm_unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class LLMAuthenticationError(AppException):
    """Raised when LLM authentication credentials fail."""
    def __init__(self, message: str = "The assistant is temporarily unavailable. Please try again."):
        super().__init__(
            message=message,
            code="llm_auth_error",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class MemoryUnavailableError(AppException):
    """Raised when Hindsight persistent memory service is temporarily unavailable."""
    def __init__(self, message: str = "Memory service is temporarily unavailable."):
        super().__init__(
            message=message,
            code="memory_unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Formats AppException into consistent clean JSON response without leaking tracebacks."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )
