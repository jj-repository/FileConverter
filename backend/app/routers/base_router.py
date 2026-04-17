"""Shared converter router helpers.

Each format-specific router defines its own convert endpoint (with unique Form
params) and delegates common download / formats / info operations here.
"""

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.config import settings
from app.middleware.error_handler import sanitize_error_message
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.utils.file_handler import cleanup_file, make_content_disposition, save_upload_file
from app.utils.validation import (
    validate_download_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
)
from app.utils.websocket_security import session_validator

logger = logging.getLogger(__name__)


def cleanup_after_download(path: str):
    """Background task to remove a file after it has been served."""
    cleanup_file(Path(path))


async def handle_convert(
    file: UploadFile,
    output_format: str,
    options: dict,
    *,
    converter: Any,
    formats: set,
    category: str,
    mime_types: dict,
    api_prefix: str,
) -> ConversionResponse:
    """Shared conversion flow: validate -> save -> convert -> respond."""
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)
    input_path = None
    output_path = None

    try:
        validate_file_size(file, category)
        validate_file_extension(file.filename, formats)
        output_fmt = output_format.lower()

        if output_fmt not in formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}",
            )

        input_path = await save_upload_file(file, settings.TEMP_DIR)
        validate_mime_type(input_path, mime_types)

        output_path = await converter.convert_with_cache(
            input_path=input_path,
            output_format=output_fmt,
            options=options,
            session_id=session_id,
        )
        cleanup_file(input_path)
        input_path = None

        response = ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message=f"{category.title()} conversion completed successfully",
            output_file=output_path.name,
            download_url=f"/api/{api_prefix}/download/{output_path.name}",
        )
        output_path = None
        return response
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {sanitize_error_message(str(e))}",
        )
    finally:
        if input_path:
            cleanup_file(input_path)
        if output_path:
            cleanup_file(output_path)


async def handle_download(
    filename: str,
    mime_map: dict[str, str],
    *,
    default_mime: str = "application/octet-stream",
) -> FileResponse:
    """Shared download flow: validate path -> resolve MIME -> serve file."""
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Try compound extension first (e.g. tar.gz), then simple
    ext = ""
    if "." in filename:
        parts = filename.rsplit(".", 2)
        if len(parts) >= 3:
            compound = f"{parts[-2]}.{parts[-1]}".lower()
            if compound in mime_map:
                ext = compound
        if not ext:
            ext = filename.rsplit(".", 1)[-1].lower()

    media_type = mime_map.get(ext, default_mime)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
        background=BackgroundTask(cleanup_after_download, str(file_path)),
    )


async def handle_action(
    file: UploadFile,
    *,
    action,
    formats: set,
    category: str,
    mime_types: dict,
    api_prefix: str,
    action_label: str = "Operation",
    **action_kwargs: Any,
) -> ConversionResponse:
    """Shared flow for endpoints that call an arbitrary async action on an uploaded file."""
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)
    input_path = None

    try:
        validate_file_extension(file.filename, formats)
        validate_file_size(file, category)
        input_path = await save_upload_file(file, settings.TEMP_DIR)
        validate_mime_type(input_path, mime_types)

        output_path = await action(input_path=input_path, session_id=session_id, **action_kwargs)
        cleanup_file(input_path)
        input_path = None

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message=f"{action_label} successful",
            output_file=output_path.name,
            download_url=f"/api/{api_prefix}/download/{output_path.name}",
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{action_label} failed: {sanitize_error_message(str(e))}",
        )
    finally:
        if input_path:
            cleanup_file(input_path)


_formats_cache: dict = {}


async def handle_formats(converter: Any) -> dict:
    """Shared formats endpoint. Cached per-converter; static data."""
    key = id(converter)
    cached = _formats_cache.get(key)
    if cached is not None:
        return cached
    formats = await converter.get_supported_formats()
    payload = {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }
    _formats_cache[key] = payload
    return payload


async def handle_info(
    file: UploadFile,
    *,
    converter: Any,
    formats: set,
    category: str,
    metadata_getter: str,
) -> FileInfo:
    """Shared info endpoint. *metadata_getter* is the method name on converter."""
    temp_path = None
    try:
        validate_file_size(file, category)
        input_format = validate_file_extension(file.filename, formats)
        temp_path = await save_upload_file(file, settings.TEMP_DIR)
        metadata = await getattr(converter, metadata_getter)(temp_path)
        file_size = temp_path.stat().st_size
        cleanup_file(temp_path)
        temp_path = None
        return FileInfo(
            filename=file.filename,
            size=file_size,
            format=input_format,
            metadata=metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get {category} info: {sanitize_error_message(str(e))}",
        )
    finally:
        if temp_path:
            cleanup_file(temp_path)


async def handle_info_raw(
    file: UploadFile,
    *,
    converter: Any,
    formats: set,
    category: str,
    info_getter: str = "get_info",
) -> FileInfo:
    """Info endpoint for converters whose *info_getter* returns a dict with
    filename/size/format keys plus extra metadata fields."""
    temp_path = None
    try:
        validate_file_extension(file.filename, formats)
        validate_file_size(file, category)
        temp_path = await save_upload_file(file, settings.TEMP_DIR)
        info = await getattr(converter, info_getter)(temp_path)
        cleanup_file(temp_path)
        temp_path = None
        metadata = {k: v for k, v in info.items() if k not in ("filename", "size", "format")}
        return FileInfo(
            filename=info["filename"],
            size=info["size"],
            format=info["format"],
            metadata=metadata or None,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get {category} info: {sanitize_error_message(str(e))}",
        )
    finally:
        if temp_path:
            cleanup_file(temp_path)
