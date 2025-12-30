"""
Pandoc mocking utilities
"""

from unittest.mock import Mock, patch
from pathlib import Path


class PandocMock:
    """Mock Pandoc subprocess calls"""

    @staticmethod
    def mock_successful_conversion(output_content="<h1>Converted Document</h1>\n<p>This is converted content.</p>"):
        """
        Mock successful Pandoc conversion

        Args:
            output_content: Content to write to output file
        """
        def subprocess_side_effect(*args, **kwargs):
            # Find output file in command arguments
            command = args[0] if args else kwargs.get('args', [])

            # Look for --output or -o flag
            output_file = None
            for i, arg in enumerate(command):
                if arg in ['--output', '-o'] and i + 1 < len(command):
                    output_file = command[i + 1]
                    break

            # Write output to file if specified
            if output_file:
                Path(output_file).write_text(output_content)

            return Mock(
                returncode=0,
                stdout=b'',
                stderr=b''
            )

        return patch('subprocess.run', side_effect=subprocess_side_effect)

    @staticmethod
    def mock_failed_conversion(error_message="Unknown reader: invalid"):
        """
        Mock failed Pandoc conversion

        Args:
            error_message: Error message to return
        """
        mock_run = Mock(
            returncode=1,
            stdout=b'',
            stderr=error_message.encode() if isinstance(error_message, str) else error_message
        )

        return patch('subprocess.run', return_value=mock_run)

    @staticmethod
    def mock_not_installed():
        """Mock Pandoc not being installed"""
        def subprocess_side_effect(*args, **kwargs):
            raise FileNotFoundError("Pandoc not found")

        return patch('subprocess.run', side_effect=subprocess_side_effect)

    @staticmethod
    def mock_version_check(version="3.1.2"):
        """
        Mock Pandoc version check

        Args:
            version: Pandoc version to return
        """
        version_output = f"pandoc {version}\nCompiled with pandoc-types..."

        mock_run = Mock(
            returncode=0,
            stdout=version_output.encode(),
            stderr=b''
        )

        return patch('subprocess.run', return_value=mock_run)

    @staticmethod
    def mock_markdown_to_html(markdown_content: str):
        """
        Mock Markdown to HTML conversion

        Args:
            markdown_content: Markdown content to convert
        """
        # Simple markdown to HTML conversion for testing
        html_content = markdown_content.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html_content = html_content.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
        html_content = html_content.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
        html_content = f"<html><body>{html_content}</body></html>"

        return PandocMock.mock_successful_conversion(html_content)

    @staticmethod
    def mock_html_to_pdf():
        """Mock HTML to PDF conversion"""
        pdf_content = b'%PDF-1.4\nMOCK_PDF_CONTENT'
        return PandocMock.mock_successful_conversion(pdf_content.decode('latin-1'))

    @staticmethod
    def mock_docx_to_markdown():
        """Mock DOCX to Markdown conversion"""
        markdown_content = "# Document Title\n\nThis is a paragraph.\n\n## Section 1\n\nMore content here."
        return PandocMock.mock_successful_conversion(markdown_content)

    @staticmethod
    def validate_command_safety(command_args: list) -> bool:
        """
        Validate that Pandoc command is safe (no shell injection)

        Args:
            command_args: List of command arguments

        Returns:
            True if command is safe
        """
        shell_chars = [';', '|', '&', '`', '$', '\n', '\r']

        for arg in command_args:
            arg_str = str(arg)
            for char in shell_chars:
                if char in arg_str:
                    return False
        return True


class PandocCommandValidator:
    """Helper to validate Pandoc command construction"""

    SUPPORTED_INPUT_FORMATS = {
        'markdown', 'md', 'html', 'docx', 'odt', 'rtf', 'txt',
        'latex', 'tex', 'rst', 'org', 'textile', 'mediawiki'
    }

    SUPPORTED_OUTPUT_FORMATS = {
        'markdown', 'md', 'html', 'html5', 'docx', 'odt', 'rtf',
        'pdf', 'latex', 'tex', 'rst', 'org', 'textile'
    }

    @staticmethod
    def validate_format(format_name: str, format_type='input') -> bool:
        """
        Validate that format is supported by Pandoc

        Args:
            format_name: Format name to check
            format_type: Either 'input' or 'output'

        Returns:
            True if format is supported
        """
        formats = (
            PandocCommandValidator.SUPPORTED_INPUT_FORMATS
            if format_type == 'input'
            else PandocCommandValidator.SUPPORTED_OUTPUT_FORMATS
        )
        return format_name.lower() in formats

    @staticmethod
    def extract_input_format(command_args: list) -> str:
        """
        Extract input format from Pandoc command

        Args:
            command_args: List of command arguments

        Returns:
            Input format as string, or None if not found
        """
        for i, arg in enumerate(command_args):
            if arg in ['--from', '-f'] and i + 1 < len(command_args):
                return command_args[i + 1]
        return None

    @staticmethod
    def extract_output_format(command_args: list) -> str:
        """
        Extract output format from Pandoc command

        Args:
            command_args: List of command arguments

        Returns:
            Output format as string, or None if not found
        """
        for i, arg in enumerate(command_args):
            if arg in ['--to', '-t'] and i + 1 < len(command_args):
                return command_args[i + 1]
        return None

    @staticmethod
    def has_toc_option(command_args: list) -> bool:
        """
        Check if command includes table of contents generation

        Args:
            command_args: List of command arguments

        Returns:
            True if --toc is present
        """
        return '--toc' in command_args or '--table-of-contents' in command_args

    @staticmethod
    def has_standalone_option(command_args: list) -> bool:
        """
        Check if command includes standalone option

        Args:
            command_args: List of command arguments

        Returns:
            True if --standalone is present
        """
        return '--standalone' in command_args or '-s' in command_args
