"""
Global error handlers for FastAPI application.

This module provides:
- General exception handling with Sentry integration
- Validation error handling with detailed error info
- Structured error responses
"""
import logging
from typing import Any, Dict

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions globally.

    This handler:
    1. Captures the exception in Sentry for monitoring
    2. Logs detailed information for debugging
    3. Returns a generic error response to the client
    4. Includes an error_id for client support tickets

    Args:
        request: FastAPI request object
        exc: The exception that was raised

    Returns:
        JSON response with 500 status code and error details
    """
    # Capture in Sentry for monitoring and alerting
    event_id = sentry_sdk.capture_exception(exc) if SENTRY_AVAILABLE else None

    # Extract request info for logging
    method = request.method
    path = request.url.path
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Log detailed error information
    logger.error(
        f"Unhandled exception in {method} {path}",
        exc_info=True,
        extra={
            "method": method,
            "path": path,
            "client": client_host,
            "user_agent": user_agent,
            "sentry_event_id": event_id,
        }
    )

    # Return generic error response (don't leak details to client)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please contact support with the error ID below.",
            "error_id": event_id,  # Track in Sentry
            "status_code": 500,
        }
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Provides detailed validation error information to help clients
    understand what went wrong with their request.

    Args:
        request: FastAPI request object
        exc: Validation error from Pydantic

    Returns:
        JSON response with 422 status code and validation errors
    """
    # Extract validation error details
    errors = exc.errors()
    method = request.method
    path = request.url.path

    # Log validation errors
    logger.warning(
        f"Validation error in {method} {path}",
        extra={
            "method": method,
            "path": path,
            "error_count": len(errors),
        }
    )

    # Capture in Sentry with context
    if SENTRY_AVAILABLE:
        sentry_sdk.capture_exception(
            exc,
            tags={
                "error_type": "validation",
                "path": path,
                "method": method,
            }
        )

    # Return validation errors to client
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": "Request validation failed",
            "errors": [
                {
                    "loc": list(error["loc"]),
                    "msg": error["msg"],
                    "type": error["type"],
                }
                for error in errors
            ],
            "status_code": 422,
        }
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Handle HTTPException errors.

    HTTPExceptions are intentional errors raised by the application.
    These are not unexpected and don't need to be captured in Sentry
    unless they are 5xx errors.

    Args:
        request: FastAPI request object
        exc: HTTP exception with status code and detail

    Returns:
        JSON response with the specified status code
    """
    # Only capture 5xx errors in Sentry
    if exc.status_code >= 500 and SENTRY_AVAILABLE:
        event_id = sentry_sdk.capture_exception(exc)
    else:
        event_id = None

    # Log the error
    logger.warning(
        f"HTTP exception {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "sentry_event_id": event_id,
        }
    )

    # Return error response
    content: Dict[str, Any] = {
        "error": f"HTTP {exc.status_code}",
        "detail": exc.detail,
        "status_code": exc.status_code,
    }

    if event_id:
        content["error_id"] = event_id

    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )
