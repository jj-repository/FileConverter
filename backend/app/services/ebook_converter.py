"""
eBook Converter Service
Handles conversion between EPUB and other formats using EbookLib
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import logging

from ebooklib import epub
from ebooklib.epub import EpubHtml
from bs4 import BeautifulSoup
from pypdf import PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

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
        session_id: str
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
        output_filename = f"{input_path.stem}_converted.{output_format}"
        output_path = settings.UPLOAD_DIR / output_filename

        try:
            if input_format == 'epub':
                await self._convert_from_epub(input_path, output_path, output_format, session_id)
            elif output_format == 'epub':
                await self._convert_to_epub(input_path, input_format, output_path, session_id)
            else:
                raise ValueError(f"Unsupported conversion: {input_format} → {output_format}")

            await self.send_progress(session_id, 100, "converting", "Conversion complete")
            return output_path

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise

    async def _convert_from_epub(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str,
        session_id: str
    ):
        """Convert EPUB to other formats"""
        await self.send_progress(session_id, 30, "converting", "Reading EPUB file")

        # Read EPUB
        book = epub.read_epub(str(input_path))

        await self.send_progress(session_id, 50, "converting", f"Converting to {output_format.upper()}")

        if output_format == 'txt':
            await self._epub_to_txt(book, output_path, session_id)
        elif output_format == 'html':
            await self._epub_to_html(book, output_path, session_id)
        elif output_format == 'pdf':
            await self._epub_to_pdf(book, output_path, session_id)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    async def _epub_to_txt(self, book: epub.EpubBook, output_path: Path, session_id: str):
        """Convert EPUB to plain text"""
        text_content = []

        # Extract title and author if available
        title = book.get_metadata('DC', 'title')
        if title:
            text_content.append(f"Title: {title[0][0]}\n")

        creator = book.get_metadata('DC', 'creator')
        if creator:
            text_content.append(f"Author: {creator[0][0]}\n")

        text_content.append("\n" + "=" * 80 + "\n\n")

        # Extract text from HTML items
        items = list(book.get_items())
        for i, item in enumerate(items):
            if item.get_type() == 9:  # ITEM_DOCUMENT (HTML)
                html_content = item.get_content()
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style tags
                for script in soup(['script', 'style']):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)

                if text.strip():
                    text_content.append(text)
                    text_content.append("\n\n")

            # Update progress
            if i % 10 == 0:
                progress = 50 + int((i / len(items)) * 40)
                await self.send_progress(session_id, progress, "converting", f"Processing content ({i}/{len(items)})")

        # Write to file
        output_path.write_text('\n'.join(text_content), encoding='utf-8')

    async def _epub_to_html(self, book: epub.EpubBook, output_path: Path, session_id: str):
        """Convert EPUB to single HTML file"""
        html_parts = []

        # Add HTML header
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html>')
        html_parts.append('<head>')
        html_parts.append('<meta charset="UTF-8">')

        # Add title
        title = book.get_metadata('DC', 'title')
        if title:
            html_parts.append(f'<title>{title[0][0]}</title>')

        html_parts.append('<style>')
        html_parts.append('body { font-family: Georgia, serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }')
        html_parts.append('h1, h2, h3 { color: #333; }')
        html_parts.append('p { margin: 1em 0; }')
        html_parts.append('</style>')
        html_parts.append('</head>')
        html_parts.append('<body>')

        # Add metadata
        html_parts.append('<header>')
        if title:
            html_parts.append(f'<h1>{title[0][0]}</h1>')
        creator = book.get_metadata('DC', 'creator')
        if creator:
            html_parts.append(f'<p><strong>Author:</strong> {creator[0][0]}</p>')
        html_parts.append('</header>')
        html_parts.append('<hr>')

        # Extract HTML content
        items = list(book.get_items())
        for i, item in enumerate(items):
            if item.get_type() == 9:  # ITEM_DOCUMENT
                html_content = item.get_content().decode('utf-8')
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract body content
                body = soup.find('body')
                if body:
                    html_parts.append(str(body))
                else:
                    html_parts.append(html_content)

            # Update progress
            if i % 10 == 0:
                progress = 50 + int((i / len(items)) * 40)
                await self.send_progress(session_id, progress, "converting", f"Processing content ({i}/{len(items)})")

        # Close HTML
        html_parts.append('</body>')
        html_parts.append('</html>')

        # Write to file
        output_path.write_text('\n'.join(html_parts), encoding='utf-8')

    async def _epub_to_pdf(self, book: epub.EpubBook, output_path: Path, session_id: str):
        """Convert EPUB to PDF (simple text-based conversion)"""
        # Create PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Add title and author
        title = book.get_metadata('DC', 'title')
        if title:
            story.append(Paragraph(title[0][0], styles['Title']))
            story.append(Spacer(1, 0.2 * inch))

        creator = book.get_metadata('DC', 'creator')
        if creator:
            story.append(Paragraph(f"By {creator[0][0]}", styles['Heading2']))
            story.append(Spacer(1, 0.5 * inch))

        # Extract text content
        items = list(book.get_items())
        for i, item in enumerate(items):
            if item.get_type() == 9:  # ITEM_DOCUMENT
                html_content = item.get_content()
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style tags
                for script in soup(['script', 'style']):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)

                # Add paragraphs to PDF
                if text.strip():
                    paragraphs = text.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            try:
                                story.append(Paragraph(para, styles['BodyText']))
                                story.append(Spacer(1, 0.1 * inch))
                            except Exception as e:
                                # Skip problematic paragraphs
                                logger.warning(f"Skipped paragraph due to error: {e}")
                                continue

            # Update progress
            if i % 5 == 0:
                progress = 50 + int((i / len(items)) * 40)
                await self.send_progress(session_id, progress, "converting", f"Building PDF ({i}/{len(items)})")

        # Build PDF
        doc.build(story)

    async def _convert_to_epub(
        self,
        input_path: Path,
        input_format: str,
        output_path: Path,
        session_id: str
    ):
        """Convert other formats to EPUB"""
        await self.send_progress(session_id, 30, "converting", f"Reading {input_format.upper()} file")

        # Create new EPUB book
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(input_path.stem)
        book.set_language('en')

        await self.send_progress(session_id, 50, "converting", "Converting to EPUB")

        if input_format == 'txt':
            await self._txt_to_epub(input_path, book, session_id)
        elif input_format == 'html':
            await self._html_to_epub(input_path, book, session_id)
        else:
            raise ValueError(f"Conversion from {input_format} to EPUB not yet supported")

        # Write EPUB file
        await self.send_progress(session_id, 90, "converting", "Writing EPUB file")
        epub.write_epub(str(output_path), book)

    async def _txt_to_epub(self, input_path: Path, book: epub.EpubBook, session_id: str):
        """Convert plain text to EPUB"""
        text = input_path.read_text(encoding='utf-8')

        # Create chapter
        chapter = epub.EpubHtml(title='Content', file_name='content.xhtml', lang='en')

        # Convert text to HTML paragraphs
        paragraphs = text.split('\n\n')
        html_content = '<html><head><title>Content</title></head><body>'

        for para in paragraphs:
            if para.strip():
                html_content += f'<p>{para.strip()}</p>'

        html_content += '</body></html>'
        chapter.set_content(html_content.encode('utf-8'))

        # Add chapter to book
        book.add_item(chapter)
        book.spine = ['nav', chapter]

        # Add navigation
        book.toc = (chapter,)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

    async def _html_to_epub(self, input_path: Path, book: epub.EpubBook, session_id: str):
        """Convert HTML to EPUB"""
        html = input_path.read_text(encoding='utf-8')

        # Create chapter
        chapter = epub.EpubHtml(title='Content', file_name='content.xhtml', lang='en')
        chapter.set_content(html.encode('utf-8'))

        # Add chapter to book
        book.add_item(chapter)
        book.spine = ['nav', chapter]

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
            'filename': file_path.name,
            'size': file_path.stat().st_size,
            'format': file_path.suffix[1:].lower(),
        }

        # Try to extract EPUB metadata
        if file_path.suffix.lower() == '.epub':
            try:
                book = epub.read_epub(str(file_path))

                title = book.get_metadata('DC', 'title')
                if title:
                    info['title'] = title[0][0]

                creator = book.get_metadata('DC', 'creator')
                if creator:
                    info['author'] = creator[0][0]

                language = book.get_metadata('DC', 'language')
                if language:
                    info['language'] = language[0][0]

                # Count items
                items = list(book.get_items())
                info['chapter_count'] = sum(1 for item in items if item.get_type() == 9)

            except Exception as e:
                logger.warning(f"Could not extract EPUB metadata: {e}")

        return info
