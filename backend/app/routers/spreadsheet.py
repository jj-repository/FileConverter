from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional

from app.services.spreadsheet_converter import SpreadsheetConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings


router = APIRouter()
spreadsheet_converter = SpreadsheetConverter()


@router.post("/convert", response_model=ConversionResponse)
async def convert_spreadsheet(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    include_all_sheets: Optional[bool] = Form(False),
    encoding: Optional[str] = Form("utf-8"),
    delimiter: Optional[str] = Form(None),
):
    """
    Convert a spreadsheet to a different format

    - **file**: Spreadsheet file to convert (XLSX, XLS, ODS, CSV, TSV)
    - **output_format**: Target format (xlsx, xls, ods, csv, tsv)
    - **sheet_name**: Specific sheet to convert (optional, uses first sheet by default)
    - **include_all_sheets**: Include all sheets (for supported formats)
    - **encoding**: Character encoding (default: utf-8)
    - **delimiter**: Delimiter for CSV files (default: auto-detect)
    """
    session_id = str(uuid.uuid4())

    try:
        # Validate file size
        validate_file_size(file, "spreadsheet")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.SPREADSHEET_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.SPREADSHEET_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Convert spreadsheet
        options = {
            "sheet_name": sheet_name,
            "include_all_sheets": include_all_sheets,
            "encoding": encoding,
            "delimiter": delimiter,
        }

        output_path = await spreadsheet_converter.convert(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/spreadsheet/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Spreadsheet conversion completed successfully",
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
async def download_spreadsheet(filename: str):
    """Download converted spreadsheet file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported spreadsheet formats"""
    formats = await spreadsheet_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo)
async def get_spreadsheet_info(file: UploadFile = File(...)):
    """Get metadata about a spreadsheet file"""
    try:
        # Validate file
        validate_file_size(file, "spreadsheet")
        input_format = validate_file_extension(file.filename, settings.SPREADSHEET_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata
        metadata = await spreadsheet_converter.get_spreadsheet_info(temp_path)

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
        raise HTTPException(status_code=500, detail=f"Failed to get spreadsheet info: {str(e)}")
