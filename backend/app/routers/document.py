from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.document_converter import DocumentConverter
from app.utils.validation import DOCUMENT_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = DocumentConverter()

DOCUMENT_MIME_MAP = {
    "txt": "text/plain",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
    "html": "text/html",
    "rtf": "application/rtf",
    "odt": "application/vnd.oasis.opendocument.text",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_document(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    preserve_formatting: Optional[bool] = Form(True),
    toc: Optional[bool] = Form(False),
):
    """Convert a document to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"preserve_formatting": preserve_formatting, "toc": toc},
        converter=converter,
        formats=settings.DOCUMENT_FORMATS,
        category="document",
        mime_types=DOCUMENT_MIME_TYPES,
        api_prefix="document",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_document(filename: str):
    """Download converted document file."""
    return await handle_download(filename, DOCUMENT_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported document formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_document_info(file: UploadFile = File(...)):
    """Get metadata about a document file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.DOCUMENT_FORMATS,
        category="document",
        metadata_getter="get_document_metadata",
    )
