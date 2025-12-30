from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional

from app.services.data_converter import DataConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator


router = APIRouter()
data_converter = DataConverter()


@router.post("/convert", response_model=ConversionResponse)
async def convert_data(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    encoding: Optional[str] = Form("utf-8"),
    delimiter: Optional[str] = Form(","),
    pretty: Optional[bool] = Form(True),
):
    """
    Convert a data file to a different format

    - **file**: Data file to convert (CSV, JSON, XML)
    - **output_format**: Target format (csv, json, xml)
    - **encoding**: Character encoding (default: utf-8)
    - **delimiter**: Delimiter for CSV files (default: ,)
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

        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/download/{filename}")
async def download_data(filename: str):
    """Download converted data file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported data formats"""
    formats = await data_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo)
async def get_data_info(file: UploadFile = File(...)):
    """Get metadata about a data file"""
    try:
        # Validate file
        validate_file_size(file, "document")
        input_format = validate_file_extension(file.filename, settings.DATA_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata
        metadata = await data_converter.get_data_info(temp_path)

        # Clean up
        cleanup_file(temp_path)

        return FileInfo(
            filename=file.filename,
            size=temp_path.stat().st_size if temp_path.exists() else 0,
            format=input_format,
            metadata=metadata
        )

    except Exception as e:
        if 'temp_path' in locals():
            cleanup_file(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to get data info: {str(e)}")
