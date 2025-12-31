from pathlib import Path
from typing import Dict, Any, List
import asyncio
import zipfile
from concurrent.futures import ThreadPoolExecutor

from app.services.image_converter import ImageConverter
from app.services.video_converter import VideoConverter
from app.services.audio_converter import AudioConverter
from app.services.document_converter import DocumentConverter
from app.config import settings


class BatchConverter:
    """Batch conversion service for processing multiple files"""

    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.image_converter = ImageConverter(websocket_manager)
        self.video_converter = VideoConverter(websocket_manager)
        self.audio_converter = AudioConverter(websocket_manager)
        self.document_converter = DocumentConverter(websocket_manager)
        self.executor = ThreadPoolExecutor(max_workers=4)

    def get_converter_for_format(self, file_format: str):
        """Get the appropriate converter based on file format"""
        if file_format in settings.IMAGE_FORMATS:
            return self.image_converter, "image"
        elif file_format in settings.VIDEO_FORMATS:
            return self.video_converter, "video"
        elif file_format in settings.AUDIO_FORMATS:
            return self.audio_converter, "audio"
        elif file_format in settings.DOCUMENT_FORMATS:
            return self.document_converter, "document"
        else:
            return None, None

    async def convert_single_file(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
        file_index: int,
        total_files: int
    ) -> Dict[str, Any]:
        """Convert a single file and return the result"""
        try:
            # Get file format
            input_format = input_path.suffix.lower().lstrip('.')

            # Get appropriate converter
            converter, file_type = self.get_converter_for_format(input_format)

            if not converter:
                return {
                    "filename": input_path.name,
                    "success": False,
                    "error": f"Unsupported file format: {input_format}",
                    "session_id": session_id,
                    "index": file_index,
                }

            # Send progress update
            if self.websocket_manager:
                await self.websocket_manager.send_progress(
                    session_id,
                    (file_index / total_files) * 100,
                    "converting",
                    f"Converting file {file_index + 1} of {total_files}: {input_path.name}"
                )

            # Convert the file
            output_path = await converter.convert(
                input_path=input_path,
                output_format=output_format,
                options=options,
                session_id=f"{session_id}_{file_index}"
            )

            return {
                "filename": input_path.name,
                "success": True,
                "output_file": output_path.name,
                "output_path": str(output_path),
                "download_url": f"/api/{file_type}/download/{output_path.name}",
                "session_id": session_id,
                "index": file_index,
            }

        except Exception as e:
            return {
                "filename": input_path.name,
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "index": file_index,
            }

    async def convert_batch(
        self,
        input_paths: List[Path],
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Convert multiple files

        Args:
            input_paths: List of paths to input files
            output_format: Target output format
            options: Conversion options
            session_id: Batch session ID for progress tracking
            parallel: Whether to process files in parallel (default: True)

        Returns:
            List of conversion results
        """
        total_files = len(input_paths)

        # Send initial progress
        if self.websocket_manager:
            await self.websocket_manager.send_progress(
                session_id,
                0,
                "converting",
                f"Starting batch conversion of {total_files} files"
            )

        if parallel:
            # Process files in parallel
            tasks = [
                self.convert_single_file(
                    input_path,
                    output_format,
                    options,
                    session_id,
                    index,
                    total_files
                )
                for index, input_path in enumerate(input_paths)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error results
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append({
                        "filename": input_paths[i].name,
                        "success": False,
                        "error": str(result),
                        "session_id": session_id,
                        "index": i,
                    })
                else:
                    final_results.append(result)
            results = final_results
        else:
            # Process files sequentially
            results = []
            for index, input_path in enumerate(input_paths):
                result = await self.convert_single_file(
                    input_path,
                    output_format,
                    options,
                    session_id,
                    index,
                    total_files
                )
                results.append(result)

        # Send completion progress
        successful_count = sum(1 for r in results if r.get("success"))
        failed_count = total_files - successful_count

        if self.websocket_manager:
            await self.websocket_manager.send_progress(
                session_id,
                100,
                "completed",
                f"Batch conversion completed: {successful_count} successful, {failed_count} failed"
            )

        return results

    async def create_zip_archive(
        self,
        file_paths: List[Path],
        archive_name: str = "converted_files.zip"
    ) -> Path:
        """
        Create a ZIP archive of converted files

        Args:
            file_paths: List of file paths to include in the archive
            archive_name: Name of the ZIP file

        Returns:
            Path to created ZIP archive
        """
        zip_path = settings.UPLOAD_DIR / archive_name

        def create_zip():
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    if file_path.exists():
                        zipf.write(file_path, file_path.name)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, create_zip)

        return zip_path
