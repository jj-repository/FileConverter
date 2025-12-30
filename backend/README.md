# FileConverter Backend

[![Backend Tests](https://github.com/jj-repository/FileConverter/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/backend-tests.yml)
[![codecov](https://codecov.io/gh/jj-repository/FileConverter/branch/main/graph/badge.svg?flag=backend)](https://codecov.io/gh/jj-repository/FileConverter)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A modern, high-performance file conversion API built with FastAPI, supporting 10+ file types including images, videos, audio, documents, and more.

## 🚀 Features

- **Multi-Format Support**: Convert between 50+ file formats
- **Real-time Progress**: WebSocket-based conversion progress tracking
- **Smart Caching**: LRU cache with configurable expiration
- **Batch Processing**: Convert multiple files concurrently
- **Security First**: Input validation, rate limiting, path traversal prevention
- **Production Ready**: Comprehensive test coverage, error handling, and logging

## 📋 Supported Conversions

| Category | Formats |
|----------|---------|
| **Images** | JPG, PNG, WebP, GIF, BMP, TIFF, SVG, HEIC, ICO |
| **Videos** | MP4, WebM, AVI, MKV, MOV, FLV |
| **Audio** | MP3, WAV, OGG, FLAC, AAC, M4A |
| **Documents** | PDF, DOCX, HTML, Markdown, TXT |
| **Data** | JSON, CSV, XML, YAML |
| **Archives** | ZIP, TAR, TAR.GZ, TAR.BZ2 |
| **Spreadsheets** | XLSX, CSV, ODS |
| **Subtitles** | SRT, VTT, ASS, SUB |
| **eBooks** | EPUB, MOBI, PDF |
| **Fonts** | TTF, OTF, WOFF, WOFF2 |

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- System dependencies:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg pandoc libreoffice imagemagick ghostscript poppler-utils

  # macOS
  brew install ffmpeg pandoc libreoffice imagemagick ghostscript poppler
  ```

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jj-repository/FileConverter.git
   cd FileConverter/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create required directories**
   ```bash
   mkdir -p uploads temp cache
   ```

5. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Quick Example

```python
import requests

# Convert JPG to PNG
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/image/convert',
        files={'file': f},
        data={'output_format': 'png', 'quality': 95}
    )

result = response.json()
download_url = result['download_url']
```

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Security tests only
pytest -m security -v

# With coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Test Coverage

Current test coverage: **192 tests** across:
- **Unit Tests** (127 tests): Services, utilities, validation
- **Integration Tests** (65 tests): API endpoints, app lifecycle, caching

| Component | Tests | Coverage |
|-----------|-------|----------|
| Security-critical (validation, auth) | 47 | 95%+ |
| Core services (converters, cache) | 81 | 85%+ |
| Integration (routers, flows) | 65 | 80%+ |

### CI/CD

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests

The CI pipeline includes:
- ✅ Tests on Python 3.11, 3.12, 3.13
- ✅ Code quality checks (flake8, black, isort)
- ✅ Security scanning (bandit, safety)
- ✅ Coverage reporting to Codecov

## 🔒 Security Features

- **Input Validation**: File type, size, and extension validation
- **Path Traversal Prevention**: Secure filename handling
- **Rate Limiting**: WebSocket connection throttling (10/min per IP)
- **Session Management**: Temporary session IDs with 1-hour expiration
- **CORS Configuration**: Configurable allowed origins
- **Error Sanitization**: No sensitive data in error messages

## ⚙️ Configuration

Key environment variables (`.env`):

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# File handling
MAX_IMAGE_SIZE_MB=100
MAX_VIDEO_SIZE_MB=500
TEMP_FILE_LIFETIME=3600

# Caching
CACHE_ENABLED=true
CACHE_EXPIRATION_HOURS=1
CACHE_MAX_SIZE_MB=1000
```

## 📊 Performance

- **Cache Hit Rate**: Typical 60-80% for repeated conversions
- **Concurrent Requests**: Handles 100+ concurrent conversions
- **Cleanup**: Automatic cleanup of temp files every hour
- **Memory**: ~200-500MB for typical workload

## 🏗️ Architecture

```
backend/
├── app/
│   ├── routers/          # API endpoints (13 routers)
│   ├── services/         # Business logic (14 converters)
│   ├── utils/            # Utilities (validation, file handling)
│   ├── middleware/       # Error handling, logging
│   ├── models/           # Pydantic models
│   └── config.py         # Configuration
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── fixtures/         # Test data
│   └── mocks/            # Mock utilities
└── pytest.ini            # Test configuration
```

## 🔧 Development

### Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint
flake8 app/ tests/

# Type checking
mypy app/
```

### Adding a New Converter

1. Create service in `app/services/your_converter.py`
2. Inherit from `BaseConverter`
3. Implement `convert()` and `get_supported_formats()`
4. Create router in `app/routers/your_router.py`
5. Add tests in `tests/unit/test_services/test_your_converter.py`
6. Register router in `app/main.py`

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/jj-repository/FileConverter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jj-repository/FileConverter/discussions)

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [FFmpeg](https://ffmpeg.org/) - Video/audio processing
- [Pillow](https://python-pillow.org/) - Image processing
- [Pandoc](https://pandoc.org/) - Document conversion
- [LibreOffice](https://www.libreoffice.org/) - Office document conversion

---

**Made with ❤️ by the FileConverter team**
