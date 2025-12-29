from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional

from app.services.document_converter import DocumentConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_file_size, validate_file_extension
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings


router = APIRouter()
document_converter = DocumentConverter()


@router.post("/convert", response_model=ConversionResponse)
async def convert_document(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    preserve_formatting: Optional[bool] = Form(True),
    toc: Optional[bool] = Form(False),
):
    """
    Convert a document to a different format

    - **file**: Document file to convert
    - **output_format**: Target format (txt, pdf, docx, md, html, rtf)
    - **preserve_formatting**: Preserve original formatting (default: True)
    - **toc**: Add table of contents for PDF/HTML/DOCX (default: False)
    """
    session_id = str(uuid.uuid4())

    try:
        # Validate file size
        validate_file_size(file, "document")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.DOCUMENT_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.DOCUMENT_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Convert document
        options = {
            "preserve_formatting": preserve_formatting,
            "toc": toc,
        }

        output_path = await document_converter.convert(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/document/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Document conversion completed successfully",
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
async def download_document(filename: str):
    """Download converted document file"""
    file_path = settings.UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported document formats"""
    formats = await document_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo)
async def get_document_info(file: UploadFile = File(...)):
    """Get metadata about a document file"""
    try:
        # Validate file
        validate_file_size(file, "document")
        input_format = validate_file_extension(file.filename, settings.DOCUMENT_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata
        metadata = await document_converter.get_document_metadata(temp_path)

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
        raise HTTPException(status_code=500, detail=f"Failed to get document info: {str(e)}")
