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
        Convert eBook to target format.

        Any input (epub/txt/html/pdf) is first normalized to a sanitized HTML
        body fragment, then rendered to the requested output. This makes every
        declared input→output pair work, routed through a common hub.

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
        output_filename = f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"
        output_path = settings.UPLOAD_DIR / output_filename

        try:
            # 1. Load input into a normalized (title, sanitized HTML body).
            await self.send_progress(
                session_id, 30, "converting", f"Reading {input_format.upper()} file"
            )
            title, body_html = await self._load_content(input_path, input_format)

            # 2. Render the normalized content to the requested output format.
            await self.send_progress(
                session_id, 60, "converting", f"Converting to {output_format.upper()}"
            )
            if output_format == "html":
                await self._write_html(title, body_html, output_path)
            elif output_format == "txt":
                await self._write_txt(title, body_html, output_path)
            elif output_format == "epub":
                await self._write_epub(title, body_html, output_path)
            elif output_format == "pdf":
                await self._write_pdf(title, body_html, output_path, session_id)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

            await self.send_progress(session_id, 100, "converting", "Conversion complete")
            return output_path

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Loaders: any input format -> (title, sanitized HTML body fragment)
    # ------------------------------------------------------------------

    async def _load_content(self, input_path: Path, input_format: str):
        if input_format == "epub":
            return await asyncio.to_thread(self._load_epub, input_path)
        if input_format == "html":
            return await asyncio.to_thread(self._load_html, input_path)
        if input_format == "txt":
            return await asyncio.to_thread(self._load_txt, input_path)
        if input_format == "pdf":
            return await asyncio.to_thread(self._load_pdf, input_path)
        raise ValueError(f"Conversion from {input_format} is not supported")

    def _load_epub(self, input_path: Path):
        book = epub.read_epub(str(input_path))
        return self._epub_book_to_content(book, default_title=input_path.stem)

    def _epub_book_to_content(self, book, default_title=None):
        """Extract (title, sanitized HTML body) from an already-read EpubBook."""
        title_meta = book.get_metadata("DC", "title")
        title = title_meta[0][0] if title_meta else default_title
        bodies = []
        for item in book.get_items():
            if item.get_type() == 9:  # ITEM_DOCUMENT (HTML)
                soup = BeautifulSoup(item.get_content(), "html.parser")
                body = soup.find("body")
                bodies.append(str(body) if body else soup.decode())
        return title, self._sanitize_html("\n".join(bodies))

    # Backward-compatible EPUB-specific helpers retained for white-box tests;
    # they read/normalize the EPUB then route through the unified writers.
    async def _convert_from_epub(
        self, input_path: Path, output_path: Path, output_format: str, session_id: str
    ):
        book = await asyncio.to_thread(epub.read_epub, str(input_path))
        title, body_html = self._epub_book_to_content(book, default_title=input_path.stem)
        if output_format == "txt":
            await self._write_txt(title, body_html, output_path)
        elif output_format == "html":
            await self._write_html(title, body_html, output_path)
        elif output_format == "pdf":
            await self._write_pdf(title, body_html, output_path, session_id)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    async def _epub_to_txt(self, book, output_path: Path, session_id: str):
        title, body_html = self._epub_book_to_content(book)
        await self._write_txt(title, body_html, output_path)

    async def _epub_to_html(self, book, output_path: Path, session_id: str):
        title, body_html = self._epub_book_to_content(book)
        await self._write_html(title, body_html, output_path)

    async def _epub_to_pdf(self, book, output_path: Path, session_id: str):
        title, body_html = self._epub_book_to_content(book)
        await self._write_pdf(title, body_html, output_path, session_id)

    def _load_html(self, input_path: Path):
        raw = input_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else input_path.stem
        body = soup.find("body")
        fragment = str(body) if body else raw
        return title, self._sanitize_html(fragment)

    def _load_txt(self, input_path: Path):
        text = input_path.read_text(encoding="utf-8", errors="replace")
        return input_path.stem, self._paragraphs_to_html(text)

    def _load_pdf(self, input_path: Path):
        from pypdf import PdfReader

        reader = PdfReader(str(input_path))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
        if not text:
            text = "(No extractable text found in PDF.)"
        return input_path.stem, self._paragraphs_to_html(text)

    @staticmethod
    def _paragraphs_to_html(text: str) -> str:
        """Wrap blank-line-separated plain text into escaped <p> blocks."""
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return "\n".join(f"<p>{html.escape(p)}</p>" for p in parts)

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

    async def _write_html(self, title, body_html: str, output_path: Path):
        """Render the normalized content to a standalone, sanitized HTML file."""

        def _build() -> str:
            parts = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                '<meta charset="UTF-8">',
                f"<title>{html.escape(title)}</title>" if title else "<title>Document</title>",
                "<style>",
                "body { font-family: Georgia, serif; line-height: 1.6; max-width: 800px;"
                " margin: 0 auto; padding: 20px; }",
                "h1, h2, h3 { color: #333; }",
                "p { margin: 1em 0; }",
                "</style>",
                "</head>",
                "<body>",
            ]
            if title:
                parts.append(f"<h1>{html.escape(title)}</h1>")
            parts += ["<hr>", body_html, "</body>", "</html>"]
            return self._sanitize_html("\n".join(parts))

        result = await asyncio.to_thread(_build)
        await asyncio.to_thread(output_path.write_text, result, encoding="utf-8")

    async def _write_txt(self, title, body_html: str, output_path: Path):
        """Render the normalized content to plain text."""

        def _build() -> str:
            soup = BeautifulSoup(body_html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned = "\n".join(chunk for chunk in chunks if chunk)
            header = f"{title}\n{'=' * len(str(title))}\n\n" if title else ""
            return header + cleaned

        result = await asyncio.to_thread(_build)
        await asyncio.to_thread(output_path.write_text, result, encoding="utf-8")

    async def _write_epub(self, title, body_html: str, output_path: Path):
        """Render the normalized content to an EPUB with a single chapter."""

        def _build():
            book = epub.EpubBook()
            book.set_identifier(str(uuid.uuid4()))
            book.set_title(title or "Document")
            book.set_language("en")

            chapter = epub.EpubHtml(title="Content", file_name="content.xhtml", lang="en")
            doc = (
                "<html><head><title>"
                f"{html.escape(title or 'Document')}</title></head><body>"
                f"{body_html}</body></html>"
            )
            chapter.set_content(self._sanitize_html(doc).encode("utf-8"))
            book.add_item(chapter)
            book.spine = ["nav", chapter]
            book.toc = (chapter,)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            epub.write_epub(str(output_path), book)

        await asyncio.to_thread(_build)

    async def _write_pdf(self, title, body_html: str, output_path: Path, session_id: str):
        """Render the normalized content to a simple text-based PDF (reportlab)."""

        def _build():
            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            if title:
                story.append(Paragraph(html.escape(str(title)), styles["Title"]))
                story.append(Spacer(1, 0.3 * inch))

            soup = BeautifulSoup(body_html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text()
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            for para in paragraphs:
                try:
                    story.append(Paragraph(html.escape(para), styles["BodyText"]))
                    story.append(Spacer(1, 0.1 * inch))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Skipped paragraph due to error: {e}")
            if not story:
                try:
                    story.append(Paragraph("(empty document)", styles["BodyText"]))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Skipped fallback paragraph due to error: {e}")
            doc.build(story)

        await asyncio.to_thread(_build)

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
