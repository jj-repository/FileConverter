"""
Custom exception classes for FileConverter application
"""

from typing import Optional


class FileConverterException(Exception):
    """Base exception for all FileConverter errors"""
    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


class ConversionError(FileConverterException):
    """Raised when file conversion fails"""
    pass


class UnsupportedFormatError(FileConverterException):
    """Raised when file format is not supported"""
    pass


class ConversionTimeoutError(FileConverterException):
    """Raised when conversion operation times out"""
    pass


class FileValidationError(FileConverterException):
    """Raised when file validation fails (size, format, corruption)"""
    pass


class ExternalToolError(FileConverterException):
    """Raised when external tool (ffmpeg, pandoc, etc.) fails"""
    def __init__(self, tool_name: str, message: str, detail: Optional[str] = None):
        self.tool_name = tool_name
        super().__init__(f"{tool_name} error: {message}", detail)


class BatchConversionError(FileConverterException):
    """Raised when batch conversion encounters errors"""
    def __init__(self, message: str, failed_files: Optional[list] = None):
        self.failed_files = failed_files or []
        super().__init__(message)


class MetadataExtractionError(FileConverterException):
    """Raised when metadata extraction fails"""
    pass
