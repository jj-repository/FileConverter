"""
Error handling middleware for FastAPI
"""

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

logger = logging.getLogger(__name__)


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

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
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

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "detail": str(exc) if logger.level == logging.DEBUG else None,
            "type": "InternalServerError",
        },
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(FileConverterException, file_converter_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
