from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.spreadsheet_converter import SpreadsheetConverter
from app.utils.validation import SPREADSHEET_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = SpreadsheetConverter()

SpreadsheetEncoding = Literal["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1", "cp1252"]
SpreadsheetDelimiter = Literal[",", ";", "\t", "|"]

SPREADSHEET_MIME_MAP = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_spreadsheet(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    include_all_sheets: Optional[bool] = Form(False),
    encoding: Annotated[
        Optional[SpreadsheetEncoding], Form(description="Character encoding")
    ] = "utf-8",
    delimiter: Annotated[
        Optional[SpreadsheetDelimiter], Form(description="Delimiter for CSV files")
    ] = None,
):
    """Convert a spreadsheet to a different format."""
    return await handle_convert(
        file,
        output_format,
        {
            "sheet_name": sheet_name,
            "include_all_sheets": include_all_sheets,
            "encoding": encoding,
            "delimiter": delimiter,
        },
        converter=converter,
        formats=settings.SPREADSHEET_FORMATS,
        category="spreadsheet",
        mime_types=SPREADSHEET_MIME_TYPES,
        api_prefix="spreadsheet",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_spreadsheet(filename: str):
    """Download converted spreadsheet file."""
    return await handle_download(filename, SPREADSHEET_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported spreadsheet formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_spreadsheet_info(file: UploadFile = File(...)):
    """Get metadata about a spreadsheet file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.SPREADSHEET_FORMATS,
        category="spreadsheet",
        metadata_getter="get_spreadsheet_info",
    )
