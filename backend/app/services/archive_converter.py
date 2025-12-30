from pathlib import Path
from typing import Dict, Any
import zipfile
import tarfile
import gzip
import shutil
import tempfile

# 7z support
try:
    import py7zr
    SEVENZ_AVAILABLE = True
except ImportError:
    SEVENZ_AVAILABLE = False

from app.services.base_converter import BaseConverter
from app.config import settings


class ArchiveConverter(BaseConverter):
    """Archive compression/conversion service"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.ARCHIVE_FORMATS),
            "output": list(settings.ARCHIVE_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported archive formats"""
        return self.supported_formats

    def _normalize_format(self, fmt: str) -> str:
        """Normalize archive format names"""
        fmt = fmt.lower()
        # Normalize aliases
        if fmt == 'tgz':
            return 'tar.gz'
        elif fmt == 'tbz2':
            return 'tar.bz2'
        return fmt

    def _get_compression_mode(self, output_format: str) -> str:
        """Get tarfile compression mode"""
        if output_format == 'tar.gz' or output_format == 'tgz':
            return 'w:gz'
        elif output_format == 'tar.bz2' or output_format == 'tbz2':
            return 'w:bz2'
        elif output_format == 'tar':
            return 'w'
        return 'w'

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert archive to target format

        Args:
            input_path: Path to input archive
            output_format: Target format (zip, tar, tar.gz, 7z, etc.)
            options: Conversion options
                - compression_level: int (0-9, default: 6)

        Returns:
            Path to converted archive
        """
        await self.send_progress(session_id, 0, "converting", "Starting archive conversion")

        # Validate format
        input_format = self._detect_format(input_path)
        output_format = self._normalize_format(output_format)

        if input_format not in settings.ARCHIVE_FORMATS:
            raise ValueError(f"Unsupported input format: {input_format}")
        if output_format not in settings.ARCHIVE_FORMATS:
            raise ValueError(f"Unsupported output format: {output_format}")

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_converted.{output_format}"

        # Get options
        compression_level = options.get('compression_level', 6)

        try:
            # If same format, just copy
            if input_format == output_format:
                await self.send_progress(session_id, 50, "converting", "Copying archive")
                shutil.copy(input_path, output_path)
                await self.send_progress(session_id, 100, "completed", "Archive copied")
                return output_path

            # Extract to temporary directory
            await self.send_progress(session_id, 20, "converting", "Extracting archive")
            with tempfile.TemporaryDirectory() as temp_extract_dir:
                temp_extract_path = Path(temp_extract_dir)

                # Extract input archive
                await self._extract_archive(input_path, temp_extract_path, input_format)

                await self.send_progress(session_id, 60, "converting", f"Creating {output_format} archive")

                # Create output archive
                await self._create_archive(
                    temp_extract_path,
                    output_path,
                    output_format,
                    compression_level
                )

            await self.send_progress(session_id, 100, "completed", "Archive conversion completed")
            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    def _detect_format(self, file_path: Path) -> str:
        """Detect archive format from file extension"""
        name_lower = file_path.name.lower()

        if name_lower.endswith('.tar.gz') or name_lower.endswith('.tgz'):
            return 'tar.gz'
        elif name_lower.endswith('.tar.bz2') or name_lower.endswith('.tbz2'):
            return 'tar.bz2'
        elif name_lower.endswith('.tar'):
            return 'tar'
        elif name_lower.endswith('.zip'):
            return 'zip'
        elif name_lower.endswith('.7z'):
            return '7z'
        elif name_lower.endswith('.gz'):
            return 'gz'
        else:
            raise ValueError(f"Unknown archive format: {file_path.suffix}")

    async def _extract_archive(self, archive_path: Path, extract_to: Path, format: str):
        """Extract archive to directory"""
        if format == 'zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_to)

        elif format in ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2']:
            with tarfile.open(archive_path, 'r:*') as tf:
                # Security: prevent path traversal
                for member in tf.getmembers():
                    if member.name.startswith('/') or '..' in member.name:
                        raise ValueError(f"Unsafe archive member: {member.name}")
                tf.extractall(extract_to)

        elif format == 'gz':
            # Single file gzip
            output_file = extract_to / archive_path.stem
            with gzip.open(archive_path, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        elif format == '7z':
            if not SEVENZ_AVAILABLE:
                raise ValueError("7z support not available. Install py7zr.")
            with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                archive.extractall(path=extract_to)

        else:
            raise ValueError(f"Unsupported format for extraction: {format}")

    async def _create_archive(
        self,
        source_dir: Path,
        output_path: Path,
        format: str,
        compression_level: int
    ):
        """Create archive from directory"""
        if format == 'zip':
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        zf.write(file_path, arcname)

        elif format in ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2']:
            mode = self._get_compression_mode(format)
            with tarfile.open(output_path, mode) as tf:
                for file_path in source_dir.rglob('*'):
                    arcname = file_path.relative_to(source_dir)
                    tf.add(file_path, arcname=arcname)

        elif format == 'gz':
            # For gz, compress the first file found
            files = list(source_dir.rglob('*'))
            files = [f for f in files if f.is_file()]
            if files:
                with open(files[0], 'rb') as f_in:
                    with gzip.open(output_path, 'wb', compresslevel=compression_level) as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                raise ValueError("No files found to compress")

        elif format == '7z':
            if not SEVENZ_AVAILABLE:
                raise ValueError("7z support not available. Install py7zr.")
            with py7zr.SevenZipFile(output_path, 'w') as archive:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        archive.write(file_path, arcname=arcname)

        else:
            raise ValueError(f"Unsupported format for creation: {format}")

    async def get_archive_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from archive file"""
        try:
            format = self._detect_format(file_path)

            info = {
                "format": format,
                "size": file_path.stat().st_size,
            }

            if format == 'zip':
                with zipfile.ZipFile(file_path, 'r') as zf:
                    info["files"] = len(zf.namelist())
                    info["file_list"] = zf.namelist()[:10]  # First 10 files
                    info["compressed_size"] = sum(f.compress_size for f in zf.filelist)
                    info["uncompressed_size"] = sum(f.file_size for f in zf.filelist)

            elif format in ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2']:
                with tarfile.open(file_path, 'r:*') as tf:
                    members = tf.getmembers()
                    info["files"] = len(members)
                    info["file_list"] = [m.name for m in members[:10]]
                    info["uncompressed_size"] = sum(m.size for m in members)

            elif format == '7z':
                if SEVENZ_AVAILABLE:
                    with py7zr.SevenZipFile(file_path, mode='r') as archive:
                        file_list = archive.getnames()
                        info["files"] = len(file_list)
                        info["file_list"] = file_list[:10]

            elif format == 'gz':
                info["files"] = 1
                info["file_list"] = [file_path.stem]

            return info

        except Exception as e:
            return {"error": str(e)}
