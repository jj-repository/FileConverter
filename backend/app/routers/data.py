from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional, Annotated, Literal

from app.services.data_converter import DataConverter
from app.utils.file_handler import save_upload_file, cleanup_file, make_content_disposition
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename, validate_mime_type, DATA_MIME_TYPES
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator, check_rate_limit
from app.middleware.error_handler import sanitize_error_message


router = APIRouter()
data_converter = DataConverter()


# Whitelist types for data parameters
DataEncoding = Literal["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1", "cp1252"]
DataDelimiter = Literal[",", ";", "\t", "|", ":"]


@router.post("/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
async def convert_data(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    encoding: Annotated[Optional[DataEncoding], Form(description="Character encoding")] = "utf-8",
    delimiter: Annotated[Optional[DataDelimiter], Form(description="Delimiter for CSV files")] = ",",
    pretty: Annotated[Optional[bool], Form(description="Pretty print JSON output")] = True,
):
    """
    Convert a data file to a different format

    - **file**: Data file to convert (CSV, JSON, XML)
    - **output_format**: Target format (csv, json, xml)
    - **encoding**: Character encoding (utf-8, utf-16, ascii, latin-1, iso-8859-1, cp1252)
    - **delimiter**: Delimiter for CSV files (comma, semicolon, tab, pipe, colon)
    - **pretty**: Pretty print JSON output (default: true)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "document")  # Using document size limit for data files

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.DATA_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.DATA_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Validate MIME type to prevent file type spoofing
        validate_mime_type(input_path, DATA_MIME_TYPES)

        # Convert data file
        options = {
            "encoding": encoding,
            "delimiter": delimiter,
            "pretty": pretty,
        }

        output_path = await data_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/data/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Data conversion completed successfully",
            output_file=output_path.name,
            download_url=download_url
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'input_path' in locals():
            cleanup_file(input_path)
        if 'output_path' in locals():
            cleanup_file(output_path)

        raise HTTPException(status_code=500, detail=f"Conversion failed: {sanitize_error_message(str(e))}")


# MIME type mapping for data formats
DATA_MIME_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "xml": "application/xml",
    "yaml": "application/x-yaml",
    "yml": "application/x-yaml",
    "toml": "application/toml",
    "ini": "text/plain",
    "jsonl": "application/x-ndjson",
}


@router.get("/download/{filename}")
async def download_data(filename: str):
    """Download converted data file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = DATA_MIME_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)}
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported data formats"""
    formats = await data_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_data_info(file: UploadFile = File(...)):
    """Get metadata about a data file"""
    try:
        # Validate file
        validate_file_size(file, "document")
        input_format = validate_file_extension(file.filename, settings.DATA_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata and file size before cleanup
        metadata = await data_converter.get_data_info(temp_path)
        file_size = temp_path.stat().st_size

        # Clean up
        cleanup_file(temp_path)

        return FileInfo(
            filename=file.filename,
            size=file_size,
            format=input_format,
            metadata=metadata
        )

    except Exception as e:
        if 'temp_path' in locals():
            cleanup_file(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to get data info: {sanitize_error_message(str(e))}")
