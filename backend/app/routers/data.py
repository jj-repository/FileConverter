from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.data_converter import DataConverter
from app.utils.validation import DATA_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = DataConverter()

DataEncoding = Literal["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1", "cp1252"]
DataDelimiter = Literal[",", ";", "\t", "|", ":"]

DATA_MIME_MAP = {
    "csv": "text/csv",
    "json": "application/json",
    "xml": "application/xml",
    "yaml": "application/x-yaml",
    "yml": "application/x-yaml",
    "toml": "application/toml",
    "ini": "text/plain",
    "jsonl": "application/x-ndjson",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_data(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    encoding: Annotated[Optional[DataEncoding], Form(description="Character encoding")] = "utf-8",
    delimiter: Annotated[
        Optional[DataDelimiter], Form(description="Delimiter for CSV files")
    ] = ",",
    pretty: Annotated[Optional[bool], Form(description="Pretty print JSON output")] = True,
):
    """Convert a data file to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"encoding": encoding, "delimiter": delimiter, "pretty": pretty},
        converter=converter,
        formats=settings.DATA_FORMATS,
        category="data",
        mime_types=DATA_MIME_TYPES,
        api_prefix="data",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_data(filename: str):
    """Download converted data file."""
    return await handle_download(filename, DATA_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported data formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_data_info(file: UploadFile = File(...)):
    """Get metadata about a data file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.DATA_FORMATS,
        category="data",
        metadata_getter="get_data_info",
    )
