"""
eBook Conversion Router
Handles EPUB and other eBook format conversion endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import logging

from app.config import settings
from app.services.ebook_converter import EbookConverter
from app.utils.validation import validate_file_size, validate_file_extension
from app.models.conversion import ConversionResponse
from app.utils.websocket_security import session_validator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/convert", response_model=ConversionResponse)
async def convert_ebook(
    file: UploadFile = File(...),
    output_format: str = Form(...),
):
    """
    Convert eBook file to target format

    Supported conversions:
    - EPUB → TXT, HTML, PDF
    - TXT, HTML → EPUB

    Args:
        file: eBook file to convert
        output_format: Target format (epub, txt, html, pdf)

    Returns:
        Conversion response with download URL
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.EBOOK_FORMATS)

        # Validate output format
        if output_format not in settings.EBOOK_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format: {output_format}. Supported: {', '.join(settings.EBOOK_FORMATS)}"
            )

        # Validate file size
        validate_file_size(file, "ebook")

        # Read file content after validation
        content = await file.read()

        # Save uploaded file
        input_path = settings.TEMP_DIR / f"{session_id}_input.{input_format}"
        input_path.write_bytes(content)

        # Convert
        converter = EbookConverter()
        output_path = await converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format,
            options={},
            session_id=session_id
        )

        # Clean up input file
        input_path.unlink(missing_ok=True)

        # Return response
        return ConversionResponse(
            session_id=session_id,
            status="completed",
            message="Conversion successful",
            output_file=output_path.name,
            download_url=f"/api/ebook/download/{output_path.name}"
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        # Clean up on error
        if 'input_path' in locals():
            input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/download/{filename}")
async def download_ebook(filename: str):
    """
    Download converted eBook file

    Args:
        filename: Name of the converted file

    Returns:
        FileResponse with the converted file
    """
    file_path = settings.UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/formats")
async def get_ebook_formats():
    """
    Get supported eBook formats

    Returns:
        Dictionary with input and output formats
    """
    return {
        "input_formats": sorted(list(settings.EBOOK_FORMATS)),
        "output_formats": sorted(list(settings.EBOOK_FORMATS)),
        "notes": {
            "epub": "EPUB is the standard eBook format",
            "txt": "Plain text extraction (loses formatting)",
            "html": "Single HTML file with basic styling",
            "pdf": "PDF with text content (loses advanced formatting)"
        }
    }


@router.post("/info")
async def get_ebook_info(file: UploadFile = File(...)):
    """
    Get information about an eBook file

    Args:
        file: eBook file to analyze

    Returns:
        Dictionary with eBook metadata
    """
    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.EBOOK_FORMATS)

        # Validate file size
        validate_file_size(file, "ebook")

        # Read file content after validation
        content = await file.read()

        # Save temp file
        temp_path = settings.TEMP_DIR / f"temp_{uuid.uuid4()}.{input_format}"
        temp_path.write_bytes(content)

        # Get info
        converter = EbookConverter()
        info = await converter.get_info(temp_path)

        # Clean up
        temp_path.unlink(missing_ok=True)

        return info

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Info extraction error: {e}")
        if 'temp_path' in locals():
            temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract info: {str(e)}")
