"""
File I/O mocking utilities (aiofiles, PIL, python-magic)
"""

from unittest.mock import Mock, AsyncMock, patch, MagicMock
from PIL import Image
import io


class PILMock:
    """Mock PIL/Pillow image operations"""

    @staticmethod
    def mock_image_open(width=800, height=600, format='JPEG', mode='RGB'):
        """
        Mock PIL Image.open()

        Args:
            width: Image width in pixels
            height: Image height in pixels
            format: Image format (JPEG, PNG, etc.)
            mode: Color mode (RGB, RGBA, L, etc.)
        """
        mock_img = MagicMock(spec=Image.Image)
        mock_img.width = width
        mock_img.height = height
        mock_img.size = (width, height)
        mock_img.format = format
        mock_img.mode = mode
        mock_img.save = Mock()
        mock_img.resize = Mock(return_value=mock_img)
        mock_img.convert = Mock(return_value=mock_img)
        mock_img.thumbnail = Mock()
        mock_img.rotate = Mock(return_value=mock_img)
        mock_img.crop = Mock(return_value=mock_img)

        # Mock info dict
        mock_img.info = {
            'dpi': (72, 72),
            'compression': 'jpeg',
            'quality': 95
        }

        return patch('PIL.Image.open', return_value=mock_img)

    @staticmethod
    def mock_image_new():
        """Mock PIL Image.new()"""
        def create_new_image(mode, size, color=None):
            mock_img = MagicMock(spec=Image.Image)
            mock_img.width = size[0]
            mock_img.height = size[1]
            mock_img.size = size
            mock_img.format = None
            mock_img.mode = mode
            mock_img.save = Mock()
            mock_img.resize = Mock(return_value=mock_img)
            mock_img.convert = Mock(return_value=mock_img)
            return mock_img

        return patch('PIL.Image.new', side_effect=create_new_image)

    @staticmethod
    def mock_image_save_success():
        """Mock successful image save operation"""
        mock_save = Mock()
        return mock_save

    @staticmethod
    def mock_image_save_failure(error_message="Failed to save image"):
        """
        Mock failed image save operation

        Args:
            error_message: Error message to raise
        """
        def save_side_effect(*args, **kwargs):
            raise IOError(error_message)

        mock_save = Mock(side_effect=save_side_effect)
        return mock_save

    @staticmethod
    def create_real_test_image(width=100, height=100, color='red', format='PNG'):
        """
        Create a real PIL Image for testing (not a mock)

        Args:
            width: Image width
            height: Image height
            color: Image color
            format: Image format

        Returns:
            PIL Image object
        """
        img = Image.new('RGB', (width, height), color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img

    @staticmethod
    def image_to_bytes(img, format='PNG'):
        """
        Convert PIL Image to bytes

        Args:
            img: PIL Image object
            format: Output format

        Returns:
            BytesIO object containing image data
        """
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes


class AiofilesMock:
    """Mock aiofiles async file operations"""

    @staticmethod
    def mock_async_write():
        """Mock aiofiles.open() for writing"""
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        mock_file.read = AsyncMock(return_value=b'mock file content')
        mock_file.__aenter__ = AsyncMock(return_value=mock_file)
        mock_file.__aexit__ = AsyncMock()

        return patch('aiofiles.open', return_value=mock_file)

    @staticmethod
    def mock_async_read(content=b'mock file content'):
        """
        Mock aiofiles.open() for reading

        Args:
            content: Content to return when reading
        """
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(return_value=content)
        mock_file.write = AsyncMock()
        mock_file.__aenter__ = AsyncMock(return_value=mock_file)
        mock_file.__aexit__ = AsyncMock()

        return patch('aiofiles.open', return_value=mock_file)

    @staticmethod
    def mock_async_file_error(error_class=IOError, error_message="File operation failed"):
        """
        Mock aiofiles operation that raises an error

        Args:
            error_class: Exception class to raise
            error_message: Error message
        """
        async def async_error(*args, **kwargs):
            raise error_class(error_message)

        mock_file = AsyncMock()
        mock_file.__aenter__ = AsyncMock(side_effect=async_error)
        mock_file.__aexit__ = AsyncMock()

        return patch('aiofiles.open', return_value=mock_file)


class PythonMagicMock:
    """Mock python-magic MIME type detection"""

    @staticmethod
    def mock_mime_detection(mime_type='image/jpeg'):
        """
        Mock magic.from_file() for MIME type detection

        Args:
            mime_type: MIME type to return
        """
        mock_magic = Mock(return_value=mime_type)
        return patch('magic.from_file', mock_magic)

    @staticmethod
    def mock_mime_not_available():
        """Mock python-magic not being available"""
        def import_error(*args, **kwargs):
            raise ImportError("python-magic not installed")

        return patch('magic.from_file', side_effect=import_error)

    @staticmethod
    def get_mime_type_for_extension(extension: str) -> str:
        """
        Get expected MIME type for file extension

        Args:
            extension: File extension (with or without dot)

        Returns:
            MIME type string
        """
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.svg': 'image/svg+xml',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.zip': 'application/zip',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
        }

        ext = extension if extension.startswith('.') else f'.{extension}'
        return mime_types.get(ext.lower(), 'application/octet-stream')


class FileSystemMock:
    """Mock file system operations"""

    @staticmethod
    def mock_path_exists(exists=True):
        """
        Mock Path.exists()

        Args:
            exists: Whether path should exist
        """
        return patch('pathlib.Path.exists', return_value=exists)

    @staticmethod
    def mock_path_is_file(is_file=True):
        """
        Mock Path.is_file()

        Args:
            is_file: Whether path is a file
        """
        return patch('pathlib.Path.is_file', return_value=is_file)

    @staticmethod
    def mock_path_is_dir(is_dir=True):
        """
        Mock Path.is_dir()

        Args:
            is_dir: Whether path is a directory
        """
        return patch('pathlib.Path.is_dir', return_value=is_dir)

    @staticmethod
    def mock_path_mkdir():
        """Mock Path.mkdir()"""
        mock_mkdir = Mock()
        return patch('pathlib.Path.mkdir', mock_mkdir)

    @staticmethod
    def mock_path_unlink():
        """Mock Path.unlink() for file deletion"""
        mock_unlink = Mock()
        return patch('pathlib.Path.unlink', mock_unlink)

    @staticmethod
    def mock_shutil_rmtree():
        """Mock shutil.rmtree() for directory deletion"""
        mock_rmtree = Mock()
        return patch('shutil.rmtree', mock_rmtree)

    @staticmethod
    def mock_file_stat(size=1024):
        """
        Mock file stat for size checking

        Args:
            size: File size in bytes
        """
        mock_stat = Mock()
        mock_stat.st_size = size
        return patch('pathlib.Path.stat', return_value=mock_stat)

    @staticmethod
    def mock_glob(files=None):
        """
        Mock Path.glob() for pattern matching

        Args:
            files: List of file paths to return
        """
        if files is None:
            files = []

        from pathlib import Path
        path_objects = [Path(f) for f in files]

        return patch('pathlib.Path.glob', return_value=iter(path_objects))


class UploadFileMock:
    """Mock FastAPI UploadFile"""

    @staticmethod
    def create_mock_upload(filename='test.jpg', content=b'mock content', content_type='image/jpeg'):
        """
        Create mock UploadFile

        Args:
            filename: Filename
            content: File content as bytes
            content_type: MIME type

        Returns:
            Mock UploadFile object
        """
        from fastapi import UploadFile

        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.file = io.BytesIO(content)
        mock_file.file.seek(0)

        # Mock async read
        async def async_read():
            return content

        mock_file.read = async_read

        # Mock file size via tell()
        mock_file.file.tell = Mock(return_value=len(content))

        return mock_file

    @staticmethod
    def create_oversized_mock(filename='oversized.mp4', size=600*1024*1024):
        """
        Create mock for oversized file (doesn't create actual large file)

        Args:
            filename: Filename
            size: Size to report in bytes

        Returns:
            Mock UploadFile that reports large size
        """
        mock_file = UploadFileMock.create_mock_upload(
            filename=filename,
            content=b'MOCK_OVERSIZED_FILE',
            content_type='video/mp4'
        )

        # Override tell() to return oversized value
        mock_file.file.tell = Mock(return_value=size)

        return mock_file
