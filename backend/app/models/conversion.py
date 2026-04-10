from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversionStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversionResponse(BaseModel):
    session_id: str
    status: ConversionStatus
    message: str
    output_file: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class ProgressUpdate(BaseModel):
    session_id: str
    progress: float = Field(ge=0, le=100)
    status: ConversionStatus
    message: str
    current_operation: Optional[str] = None


class FileInfo(BaseModel):
    filename: str
    size: int
    format: str
    metadata: Optional[Dict[str, Any]] = None


class BatchFileResult(BaseModel):
    """Result for a single file in batch conversion"""

    filename: str
    success: bool
    output_path: Optional[str] = None
    output_file: Optional[str] = None
    download_url: Optional[str] = None
    session_id: Optional[str] = None
    index: Optional[int] = None
    error: Optional[str] = None


class BatchConversionResponse(BaseModel):
    """Response for batch conversion endpoint"""

    session_id: str
    total_files: int
    successful: int
    failed: int
    results: List[BatchFileResult]
    message: str


class BatchZipResponse(BaseModel):
    """Response for batch ZIP creation endpoint"""

    zip_file: str
    download_url: str
    file_count: int
