"""
eBook Converter Service
Handles conversion between EPUB and other formats using EbookLib
"""

import asyncio
import html
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

import bleach
from bs4 import BeautifulSoup
from ebooklib import epub
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.config import settings
from app.services.base_converter import BaseConverter

logger = logging.getLogger(__name__)


class EbookConverter(BaseConverter):
    """Service for converting eBook formats"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.EBOOK_FORMATS),
            "output": list(settings.EBOOK_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported eBook formats"""
        return self.supported_formats

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
    ) -> Path:
        """
        Convert eBook to target format

        Args:
            input_path: Path to input file
            output_format: Target format (epub, txt, html, pdf)
            options: Conversion options
            session_id: Session ID for progress tracking

        Returns:
            Path to converted file
        """
        await self.send_progress(session_id, 10, "converting", "Starting eBook conversion")

        input_format = input_path.suffix[1:].lower()

        # Generate output filename
        output_filename = f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"
        output_path = settings.UPLOAD_DIR / output_filename

        try:
            if input_format == "epub":
                await self._convert_from_epub(input_path, output_path, output_format, session_id)
            elif output_format == "epub":
                await self._convert_to_epub(input_path, input_format, output_path, session_id)
            else:
                raise ValueError(f"Unsupported conversion: {input_format} → {output_format}")

            await self.send_progress(session_id, 100, "converting", "Conversion complete")
            return output_path

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise

    async def _convert_from_epub(
        self, input_path: Path, output_path: Path, output_format: str, session_id: str
    ):
        """Convert EPUB to other formats"""
        await self.send_progress(session_id, 30, "converting", "Reading EPUB file")

        # Read EPUB (blocking I/O, run in thread)
        book = await asyncio.to_thread(epub.read_epub, str(input_path))

        await self.send_progress(
            session_id, 50, "converting", f"Converting to {output_format.upper()}"
        )

        if output_format == "txt":
            await self._epub_to_txt(book, output_path, session_id)
        elif output_format == "html":
            await self._epub_to_html(book, output_path, session_id)
        elif output_format == "pdf":
            await self._epub_to_pdf(book, output_path, session_id)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    async def _epub_to_txt(self, book: epub.EpubBook, output_path: Path, session_id: str):
        """Convert EPUB to plain text"""
        await self.send_progress(session_id, 60, "converting", "Extracting text content")

        def _sync_extract() -> str:
            text_content = []
            title = book.get_metadata("DC", "title")
            if title:
                text_content.append(f"Title: {title[0][0]}\n")
            creator = book.get_metadata("DC", "creator")
            if creator:
                text_content.append(f"Author: {creator[0][0]}\n")
            text_content.append("\n" + "=" * 80 + "\n\n")
            for item in book.get_items():
                if item.get_type() == 9:  # ITEM_DOCUMENT (HTML)
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    for tag in soup(["script", "style"]):
                        tag.decompose()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = "\n".join(chunk for chunk in chunks if chunk)
                    if text.strip():
                        text_content.append(text)
                        text_content.append("\n\n")
            return "\n".join(text_content)

        result = await asyncio.to_thread(_sync_extract)
        output_path.write_text(result, encoding="utf-8")

    # Allowlist for HTML sanitization via bleach
    _ALLOWED_TAGS = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "br",
        "code",
        "div",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "span",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "u",
        "ul",
        "html",
        "head",
        "body",
        "title",
        "meta",
        "header",
    ]
    # Omitting 'style' avoids needing a CSS sanitizer; style attrs are dropped.
    _ALLOWED_ATTRS = {
        "*": ["class", "id"],
        "a": ["href", "title"],
        "img": ["src", "alt", "title", "width", "height"],
        "meta": ["charset", "name", "content"],
    }
    _ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

    def _sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML via bleach to prevent XSS (scripts, events, js: URIs, etc.)"""
        return bleach.clean(
            html_content,
            tags=self._ALLOWED_TAGS,
            attributes=self._ALLOWED_ATTRS,
            protocols=self._ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True,
        )

    async def _epub_to_html(self, book: epub.EpubBook, output_path: Path, session_id: str):
        """Convert EPUB to single HTML file"""
        await self.send_progress(session_id, 60, "converting", "Building HTML output")

        def _sync_build() -> str:
            parts = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '<meta charset="UTF-8">',
            ]
            title = book.get_metadata("DC", "title")
            if title:
                parts.append(f"<title>{html.escape(title[0][0])}</title>")
            parts += [
                "<style>",
                "body { font-family: Georgia, serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }",
                "h1, h2, h3 { color: #333; }",
                "p { margin: 1em 0; }",
                "</style>",
                "</head>",
                "<body>",
                "<header>",
            ]
            if title:
                parts.append(f"<h1>{html.escape(title[0][0])}</h1>")
            creator = book.get_metadata("DC", "creator")
            if creator:
                parts.append(f"<p><strong>Author:</strong> {html.escape(creator[0][0])}</p>")
            parts += ["</header>", "<hr>"]
            for item in book.get_items():
                if item.get_type() == 9:  # ITEM_DOCUMENT
                    html_content = item.get_content().decode("utf-8", errors="replace")
                    soup = BeautifulSoup(html_content, "html.parser")
                    body = soup.find("body")
                    parts.append(str(body) if body else html_content)
            parts += ["</body>", "</html>"]
            return self._sanitize_html("\n".join(parts))

        result = await asyncio.to_thread(_sync_build)
        output_path.write_text(result, encoding="utf-8")

    async def _epub_to_pdf(self, book: epub.EpubBook, output_path: Path, session_id: str):
        """Convert EPUB to PDF (simple text-based conversion)"""
        # Create PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Add title and author
        title = book.get_metadata("DC", "title")
        if title:
            story.append(Paragraph(title[0][0], styles["Title"]))
            story.append(Spacer(1, 0.2 * inch))

        creator = book.get_metadata("DC", "creator")
        if creator:
            story.append(Paragraph(f"By {creator[0][0]}", styles["Heading2"]))
            story.append(Spacer(1, 0.5 * inch))

        # Extract text content. BeautifulSoup parse is CPU-bound — offload per item.
        def _extract_paragraphs(raw_html: bytes) -> list[str]:
            soup = BeautifulSoup(raw_html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            joined = "\n".join(chunk for chunk in chunks if chunk)
            return [p for p in joined.split("\n\n") if p.strip()]

        items = list(book.get_items())
        for i, item in enumerate(items):
            if item.get_type() == 9:  # ITEM_DOCUMENT
                paragraphs = await asyncio.to_thread(_extract_paragraphs, item.get_content())
                for para in paragraphs:
                    try:
                        story.append(Paragraph(para, styles["BodyText"]))
                        story.append(Spacer(1, 0.1 * inch))
                    except Exception as e:
                        logger.warning(f"Skipped paragraph due to error: {e}")
                        continue

            # Update progress
            if i % 5 == 0:
                progress = 50 + int((i / len(items)) * 40)
                await self.send_progress(
                    session_id,
                    progress,
                    "converting",
                    f"Building PDF ({i}/{len(items)})",
                )

        # Build PDF (blocking I/O, run in thread)
        await asyncio.to_thread(doc.build, story)

    async def _convert_to_epub(
        self, input_path: Path, input_format: str, output_path: Path, session_id: str
    ):
        """Convert other formats to EPUB"""
        await self.send_progress(
            session_id, 30, "converting", f"Reading {input_format.upper()} file"
        )

        # Create new EPUB book
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(input_path.stem)
        book.set_language("en")

        await self.send_progress(session_id, 50, "converting", "Converting to EPUB")

        if input_format == "txt":
            await self._txt_to_epub(input_path, book, session_id)
        elif input_format == "html":
            await self._html_to_epub(input_path, book, session_id)
        else:
            raise ValueError(f"Conversion from {input_format} to EPUB not yet supported")

        # Write EPUB file
        await self.send_progress(session_id, 90, "converting", "Writing EPUB file")
        await asyncio.to_thread(epub.write_epub, str(output_path), book)

    async def _txt_to_epub(self, input_path: Path, book: epub.EpubBook, session_id: str):
        """Convert plain text to EPUB"""
        text = await asyncio.to_thread(input_path.read_text, encoding="utf-8")

        # Create chapter
        chapter = epub.EpubHtml(title="Content", file_name="content.xhtml", lang="en")

        # Convert text to HTML paragraphs
        paragraphs = text.split("\n\n")
        html_content = "<html><head><title>Content</title></head><body>"

        for para in paragraphs:
            if para.strip():
                html_content += f"<p>{html.escape(para.strip())}</p>"

        html_content += "</body></html>"
        chapter.set_content(html_content.encode("utf-8"))

        # Add chapter to book
        book.add_item(chapter)
        book.spine = ["nav", chapter]

        # Add navigation
        book.toc = (chapter,)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

    async def _html_to_epub(self, input_path: Path, book: epub.EpubBook, session_id: str):
        """Convert HTML to EPUB"""
        raw_html = await asyncio.to_thread(input_path.read_text, encoding="utf-8")
        safe_html = await asyncio.to_thread(self._sanitize_html, raw_html)

        # Create chapter
        chapter = epub.EpubHtml(title="Content", file_name="content.xhtml", lang="en")
        chapter.set_content(safe_html.encode("utf-8"))

        # Add chapter to book
        book.add_item(chapter)
        book.spine = ["nav", chapter]

        # Add navigation
        book.toc = (chapter,)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

    async def get_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about an eBook file

        Args:
            file_path: Path to the eBook file

        Returns:
            Dictionary with file information
        """
        info = {
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "format": file_path.suffix[1:].lower(),
        }

        # Try to extract EPUB metadata
        if file_path.suffix.lower() == ".epub":
            try:
                book = await asyncio.to_thread(epub.read_epub, str(file_path))

                title = book.get_metadata("DC", "title")
                if title:
                    info["title"] = title[0][0]

                creator = book.get_metadata("DC", "creator")
                if creator:
                    info["author"] = creator[0][0]

                language = book.get_metadata("DC", "language")
                if language:
                    info["language"] = language[0][0]

                # Count items
                items = list(book.get_items())
                info["chapter_count"] = sum(1 for item in items if item.get_type() == 9)

            except Exception as e:
                logger.warning(f"Could not extract EPUB metadata: {e}")

        return info
