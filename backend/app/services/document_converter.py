from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.base_converter import BaseConverter
from app.config import settings


class DocumentConverter(BaseConverter):
    """Document conversion service using Pandoc and other libraries"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.DOCUMENT_FORMATS),
            "output": list(settings.DOCUMENT_FORMATS),
        }
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._check_pandoc()

    def _check_pandoc(self):
        """Check if Pandoc is installed"""
        try:
            result = subprocess.run(
                [settings.PANDOC_PATH, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.pandoc_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.pandoc_available = False

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported document formats"""
        return self.supported_formats

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert document to target format

        Args:
            input_path: Path to input document
            output_format: Target format (txt, pdf, docx, md, html, rtf)
            options: Conversion options
                - preserve_formatting: bool (default: True)
                - toc: bool (add table of contents, default: False)

        Returns:
            Path to converted document
        """
        await self.send_progress(session_id, 0, "converting", "Starting document conversion")

        # Check if Pandoc is available
        if not self.pandoc_available:
            raise Exception(
                "Pandoc is not installed. Please install Pandoc to use document conversion. "
                "Installation: sudo apt install pandoc (Linux) or brew install pandoc (macOS)"
            )

        # Validate format
        input_format = input_path.suffix.lower().lstrip('.')
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_converted.{output_format}"

        await self.send_progress(session_id, 10, "converting", "Preparing conversion")

        # Build Pandoc command
        preserve_formatting = options.get('preserve_formatting', True)
        toc = options.get('toc', False)

        cmd = [
            settings.PANDOC_PATH,
            str(input_path),
            "-o", str(output_path),
            "-f", self._get_pandoc_format(input_format),
            "-t", self._get_pandoc_format(output_format),
        ]

        # Add table of contents if requested
        if toc and output_format in ["pdf", "html", "docx"]:
            cmd.append("--toc")

        # Add standalone flag for HTML
        if output_format == "html":
            cmd.append("--standalone")

        # PDF engine
        if output_format == "pdf":
            cmd.extend(["--pdf-engine=pdflatex"])

        await self.send_progress(session_id, 20, "converting", "Converting document with Pandoc")

        # Run Pandoc conversion
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await self.send_progress(session_id, 50, "converting", "Processing document")

            # Wait for process to complete
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise Exception(f"Pandoc conversion failed: {error_msg[:200]}")

            await self.send_progress(session_id, 90, "converting", "Finalizing document")

            # Verify output file exists
            if not output_path.exists():
                raise Exception("Output file was not created")

            await self.send_progress(session_id, 100, "completed", "Document conversion completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    def _get_pandoc_format(self, format_ext: str) -> str:
        """Map file extension to Pandoc format identifier"""
        format_map = {
            "txt": "markdown",  # Pandoc 3.x uses markdown for plain text input
            "md": "markdown",
            "html": "html",
            "docx": "docx",
            "pdf": "pdf",
            "rtf": "rtf",
        }
        return format_map.get(format_ext, format_ext)

    async def get_document_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract document metadata"""
        try:
            input_format = file_path.suffix.lower().lstrip('.')
            file_size = file_path.stat().st_size

            metadata = {
                "size": file_size,
                "format": input_format,
            }

            # Try to get word count using Pandoc
            if self.pandoc_available:
                try:
                    cmd = [
                        settings.PANDOC_PATH,
                        str(file_path),
                        "-f", self._get_pandoc_format(input_format),
                        "-t", "plain",
                        "--strip-comments"
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        text = result.stdout
                        word_count = len(text.split())
                        char_count = len(text)
                        line_count = len(text.splitlines())

                        metadata.update({
                            "word_count": word_count,
                            "character_count": char_count,
                            "line_count": line_count,
                        })
                except Exception as e:
                    print(f"Error getting document stats: {e}")

            # Special handling for DOCX
            if input_format == "docx":
                try:
                    from docx import Document
                    doc = Document(str(file_path))
                    metadata["paragraph_count"] = len(doc.paragraphs)
                    metadata["section_count"] = len(doc.sections)
                except Exception as e:
                    print(f"Error reading DOCX metadata: {e}")

            # Special handling for PDF
            if input_format == "pdf":
                try:
                    from PyPDF2 import PdfReader
                    pdf = PdfReader(str(file_path))
                    metadata["page_count"] = len(pdf.pages)

                    # Get PDF info if available
                    if pdf.metadata:
                        if pdf.metadata.title:
                            metadata["title"] = pdf.metadata.title
                        if pdf.metadata.author:
                            metadata["author"] = pdf.metadata.author
                except Exception as e:
                    print(f"Error reading PDF metadata: {e}")

            return metadata

        except Exception as e:
            return {"error": str(e)}
