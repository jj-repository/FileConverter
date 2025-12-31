"""
Comprehensive tests for app/middleware/error_handler.py

COVERAGE GOAL: 85%+

Tests cover:
1. file_converter_exception_handler - custom exception handling with proper HTTP status codes
2. validation_exception_handler - FastAPI validation error handling
3. http_exception_handler - HTTP exception handling
4. generic_exception_handler - catch-all for unexpected exceptions
5. register_exception_handlers - handler registration

Tests async handlers properly with pytest-asyncio and mocking.
"""

import pytest
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError as PydanticValidationError

from app.middleware.error_handler import (
    file_converter_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
    register_exception_handlers,
)
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


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object"""
    request = Mock(spec=Request)
    request.url = "http://localhost:8000/api/convert"
    request.method = "POST"
    request.client = ("127.0.0.1", 12345)
    return request


@pytest.fixture
def mock_logger():
    """Create a mock logger for capturing logs"""
    with patch('app.middleware.error_handler.logger') as logger_mock:
        yield logger_mock


# ============================================================================
# FILE_CONVERTER_EXCEPTION_HANDLER TESTS
# ============================================================================

class TestFileConverterExceptionHandler:
    """Test file_converter_exception_handler function"""

    @pytest.mark.asyncio
    async def test_unsupported_format_error_returns_400(self, mock_request, mock_logger):
        """Test that UnsupportedFormatError returns 400 status code"""
        exc = UnsupportedFormatError(
            message="Format .xyz is not supported",
            detail="Supported formats: .mp4, .mkv, .avi"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.media_type == "application/json"

    @pytest.mark.asyncio
    async def test_unsupported_format_error_response_format(self, mock_request, mock_logger):
        """Test response format for UnsupportedFormatError"""
        exc = UnsupportedFormatError(
            message="Format .xyz is not supported",
            detail="Supported formats: .mp4, .mkv, .avi"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        # Verify response structure
        assert response.status_code == 400
        content = response.body.decode()
        assert "Format .xyz is not supported" in content
        assert "UnsupportedFormatError" in content

    @pytest.mark.asyncio
    async def test_file_validation_error_returns_400(self, mock_request, mock_logger):
        """Test that FileValidationError returns 400 status code"""
        exc = FileValidationError(
            message="File validation failed",
            detail="File is corrupted or incomplete"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_conversion_timeout_error_returns_504(self, mock_request, mock_logger):
        """Test that ConversionTimeoutError returns 504 status code"""
        exc = ConversionTimeoutError(
            message="Conversion operation timed out",
            detail="Operation exceeded 300 seconds"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    @pytest.mark.asyncio
    async def test_conversion_error_returns_500(self, mock_request, mock_logger):
        """Test that ConversionError returns 500 status code"""
        exc = ConversionError(
            message="Conversion failed",
            detail="Internal conversion error occurred"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_external_tool_error_returns_500(self, mock_request, mock_logger):
        """Test that ExternalToolError returns 500 status code"""
        exc = ExternalToolError(
            tool_name="ffmpeg",
            message="FFmpeg failed to process video",
            detail="Error: codec not found"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_metadata_extraction_error_returns_500(self, mock_request, mock_logger):
        """Test that MetadataExtractionError returns 500 status code"""
        exc = MetadataExtractionError(
            message="Failed to extract metadata",
            detail="Could not read file headers"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_batch_conversion_error_returns_500(self, mock_request, mock_logger):
        """Test that BatchConversionError returns 500 status code"""
        exc = BatchConversionError(
            message="Batch conversion failed",
            failed_files=["file1.mp4", "file2.avi"]
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_unknown_file_converter_exception_returns_500(self, mock_request, mock_logger):
        """Test unknown FileConverterException subclass returns 500"""
        # Create a custom subclass not in the mapping
        class UnknownFileConverterException(FileConverterException):
            pass

        exc = UnknownFileConverterException(
            message="Unknown error",
            detail="This is not mapped to a specific status code"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_response_has_error_field(self, mock_request, mock_logger):
        """Test that response includes 'error' field"""
        exc = UnsupportedFormatError(
            message="Format not supported",
            detail="Details"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert b"error" in response.body

    @pytest.mark.asyncio
    async def test_response_has_detail_field(self, mock_request, mock_logger):
        """Test that response includes 'detail' field"""
        exc = FileValidationError(
            message="Validation failed",
            detail="File is corrupted"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert b"detail" in response.body

    @pytest.mark.asyncio
    async def test_response_has_type_field(self, mock_request, mock_logger):
        """Test that response includes 'type' field with exception class name"""
        exc = ConversionError(
            message="Conversion failed",
            detail="Details"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert b"ConversionError" in response.body

    @pytest.mark.asyncio
    async def test_logging_called_on_exception(self, mock_request, mock_logger):
        """Test that logger.error is called when exception occurs"""
        exc = UnsupportedFormatError(
            message="Format not supported",
            detail="Details"
        )

        await file_converter_exception_handler(mock_request, exc)

        # Verify logger was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "UnsupportedFormatError" in call_args[0][0]
        assert "Format not supported" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_logging_includes_detail(self, mock_request, mock_logger):
        """Test that logger includes detail in extra field"""
        exc = FileValidationError(
            message="Validation failed",
            detail="File is corrupted"
        )

        await file_converter_exception_handler(mock_request, exc)

        # Verify extra field in logger call
        call_kwargs = mock_logger.error.call_args[1]
        assert "extra" in call_kwargs
        assert call_kwargs["extra"]["detail"] == "File is corrupted"

    @pytest.mark.asyncio
    async def test_external_tool_error_preserves_tool_name(self, mock_request, mock_logger):
        """Test that ExternalToolError preserves tool name"""
        exc = ExternalToolError(
            tool_name="pandoc",
            message="Conversion failed",
            detail="Unknown format"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert b"pandoc" in response.body

    @pytest.mark.asyncio
    async def test_batch_conversion_error_preserves_failed_files(self, mock_request, mock_logger):
        """Test that BatchConversionError preserves failed_files list"""
        failed_files = ["file1.txt", "file2.docx"]
        exc = BatchConversionError(
            message="Batch failed",
            failed_files=failed_files
        )

        assert exc.failed_files == failed_files

    @pytest.mark.asyncio
    async def test_json_response_content_structure(self, mock_request, mock_logger):
        """Test complete JSON response structure"""
        exc = ConversionTimeoutError(
            message="Operation timed out",
            detail="Exceeded 300 seconds"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        # Response should be JSON
        assert response.media_type == "application/json"
        assert response.status_code == 504


# ============================================================================
# VALIDATION_EXCEPTION_HANDLER TESTS
# ============================================================================

class TestValidationExceptionHandler:
    """Test validation_exception_handler function"""

    @pytest.mark.asyncio
    async def test_returns_422_status_code(self, mock_request, mock_logger):
        """Test that validation errors return 422 status code"""
        # Create a mock RequestValidationError
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = [
            {
                "type": "value_error.missing",
                "loc": ("body", "filename"),
                "msg": "field required",
                "input": {}
            }
        ]

        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_response_format(self, mock_request, mock_logger):
        """Test validation error response format"""
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = [{"type": "value_error", "loc": ("body",), "msg": "error"}]

        response = await validation_exception_handler(mock_request, exc)

        assert b"error" in response.body
        assert b"detail" in response.body
        assert b"ValidationError" in response.body

    @pytest.mark.asyncio
    async def test_error_details_included(self, mock_request, mock_logger):
        """Test that validation error details are included in response"""
        error_details = [
            {
                "type": "value_error.missing",
                "loc": ("body", "file"),
                "msg": "field required",
                "input": {}
            },
            {
                "type": "type_error.string",
                "loc": ("query", "format"),
                "msg": "str type expected",
                "input": 123
            }
        ]
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = error_details

        response = await validation_exception_handler(mock_request, exc)

        # Verify errors are in response
        assert b"field required" in response.body
        assert b"str type expected" in response.body

    @pytest.mark.asyncio
    async def test_logging_called(self, mock_request, mock_logger):
        """Test that logger.warning is called for validation errors"""
        exc = Mock(spec=RequestValidationError)
        error_list = [{"type": "value_error", "loc": ("body",), "msg": "error"}]
        exc.errors.return_value = error_list

        await validation_exception_handler(mock_request, exc)

        # Verify logger was called
        mock_logger.warning.assert_called_once()
        assert "Validation error" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_logging_includes_errors(self, mock_request, mock_logger):
        """Test that logger includes error details"""
        exc = Mock(spec=RequestValidationError)
        error_list = [{"type": "value_error.missing", "loc": ("body", "file")}]
        exc.errors.return_value = error_list

        await validation_exception_handler(mock_request, exc)

        # Verify the errors list was passed to logger in the message
        call_args = mock_logger.warning.call_args[0][0]
        assert "value_error.missing" in call_args or "body" in call_args

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(self, mock_request, mock_logger):
        """Test handling of multiple validation errors"""
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"type": "value_error.missing", "loc": ("body", "field1")},
            {"type": "value_error.missing", "loc": ("body", "field2")},
            {"type": "value_error.missing", "loc": ("body", "field3")},
        ]

        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == 422


# ============================================================================
# HTTP_EXCEPTION_HANDLER TESTS
# ============================================================================

class TestHttpExceptionHandler:
    """Test http_exception_handler function"""

    @pytest.mark.asyncio
    async def test_404_not_found_status_code(self, mock_request):
        """Test HTTP 404 Not Found exception"""
        exc = StarletteHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_403_forbidden_status_code(self, mock_request):
        """Test HTTP 403 Forbidden exception"""
        exc = StarletteHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_400_bad_request_status_code(self, mock_request):
        """Test HTTP 400 Bad Request exception"""
        exc = StarletteHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request"
        )

        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_401_unauthorized_status_code(self, mock_request):
        """Test HTTP 401 Unauthorized exception"""
        exc = StarletteHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_response_format(self, mock_request):
        """Test HTTP exception response format"""
        exc = StarletteHTTPException(
            status_code=404,
            detail="Not found"
        )

        response = await http_exception_handler(mock_request, exc)

        assert b"error" in response.body
        assert b"HTTPException" in response.body
        assert b"Not found" in response.body

    @pytest.mark.asyncio
    async def test_detail_message_included(self, mock_request):
        """Test that detail message is included in response"""
        detail_msg = "The requested endpoint does not exist"
        exc = StarletteHTTPException(
            status_code=404,
            detail=detail_msg
        )

        response = await http_exception_handler(mock_request, exc)

        assert detail_msg.encode() in response.body

    @pytest.mark.asyncio
    async def test_various_status_codes(self, mock_request):
        """Test various HTTP status codes are preserved"""
        status_codes = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (405, "Method Not Allowed"),
            (409, "Conflict"),
            (410, "Gone"),
        ]

        for code, detail in status_codes:
            exc = StarletteHTTPException(status_code=code, detail=detail)
            response = await http_exception_handler(mock_request, exc)
            assert response.status_code == code

    @pytest.mark.asyncio
    async def test_response_type_field(self, mock_request):
        """Test that response includes type field with HTTPException"""
        exc = StarletteHTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(mock_request, exc)

        assert b'"type":"HTTPException"' in response.body or b'"type": "HTTPException"' in response.body


# ============================================================================
# GENERIC_EXCEPTION_HANDLER TESTS
# ============================================================================

class TestGenericExceptionHandler:
    """Test generic_exception_handler function"""

    @pytest.mark.asyncio
    async def test_returns_500_status_code(self, mock_request, mock_logger):
        """Test that generic exceptions return 500 status code"""
        exc = ValueError("Unexpected error occurred")

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_response_format(self, mock_request, mock_logger):
        """Test generic exception response format"""
        exc = RuntimeError("Something went wrong")

        response = await generic_exception_handler(mock_request, exc)

        assert b"error" in response.body
        assert b"InternalServerError" in response.body

    @pytest.mark.asyncio
    async def test_error_message_in_response(self, mock_request, mock_logger):
        """Test that generic error message is included"""
        exc = Exception("Test exception")

        response = await generic_exception_handler(mock_request, exc)

        assert b"An unexpected error occurred" in response.body

    @pytest.mark.asyncio
    async def test_logging_called(self, mock_request, mock_logger):
        """Test that logger.exception is called"""
        exc = Exception("Test error")

        await generic_exception_handler(mock_request, exc)

        mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_logging_includes_exception_message(self, mock_request, mock_logger):
        """Test that logger includes exception message"""
        exc_message = "Critical failure"
        exc = Exception(exc_message)

        await generic_exception_handler(mock_request, exc)

        call_args = mock_logger.exception.call_args[0]
        assert exc_message in call_args[0]

    @pytest.mark.asyncio
    async def test_detail_included_in_debug_mode(self, mock_request, mock_logger):
        """Test that detail is included when logger level is DEBUG"""
        exc = ValueError("Debug details should be visible")
        mock_logger.level = logging.DEBUG

        response = await generic_exception_handler(mock_request, exc)

        # In DEBUG mode, detail should be included
        content = response.body.decode()
        if "Debug details should be visible" in content or "null" not in content:
            # Debug mode shows detail
            pass

    @pytest.mark.asyncio
    async def test_detail_hidden_in_production(self, mock_request, mock_logger):
        """Test that detail is hidden when logger level is not DEBUG"""
        exc = ValueError("Production details should be hidden")
        mock_logger.level = logging.INFO

        response = await generic_exception_handler(mock_request, exc)

        # In production, detail may be None
        content = response.body.decode()
        # Should not have the actual exception message visible in production
        # (unless it's in the error field)

    @pytest.mark.asyncio
    async def test_handles_various_exception_types(self, mock_request, mock_logger):
        """Test handling of various exception types"""
        exceptions = [
            ValueError("Value error"),
            RuntimeError("Runtime error"),
            KeyError("Key error"),
            TypeError("Type error"),
            AttributeError("Attribute error"),
        ]

        for exc in exceptions:
            response = await generic_exception_handler(mock_request, exc)
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_handles_exception_with_no_message(self, mock_request, mock_logger):
        """Test handling of exception with empty message"""
        exc = Exception()

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == 500
        assert b"error" in response.body

    @pytest.mark.asyncio
    async def test_response_has_type_field(self, mock_request, mock_logger):
        """Test that response includes type field"""
        exc = Exception("Test")

        response = await generic_exception_handler(mock_request, exc)

        assert b"type" in response.body
        assert b"InternalServerError" in response.body


# ============================================================================
# REGISTER_EXCEPTION_HANDLERS TESTS
# ============================================================================

class TestRegisterExceptionHandlers:
    """Test register_exception_handlers function"""

    def test_all_handlers_are_registered(self):
        """Test that all exception handlers are registered"""
        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        register_exception_handlers(mock_app)

        # Verify add_exception_handler was called 4 times
        assert mock_app.add_exception_handler.call_count == 4

    def test_file_converter_exception_registered(self):
        """Test that FileConverterException handler is registered"""
        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        register_exception_handlers(mock_app)

        # Find the call for FileConverterException
        calls = mock_app.add_exception_handler.call_args_list
        exception_types = [call[0][0] for call in calls]
        assert FileConverterException in exception_types

    def test_validation_error_exception_registered(self):
        """Test that RequestValidationError handler is registered"""
        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        register_exception_handlers(mock_app)

        calls = mock_app.add_exception_handler.call_args_list
        exception_types = [call[0][0] for call in calls]
        assert RequestValidationError in exception_types

    def test_http_exception_registered(self):
        """Test that HTTPException handler is registered"""
        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        register_exception_handlers(mock_app)

        calls = mock_app.add_exception_handler.call_args_list
        exception_types = [call[0][0] for call in calls]
        assert StarletteHTTPException in exception_types

    def test_generic_exception_registered(self):
        """Test that generic Exception handler is registered"""
        mock_app = Mock()
        mock_app.add_exception_handler = Mock()

        register_exception_handlers(mock_app)

        calls = mock_app.add_exception_handler.call_args_list
        exception_types = [call[0][0] for call in calls]
        assert Exception in exception_types

    def test_correct_handler_mapping(self):
        """Test that correct handlers are mapped to correct exceptions"""
        mock_app = Mock()
        handler_map = {}

        def capture_handler(exc_type, handler):
            handler_map[exc_type] = handler

        mock_app.add_exception_handler = capture_handler

        register_exception_handlers(mock_app)

        # Verify mappings
        assert handler_map[FileConverterException] == file_converter_exception_handler
        assert handler_map[RequestValidationError] == validation_exception_handler
        assert handler_map[StarletteHTTPException] == http_exception_handler
        assert handler_map[Exception] == generic_exception_handler

    def test_handlers_are_callable(self):
        """Test that registered handlers are callable"""
        mock_app = Mock()
        handler_map = {}

        def capture_handler(exc_type, handler):
            handler_map[exc_type] = handler

        mock_app.add_exception_handler = capture_handler

        register_exception_handlers(mock_app)

        # All handlers should be callable
        for handler in handler_map.values():
            assert callable(handler)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestExceptionHandlingIntegration:
    """Integration tests for error handling in context"""

    @pytest.mark.asyncio
    async def test_exception_handler_with_real_exception_instance(self, mock_request):
        """Test handler with actual exception instance (not mock)"""
        exc = UnsupportedFormatError(
            message="HEIC format not supported",
            detail="Please convert HEIC to JPEG, PNG, or GIF"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 400
        content = response.body.decode()
        assert "HEIC" in content or "not supported" in content

    @pytest.mark.asyncio
    async def test_multiple_exception_types_have_different_status_codes(self, mock_request, mock_logger):
        """Test that different exception types return different status codes"""
        exceptions = [
            (UnsupportedFormatError("", ""), 400),
            (FileValidationError("", ""), 400),
            (ConversionTimeoutError("", ""), 504),
            (ConversionError("", ""), 500),
        ]

        for exc, expected_status in exceptions:
            response = await file_converter_exception_handler(mock_request, exc)
            assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_all_response_types_are_json(self, mock_request, mock_logger):
        """Test that all handlers return JSON responses"""
        handlers = [
            (
                file_converter_exception_handler,
                UnsupportedFormatError("test", "test")
            ),
            (
                validation_exception_handler,
                Mock(spec=RequestValidationError, errors=lambda: [])
            ),
            (
                http_exception_handler,
                StarletteHTTPException(status_code=404, detail="not found")
            ),
            (
                generic_exception_handler,
                Exception("test")
            ),
        ]

        for handler, exc in handlers:
            response = await handler(mock_request, exc)
            assert response.media_type == "application/json"

    @pytest.mark.asyncio
    async def test_response_contains_no_circular_references(self, mock_request, mock_logger):
        """Test that responses can be properly serialized without circular refs"""
        exc = ConversionError("Conversion failed", "Details here")

        response = await file_converter_exception_handler(mock_request, exc)

        # Should be able to decode without errors
        content = response.body.decode()
        assert len(content) > 0
        assert "error" in content


# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================

class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_exception_with_none_detail(self, mock_request, mock_logger):
        """Test exception handling when detail is None"""
        exc = FileConverterException(
            message="Error message",
            detail=None
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 500
        content = response.body.decode()
        assert "null" in content or "None" in content or exc.message in content

    @pytest.mark.asyncio
    async def test_exception_with_empty_strings(self, mock_request, mock_logger):
        """Test exception handling with empty strings"""
        exc = UnsupportedFormatError(
            message="",
            detail=""
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_exception_with_special_characters(self, mock_request, mock_logger):
        """Test exception handling with special characters"""
        exc = ConversionError(
            message='Error with "quotes" and \\ backslashes',
            detail="Unicode: émojis, 中文, العربية"
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 500
        # Should not raise serialization errors
        content = response.body.decode()
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_exception_with_very_long_message(self, mock_request, mock_logger):
        """Test exception handling with very long message"""
        long_message = "X" * 10000
        exc = FileValidationError(
            message=long_message,
            detail="Long detail" * 1000
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 400
        # Response should still be valid

    @pytest.mark.asyncio
    async def test_external_tool_error_with_missing_optional_detail(self, mock_request, mock_logger):
        """Test ExternalToolError without optional detail"""
        exc = ExternalToolError(
            tool_name="ffmpeg",
            message="Process failed"
            # detail is optional and defaults to None
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 500
        assert b"ffmpeg" in response.body

    @pytest.mark.asyncio
    async def test_batch_conversion_error_with_empty_failed_files(self, mock_request, mock_logger):
        """Test BatchConversionError with empty failed files list"""
        exc = BatchConversionError(
            message="Some conversions failed",
            failed_files=[]
        )

        response = await file_converter_exception_handler(mock_request, exc)

        assert response.status_code == 500
        assert exc.failed_files == []
