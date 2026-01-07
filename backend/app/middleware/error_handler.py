"""
Error handling middleware for FastAPI
"""

import re
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.exceptions import (
    FileConverterException,
    ConversionError,
    UnsupportedFormatError,
    ConversionTimeoutError,
    FileValidationError,
    ExternalToolError,
    BatchConversionError,
    MetadataExtractionError,
)
from app.config import settings

logger = logging.getLogger(__name__)


def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages for production.

    Strips file paths, system paths, and other potentially sensitive info.
    """
    if not message:
        return message

    # Remove absolute file paths (Unix and Windows)
    message = re.sub(r'(/[a-zA-Z0-9_\-./]+)+', '[path]', message)
    message = re.sub(r'([A-Za-z]:\\[^\s:]+)', '[path]', message)

    # Remove potential IP addresses
    message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[ip]', message)

    # Remove UUIDs that might identify sessions
    message = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '[id]', message, flags=re.IGNORECASE)

    return message


async def file_converter_exception_handler(request: Request, exc: FileConverterException) -> JSONResponse:
    """Handle custom FileConverter exceptions"""
    logger.error(f"{exc.__class__.__name__}: {exc.message}", extra={"detail": exc.detail})

    # Map exception types to HTTP status codes
    status_code_map = {
        UnsupportedFormatError: status.HTTP_400_BAD_REQUEST,
        FileValidationError: status.HTTP_400_BAD_REQUEST,
        ConversionTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
        ConversionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalToolError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        MetadataExtractionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        BatchConversionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Sanitize error messages in production to prevent information leakage
    error_message = exc.message if settings.DEBUG else sanitize_error_message(exc.message)
    error_detail = exc.detail if settings.DEBUG else sanitize_error_message(str(exc.detail)) if exc.detail else None

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_message,
            "detail": error_detail,
            "type": exc.__class__.__name__,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Invalid request data",
            "detail": exc.errors(),
            "type": "ValidationError",
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "HTTPException",
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {str(exc)}")

    # Only include error details in DEBUG mode, sanitized for production
    detail = None
    if settings.DEBUG:
        detail = str(exc)
    else:
        # Provide sanitized hint in production without exposing internals
        detail = sanitize_error_message(str(exc)) if str(exc) else None

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "detail": detail,
            "type": "InternalServerError",
        },
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(FileConverterException, file_converter_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
